"""Unit tests for the worker's pure helpers (no DB / HTTP / subprocess)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "worker"))

from runner import WorkerCliError, build_cli_args, parse_cli_result  # noqa: E402
from callback import build_payload  # noqa: E402
from storage import Storage  # noqa: E402


def test_build_cli_args_score():
    job = {
        "Kind": "score", "Category": "Home Services", "Preset": "Manual",
        "JobSpec": json.dumps({"weights": {"$ Income": 1}, "profile": {"mode": None}, "originalName": "x.xlsx"}),
    }
    mode, args = build_cli_args(job, "/efs/route_optimizer/abc/input.xlsx")
    assert mode == "score"
    assert args["category"] == "Home Services"
    assert args["preset"] == "Manual"
    assert args["filePath"] == "/efs/route_optimizer/abc/input.xlsx"
    assert args["weights"] == {"$ Income": 1}


def test_build_cli_args_roi():
    job = {"Kind": "roi", "Category": "Home Services", "Preset": "Manual", "JobSpec": "{}"}
    mode, args = build_cli_args(job, "/efs/route_optimizer/def/input.csv")
    assert mode == "roi"
    assert args == {"roiFilePath": "/efs/route_optimizer/def/input.csv"}


def test_parse_cli_result_success():
    out = parse_cli_result('{"rankedRows": [1, 2], "warnings": []}', 0)
    assert out["rankedRows"] == [1, 2]


def test_parse_cli_result_error_envelope():
    with pytest.raises(WorkerCliError) as exc:
        parse_cli_result('{"error": {"code": "MISSING_COLUMNS", "message": "m", "details": {"missingColumns": ["x"]}}}', 2)
    assert exc.value.code == "MISSING_COLUMNS"
    assert exc.value.details == {"missingColumns": ["x"]}


def test_parse_cli_result_empty_and_bad():
    with pytest.raises(WorkerCliError) as e1:
        parse_cli_result("   ", 1)
    assert e1.value.code == "WORKER_NO_OUTPUT"
    with pytest.raises(WorkerCliError) as e2:
        parse_cli_result("not json", 0)
    assert e2.value.code == "WORKER_BAD_OUTPUT"


def test_build_payload_shape():
    p = build_payload("jid", "RUNNING", progress=5, total=10, message="go")
    assert p == {
        "jobId": "jid", "status": "RUNNING", "progress": 5, "total": 10, "eta": None,
        "message": "go", "errorCode": None, "errorMessage": None, "errorDetails": None,
    }


def test_storage_paths(tmp_path):
    s = Storage(str(tmp_path), "route_optimizer")
    assert s.job_dir("abc") == os.path.join(str(tmp_path), "route_optimizer", "abc")
    assert s.resolve("route_optimizer/abc/input.xlsx") == os.path.join(str(tmp_path), "route_optimizer/abc/input.xlsx")


def test_storage_write_result_and_stage_parts(tmp_path):
    s = Storage(str(tmp_path), "route_optimizer")
    # parent has a ranked.pkl + parts.json; ROI staging copies them into the child dir
    parent = s.ensure_job_dir("parent")
    with open(os.path.join(parent, "ranked.pkl"), "wb") as h:
        h.write(b"PKL")
    with open(os.path.join(parent, "parts.json"), "w") as h:
        h.write("{}")
    s.ensure_job_dir("child")
    s.stage_roi_parent_parts("parent", "child")
    assert os.path.exists(os.path.join(s.job_dir("child"), "ranked.pkl"))
    assert os.path.exists(os.path.join(s.job_dir("child"), "parts.json"))

    s.write_result("child", {"ok": 1})
    with open(os.path.join(s.job_dir("child"), "result.json")) as h:
        assert json.load(h) == {"ok": 1}
