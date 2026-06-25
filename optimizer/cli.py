"""Headless entrypoint for the Mail Shark Route Optimizer.

Wraps the existing scoring/ROI pipeline (``utilities.*``) so the Team Dashboard
backend can run it without Streamlit. Reads a JSON job spec, prints a JSON result
to stdout, and writes any ``.xlsx`` workbook into the working directory.

The process is stateless: every input is supplied per invocation and all outputs
land in ``--out-dir``. Diagnostics go to stderr; stdout carries only the JSON
result. Exit codes: 0 success, 2 validation failure, 1 unexpected error.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd

from utilities.calculations import (
    calculate_cpms,
    calculate_cs,
    calculate_vds,
    calculate_wps,
)
from utilities.config import CATEGORY_CONFIG
from utilities.dashboard import build_dashboard_model
from utilities.helpers import (
    build_profiles_df,
    coerce_numeric_columns,
    coerce_year_built,
    create_summary,
    extract_driver_ideals,
    feature,
    flag_and_filter,
    get_default_weights,
    get_export_layout,
    normalize,
    normalize_weight_defaults,
    prepare_ranked_columns,
    required_columns_for,
    restrict_visible_sheets,
    sanitize_ideal_year,
    write_ranked_workbook,
)
from utilities.roi import ensure_numeric, roi_merge

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2

ONLY_FIXED_PRESETS = {
    "Home SRVCS Acquisition (No History)",
    "Auto Acquisition (No History)",
}
SCORING_SHEETS = ("Dashboard", "Ranked Geocodes")
ROI_SHEETS = ("Dashboard", "Ranked + ROI Summary", "ROI Summary by Campaign")


class CliError(Exception):
    def __init__(self, exit_code, code, message, details=None):
        super().__init__(message)
        self.exit_code = exit_code
        self.code = code
        self.message = message
        self.details = details


def _scalar(value):
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    return value


def _records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    return [{key: _scalar(val) for key, val in row.items()}
            for row in df.to_dict(orient="records")]


def _load_table(path: str) -> pd.DataFrame:
    if not path or not os.path.exists(path):
        raise CliError(EXIT_VALIDATION, "FILE_NOT_FOUND", "Input file was not found.")
    lower = path.lower()
    if lower.endswith(".csv"):
        return pd.read_csv(path)
    if lower.endswith(".xlsx"):
        return pd.read_excel(path)
    raise CliError(EXIT_VALIDATION, "UNSUPPORTED_FILE",
                   "Upload must be a .csv or .xlsx file.")


def _require_category(category: str) -> dict:
    config = CATEGORY_CONFIG.get(category)
    if config is None:
        raise CliError(EXIT_VALIDATION, "UNKNOWN_CATEGORY",
                       f"Unknown category: {category}")
    return config


def _preprocess(df: pd.DataFrame, category: str, config: dict, required: list[str]) -> None:
    numeric_candidates = set(required)
    numeric_candidates.update(config["currency_columns"])
    numeric_candidates.update(config["percentage_columns"])
    numeric_candidates.update(config["numeric_columns"])

    if "Median Year Structure Built" in df.columns:
        df["Median Year Structure Built"] = (
            coerce_year_built(df["Median Year Structure Built"]).astype("float64"))

    coerce_numeric_columns(df, numeric_candidates)

    for col in config["percentage_columns"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0


def _active_weight_keys(category: str, config: dict, default_weights: dict) -> dict:
    valid = dict(default_weights)
    if not feature(category, "use_wps", CATEGORY_CONFIG):
        valid.pop("Weighted Penetration Score", None)
    if not feature(category, "use_cpms", CATEGORY_CONFIG):
        valid.pop("Customer Profile Match Score", None)
    if not feature(category, "use_vds", CATEGORY_CONFIG):
        valid.pop("Vehicle Density Score", None)
    return valid


def _effective_weights(weights: dict, df: pd.DataFrame, category: str, warnings: list) -> dict:
    active, dropped = {}, {}
    for key, weight in weights.items():
        is_enabled_derived = (
            (key == "Weighted Penetration Score" and feature(category, "use_wps", CATEGORY_CONFIG))
            or (key == "Customer Profile Match Score" and feature(category, "use_cpms", CATEGORY_CONFIG))
            or (key == "Vehicle Density Score" and feature(category, "use_vds", CATEGORY_CONFIG))
        )
        if key in df.columns or is_enabled_derived:
            active[key] = weight
        else:
            dropped[key] = weight

    if dropped:
        detail = ", ".join(f"{key} ({weight:.2f})" for key, weight in dropped.items())
        warnings.append(
            "These weighted columns are not in the uploaded file; their weight "
            f"was redistributed across the scored components: {detail}."
        )

    if not active:
        raise CliError(EXIT_VALIDATION, "NO_SCORABLE_WEIGHTS",
                       "None of the weighted components are available for this file.")

    active = normalize_weight_defaults(active, target=1.0)

    applied = sum(active.values())
    if abs(applied - 1.0) > 1e-6:
        raise CliError(EXIT_ERROR, "WEIGHTS_RENORMALIZE_FAILED",
                       f"Applied weights sum to {round(applied, 4)}, expected 1.0.")
    return active


def _resolve_ideals(df, category, config, preset, profile):
    ideal_map = config.get("ideals_columns", {})
    ideal_values = {col: None for col in ideal_map}
    profile = profile or {}
    mode = profile.get("mode")
    driver = profile.get("driver")

    if not (feature(category, "use_cpms", CATEGORY_CONFIG)
            and config["features"].get("profile_modes")):
        return ideal_values, None, None, pd.DataFrame()

    if preset in ONLY_FIXED_PRESETS:
        mode = "Fixed Standard"

    profiles_df = pd.DataFrame()
    if mode == "Fixed Standard":
        for col, value in (profile.get("idealValues") or {}).items():
            if col not in ideal_map:
                continue
            ideal_values[col] = (sanitize_ideal_year(value)
                                 if col == "Median Year Structure Built" else value)
    elif mode == "Dynamic (from file)":
        drivers = [c for c in config.get("drivers", []) if c in df.columns]
        if driver in drivers:
            source = df.copy()
            source, _ = calculate_vds(
                source, None, feature(category, "use_vds", CATEGORY_CONFIG), [])
            profiles_df = build_profiles_df(source, drivers, ideal_map)
            driver_ideals = extract_driver_ideals(profiles_df, driver, ideal_map)
            for col in ideal_map:
                raw = driver_ideals.get(col)
                ideal_values[col] = (sanitize_ideal_year(raw)
                                     if col == "Median Year Structure Built" else raw)

    return ideal_values, mode, driver, profiles_df


def _score_frame(df, category, valid_weight_keys, weights, ideal_map, ideal_values, warnings):
    working = df.copy()
    audits = []
    id_series = working["Geocode"] if "Geocode" in working.columns else None

    try:
        working, audits = normalize(
            working, valid_weight_keys.keys(), working.columns, audits, id_series)
    except Exception as error:
        warnings.append(f"Normalization failed for some columns: {error}")

    try:
        result = calculate_wps(
            working, id_series, feature(category, "use_wps", CATEGORY_CONFIG), audits)
        if len(result) == 3:
            working, audits, wps_warning = result
            if wps_warning:
                warnings.append(wps_warning)
        else:
            working, audits = result
    except Exception as error:
        warnings.append(f"Weighted Penetration Score calculation failed: {error}")

    try:
        working, audits = calculate_vds(
            working, id_series, feature(category, "use_vds", CATEGORY_CONFIG), audits)
    except Exception as error:
        warnings.append(f"Vehicle Density Score calculation failed: {error}")

    try:
        working = calculate_cpms(
            working, ideal_map, ideal_values, feature(category, "use_cpms", CATEGORY_CONFIG))
    except Exception as error:
        warnings.append(f"Customer Profile Match Score calculation failed: {error}")

    try:
        working = calculate_cs(working, weights)
    except Exception as error:
        warnings.append(f"Composite Score calculation failed: {error}")

    return working, audits


def run_config(_args, _out_dir) -> dict:
    categories = []
    for name, config in CATEGORY_CONFIG.items():
        presets = list(config["presets"].keys())
        categories.append({
            "name": name,
            "presets": presets,
            "features": config["features"],
            "failFilters": config.get("fail_filters", []),
            "ideals": config.get("ideals_columns", {}),
            "drivers": config.get("drivers", []),
            "profileDefaults": config.get("profile_defaults", {}),
            "requiredColumnsBase": config.get("required_columns_base", []),
            "defaultWeightsByPreset": {
                preset: get_default_weights(name, preset, CATEGORY_CONFIG)
                for preset in presets
            },
            "fixedStandardOnlyPresets": [p for p in presets if p in ONLY_FIXED_PRESETS],
        })
    return {"categories": categories}


def run_validate(args, _out_dir) -> dict:
    category = args["category"]
    preset = args["preset"]
    config = _require_category(category)
    df = _load_table(args["filePath"])

    required = required_columns_for(category, preset, CATEGORY_CONFIG)
    missing = [col for col in required if col not in df.columns]
    disabled_filters = [
        f["key"] for f in config.get("fail_filters", [])
        if f.get("required_column") and f["required_column"] not in df.columns
    ]
    available_drivers = [d for d in config.get("drivers", []) if d in df.columns]

    return {
        "ok": not missing,
        "missingColumns": missing,
        "disabledFilters": disabled_filters,
        "availableDrivers": available_drivers,
        "rowCount": int(len(df)),
        "warnings": [],
    }


def run_score(args, out_dir) -> dict:
    category = args["category"]
    preset = args["preset"]
    config = _require_category(category)
    df = _load_table(args["filePath"])
    warnings = []

    required = required_columns_for(category, preset, CATEGORY_CONFIG)
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise CliError(EXIT_VALIDATION, "MISSING_COLUMNS",
                       "Missing required columns for the selected mode.",
                       {"missingColumns": missing})

    _preprocess(df, category, config, required)

    default_weights = get_default_weights(category, preset, CATEGORY_CONFIG)
    valid_weight_keys = _active_weight_keys(category, config, default_weights)
    weights = {key: float(value) for key, value in (args.get("weights") or {}).items()}
    if not weights:
        raise CliError(EXIT_VALIDATION, "WEIGHTS_REQUIRED", "No weights were provided.")
    if abs(sum(weights.values()) - 1.0) > 1e-2:
        raise CliError(EXIT_VALIDATION, "WEIGHTS_SUM",
                       "Weights must sum to 1.00.",
                       {"sum": round(sum(weights.values()), 4)})
    weights = _effective_weights(weights, df, category, warnings)

    ideal_map = config.get("ideals_columns", {})
    ideal_values, profile_mode, profile_driver, profiles_df = _resolve_ideals(
        df, category, config, preset, args.get("profile"))

    working, audits = _score_frame(
        df, category, valid_weight_keys, weights, ideal_map, ideal_values, warnings)

    fail_filters = args.get("failFilters") or {}
    try:
        working = flag_and_filter(
            working,
            fail_filters.get("max_penetration"),
            fail_filters.get("max_income"),
            fail_filters.get("min_income"),
            fail_filters.get("max_distance"),
            fail_filters.get("min_owner"),
        )
    except Exception as error:
        warnings.append(f"Fail filter flagging failed: {error}")

    sort_cols = [c for c in ("Status", "Composite Score") if c in working.columns]
    if sort_cols:
        working = working.sort_values(by=sort_cols, ascending=[False] * len(sort_cols))

    try:
        audit_summary_df, winsor_details_df, base_summary = create_summary(
            audits, profile_mode, ideal_values, ideal_map)
    except Exception as error:
        warnings.append(f"Summary creation failed: {error}")
        audit_summary_df = pd.DataFrame()
        winsor_details_df = pd.DataFrame()
        base_summary = {"Note": [], "Value": []}

    report_label = (args.get("clientName") or "").strip() or _default_label(
        args.get("originalName") or args["filePath"])
    export_layout = get_export_layout(category, CATEGORY_CONFIG)

    xlsx_path = os.path.join(out_dir, "ranked.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        write_ranked_workbook(
            writer=writer,
            working_df=working,
            base_summary_dict=base_summary,
            audit_summary_df=audit_summary_df,
            profiles_df=profiles_df,
            winsor_details_df=winsor_details_df,
            profile_mode=profile_mode,
            ranked_columns_order=export_layout.get("ranked_columns_order"),
            ranked_columns_drop=export_layout.get("ranked_columns_drop"),
            ranked_header_colors=export_layout.get("ranked_header_colors"),
            include_winsor_sheet=export_layout.get("include_winsor_sheet"),
            ranked_sheet_name="Ranked Geocodes",
            report_label=report_label,
            profile_driver=profile_driver,
        )
        restrict_visible_sheets(writer.book, SCORING_SHEETS)

    _persist_run_parts(out_dir, working, audit_summary_df, profiles_df,
                       winsor_details_df, base_summary, profile_mode,
                       profile_driver, category, report_label)

    ranked_view = prepare_ranked_columns(
        working,
        export_layout.get("ranked_columns_drop"),
        export_layout.get("ranked_columns_order"),
        False,
    )
    dashboard_model = build_dashboard_model(
        working, base_summary, profile_mode, profile_driver)

    return {
        "dashboardModel": dashboard_model,
        "rankedRows": _records(ranked_view),
        "rankedColumns": list(ranked_view.columns),
        "artifacts": {"xlsx": "ranked.xlsx"},
        "exportSheets": list(SCORING_SHEETS),
        "meta": {
            "category": category,
            "preset": preset,
            "profileMode": profile_mode,
            "profileDriver": profile_driver,
            "reportLabel": report_label,
        },
        "warnings": warnings,
    }


def run_roi(args, out_dir) -> dict:
    ranked_path = args.get("rankedPath") or os.path.join(out_dir, "ranked.pkl")
    if not os.path.exists(ranked_path):
        raise CliError(EXIT_VALIDATION, "RANKED_NOT_FOUND",
                       "Ranked data for this run was not found.")
    ranked_df = pd.read_pickle(ranked_path)
    roi_df = ensure_numeric(_load_table(args["roiFilePath"]))

    merged, roi_summary, merge_error = roi_merge(roi_df, ranked_df)
    if merge_error:
        raise CliError(EXIT_VALIDATION, "ROI_MERGE_FAILED", merge_error)

    parts = _load_run_parts(out_dir)
    export_layout = get_export_layout(parts["category"], CATEGORY_CONFIG)

    xlsx_path = os.path.join(out_dir, "roi.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        write_ranked_workbook(
            writer=writer,
            working_df=ranked_df,
            base_summary_dict=parts["base_summary"],
            audit_summary_df=parts["audit_summary_df"],
            profiles_df=parts["profiles_df"],
            winsor_details_df=parts["winsor_details_df"],
            profile_mode=parts["profile_mode"],
            ranked_columns_order=export_layout.get("roi_columns_order"),
            ranked_columns_drop=export_layout.get("roi_columns_drop"),
            ranked_header_colors=export_layout.get("roi_header_colors"),
            include_winsor_sheet=export_layout.get("include_winsor_sheet"),
            ranked_sheet_name="Ranked + ROI Summary",
            ranked_df_override=merged,
            report_label=parts["report_label"],
            profile_driver=parts["profile_driver"],
        )
        roi_summary.to_excel(writer, index=False, sheet_name="ROI Summary by Campaign")
        restrict_visible_sheets(writer.book, ROI_SHEETS)

    return {
        "mergedRows": _records(merged),
        "mergedColumns": list(merged.columns),
        "roiSummary": _records(roi_summary),
        "artifacts": {"xlsx": "roi.xlsx"},
        "exportSheets": list(ROI_SHEETS),
        "warnings": [],
    }


def _default_label(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]


def _persist_run_parts(out_dir, working, audit_summary_df, profiles_df,
                       winsor_details_df, base_summary, profile_mode,
                       profile_driver, category, report_label) -> None:
    working.to_pickle(os.path.join(out_dir, "ranked.pkl"))
    audit_summary_df.to_pickle(os.path.join(out_dir, "audit_summary.pkl"))
    profiles_df.to_pickle(os.path.join(out_dir, "profiles.pkl"))
    winsor_details_df.to_pickle(os.path.join(out_dir, "winsor_details.pkl"))
    with open(os.path.join(out_dir, "parts.json"), "w", encoding="utf-8") as handle:
        json.dump({
            "base_summary": base_summary,
            "profile_mode": profile_mode,
            "profile_driver": profile_driver,
            "category": category,
            "report_label": report_label,
        }, handle)


def _load_run_parts(out_dir) -> dict:
    parts_path = os.path.join(out_dir, "parts.json")
    if not os.path.exists(parts_path):
        raise CliError(EXIT_VALIDATION, "RUN_PARTS_NOT_FOUND",
                       "Stored run data for this run was not found.")
    with open(parts_path, "r", encoding="utf-8") as handle:
        parts = json.load(handle)
    parts["audit_summary_df"] = pd.read_pickle(os.path.join(out_dir, "audit_summary.pkl"))
    parts["profiles_df"] = pd.read_pickle(os.path.join(out_dir, "profiles.pkl"))
    parts["winsor_details_df"] = pd.read_pickle(os.path.join(out_dir, "winsor_details.pkl"))
    return parts


HANDLERS = {
    "config": run_config,
    "validate": run_validate,
    "score": run_score,
    "roi": run_roi,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mail Shark Route Optimizer CLI")
    parser.add_argument("--mode", required=True, choices=sorted(HANDLERS.keys()))
    parser.add_argument("--args-file")
    parser.add_argument("--out-dir", default=".")
    parsed = parser.parse_args(argv)

    try:
        if parsed.args_file:
            with open(parsed.args_file, "r", encoding="utf-8") as handle:
                args = json.load(handle)
        else:
            raw = sys.stdin.read()
            args = json.loads(raw) if raw.strip() else {}

        os.makedirs(parsed.out_dir, exist_ok=True)
        result = HANDLERS[parsed.mode](args, parsed.out_dir)
        json.dump(result, sys.stdout, allow_nan=False)
        sys.stdout.flush()
        return EXIT_OK
    except CliError as error:
        json.dump({"error": {"code": error.code, "message": error.message,
                             "details": error.details}}, sys.stdout, allow_nan=False)
        sys.stdout.flush()
        return error.exit_code
    except Exception as error:  # noqa: BLE001 - top-level guard maps to exit code 1
        print(f"route-optimizer cli failed: {error}", file=sys.stderr)
        json.dump({"error": {"code": "PY_FAILED", "message": str(error)}},
                  sys.stdout, allow_nan=False)
        sys.stdout.flush()
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
