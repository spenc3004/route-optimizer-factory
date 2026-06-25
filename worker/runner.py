"""Run optimizer/cli.py for a claimed job. Pure helpers (arg building + output
parsing) are separated from the subprocess call so they can be unit-tested."""
from __future__ import annotations

import json
import subprocess


class WorkerCliError(Exception):
    """cli.py returned a structured error (exit 1/2) or unusable output."""

    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def build_cli_args(job: dict, input_path: str) -> tuple[str, dict]:
    """Return (mode, args) for cli.py from a claimed ro_jobs row + resolved input path.

    The jobSpec (weights, failFilters, profile, originalName) is stored inline;
    category/preset are also columns. For ROI, cli reads ranked.pkl + run-parts
    from --out-dir (the worker stages them there), so only roiFilePath is passed.
    """
    spec = json.loads(job.get("JobSpec") or "{}")
    kind = (job.get("Kind") or "score").lower()
    if kind == "roi":
        return "roi", {"roiFilePath": input_path}
    args = {
        **spec,
        "category": job["Category"],
        "preset": job["Preset"],
        "filePath": input_path,
    }
    return "score", args


def parse_cli_result(stdout: str, returncode: int) -> dict:
    """Parse cli.py stdout. Raises WorkerCliError on error envelopes / bad output."""
    if not (stdout or "").strip():
        raise WorkerCliError("WORKER_NO_OUTPUT", f"cli.py produced no output (exit {returncode}).")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        raise WorkerCliError("WORKER_BAD_OUTPUT", "cli.py output was not valid JSON.")
    if isinstance(payload, dict) and "error" in payload:
        err = payload["error"] or {}
        raise WorkerCliError(err.get("code", "PY_FAILED"), err.get("message", "cli.py failed."), err.get("details"))
    return payload


def run_cli(python_bin: str, cli_path: str, mode: str, args: dict, out_dir: str) -> dict:
    proc = subprocess.run(
        [python_bin, cli_path, "--mode", mode, "--out-dir", out_dir],
        input=json.dumps(args), capture_output=True, text=True,
    )
    if proc.stderr:
        # cli diagnostics go to stderr; surface them in the worker log.
        print(f"[cli stderr] {proc.stderr.strip()[:1000]}")
    return parse_cli_result(proc.stdout, proc.returncode)
