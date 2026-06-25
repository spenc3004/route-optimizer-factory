"""Generate the published, versioned Route Optimizer config contract.

This is the read-only artifact the Team Dashboard backend caches so it can serve
`GET /config` and validate uploaded columns for `POST /jobs` WITHOUT running
Python. It is the source of truth for categories, presets, features, fail
filters, ideals, drivers, default weights, and — critically — the required
columns *per preset* so Node can replicate `required_columns_for`.

Shape mirrors `cli.py:run_config` (kept byte-identical) PLUS one addition:
`requiredColumnsByPreset`. `cli.py` is NOT modified; this generator reads the
same embedded `CATEGORY_CONFIG` so the published artifact can never silently
drift from the engine.

Usage:
    python contract/generate_config.py            # writes contract/config.json
    python contract/generate_config.py --check     # verify config.json is up to date (CI)

The optimizer package must be importable (run from the repo root with the
optimizer venv, or `PYTHONPATH=optimizer`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

# Make the vendored optimizer importable when run from the repo root.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "optimizer"))

from utilities.config import CATEGORY_CONFIG  # noqa: E402
from utilities.helpers import get_default_weights  # noqa: E402

# Human-facing contract version. Bump on any intentional change to the config
# values OR the cli.py JSON I/O shape. Jobs pin this into ro_jobs.ConfigVersion
# / ContractVersion so past runs stay reproducible.
CONTRACT_VERSION = "ro-config-2026-06-25"

# Presets that the engine forces to "Fixed Standard" profile mode
# (mirrors cli.py:ONLY_FIXED_PRESETS — kept in sync deliberately).
ONLY_FIXED_PRESETS = {
    "Home SRVCS Acquisition (No History)",
    "Auto Acquisition (No History)",
}

OUTPUT_PATH = os.path.join(REPO_ROOT, "contract", "config.json")


def build_contract() -> dict:
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
            # ADDITION over run_config: lets the backend validate in Node via
            # required = dedupe(requiredColumnsBase + requiredColumnsByPreset[preset]).
            "requiredColumnsByPreset": config.get("required_columns_by_preset", {}),
            "defaultWeightsByPreset": {
                preset: get_default_weights(name, preset, CATEGORY_CONFIG)
                for preset in presets
            },
            "fixedStandardOnlyPresets": [p for p in presets if p in ONLY_FIXED_PRESETS],
        })

    payload = {
        "contractVersion": CONTRACT_VERSION,
        "categories": categories,
    }
    # Content hash over the categories (not the version label) so drift is
    # detectable even if someone forgets to bump CONTRACT_VERSION.
    canonical = json.dumps(categories, sort_keys=True, ensure_ascii=False)
    payload["sourceHash"] = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return payload


def render(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Route Optimizer config contract")
    parser.add_argument("--check", action="store_true",
                        help="Fail if contract/config.json is stale (for CI).")
    parser.add_argument("--out", default=OUTPUT_PATH)
    args = parser.parse_args(argv)

    rendered = render(build_contract())

    if args.check:
        if not os.path.exists(args.out):
            print(f"MISSING: {args.out} does not exist; run generate_config.py", file=sys.stderr)
            return 1
        with open(args.out, "r", encoding="utf-8") as handle:
            current = handle.read()
        if current != rendered:
            print("STALE: contract/config.json is out of date with CATEGORY_CONFIG; "
                  "run `python contract/generate_config.py`", file=sys.stderr)
            return 1
        print("OK: contract/config.json is up to date.")
        return 0

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
