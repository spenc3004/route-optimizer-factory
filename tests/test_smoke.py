"""Standalone smoke tests for the extracted optimizer.

Proves `cli.py` runs independently in this repo (no backend, no Streamlit) via
the same subprocess JSON contract the backend/worker use. Uses synthetic,
non-proprietary data so it can run in CI without client reports. Real output
parity against client baselines lives in `tests/parity/run_parity.py`.

Run:  .venv/bin/python -m pytest tests/test_smoke.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(REPO_ROOT, "optimizer", "cli.py")
SYNTHETIC = os.path.join(REPO_ROOT, "tests", "parity", "fixtures", "synthetic", "home_services.csv")
PYTHON = sys.executable

CATEGORY = "Home Services"
PRESET = "Home SRVCS Acquisition (No History)"
WEIGHTS = {
    "$ Income": 0.25,
    "$ Home Value": 0.15,
    "Owner Occupied": 0.30,
    "Median Year Structure Built": 0.05,
    "Distance": 0.25,
}


def run_cli(mode: str, args: dict, out_dir: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [PYTHON, CLI, "--mode", mode, "--out-dir", out_dir],
        input=json.dumps(args), capture_output=True, text=True,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload


def test_config_lists_categories(tmp_path):
    code, out = run_cli("config", {}, str(tmp_path))
    assert code == 0
    names = [c["name"] for c in out["categories"]]
    assert "Home Services" in names and "Automotive" in names


def test_validate_clean_file(tmp_path):
    code, out = run_cli("validate", {
        "category": CATEGORY, "preset": PRESET, "filePath": SYNTHETIC,
    }, str(tmp_path))
    assert code == 0
    assert out["ok"] is True
    assert out["missingColumns"] == []
    assert out["rowCount"] == 10


def test_validate_reports_missing_columns(tmp_path):
    code, out = run_cli("validate", {
        "category": CATEGORY,
        "preset": "Home SRVCS Acquisition (With History + Suppression)",
        "filePath": SYNTHETIC,
    }, str(tmp_path))
    assert code == 0
    # synthetic file lacks the history columns this preset requires
    assert out["ok"] is False
    assert "$ Total Spend" in out["missingColumns"]


def test_score_produces_ranked_output_and_xlsx(tmp_path):
    code, out = run_cli("score", {
        "category": CATEGORY, "preset": PRESET, "filePath": SYNTHETIC,
        "clientName": "Synthetic Smoke", "originalName": "home_services.csv",
        "weights": WEIGHTS,
        "failFilters": {"min_income": 40000, "max_distance": 50, "min_owner": 60},
        "profile": {"mode": None},
    }, str(tmp_path))
    assert code == 0, out
    assert len(out["rankedRows"]) == 10
    assert "Composite Score" in out["rankedColumns"]
    # ranked descending: every Composite Score <= the one above it
    scores = [r["Composite Score"] for r in out["rankedRows"]]
    assert scores == sorted(scores, reverse=True)
    assert out["dashboardModel"]  # non-empty dashboard model
    assert os.path.exists(tmp_path / "ranked.xlsx")
    assert os.path.exists(tmp_path / "ranked.pkl")  # ROI depends on this


def test_score_missing_required_columns_is_validation_error(tmp_path):
    code, out = run_cli("score", {
        "category": CATEGORY,
        "preset": "Home SRVCS Acquisition (With History + Suppression)",
        "filePath": SYNTHETIC, "weights": WEIGHTS,
    }, str(tmp_path))
    assert code == 2  # EXIT_VALIDATION
    assert out["error"]["code"] == "MISSING_COLUMNS"
