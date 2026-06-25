"""route-optimizer-factory worker loop.

Poll dbo.ro_jobs -> claim -> run optimizer/cli.py -> write result.json + .xlsx to
shared storage -> POST status to the backend. cli.py runs as a subprocess per job
for parity + process isolation (a pandas blowup dies in the child, not the loop).
"""
from __future__ import annotations

import json
import time

from callback import build_payload, post_progress
from db import Db
from runner import WorkerCliError, build_cli_args, run_cli
from settings import load_settings
from storage import Storage


def process_job(settings, storage: Storage, job: dict) -> None:
    job_id = str(job["JobId"])
    kind = (job.get("Kind") or "score").lower()
    print(f"[worker] claimed {job_id} ({kind})")

    post_progress(settings, build_payload(job_id, "RUNNING", message="Processing"))

    out_dir = storage.ensure_job_dir(job_id)
    input_path = storage.resolve(job["InputRef"])

    if kind == "roi":
        parent = job.get("ParentJobId")
        if not parent:
            raise WorkerCliError("RO_ROI_NO_PARENT", "ROI job has no parent job.")
        storage.stage_roi_parent_parts(str(parent), job_id)

    mode, args = build_cli_args(job, input_path)
    result = run_cli(settings.python_bin, settings.cli_path, mode, args, out_dir)
    storage.write_result(job_id, result)

    total = len(result.get("rankedRows") or result.get("mergedRows") or [])
    post_progress(settings, build_payload(
        job_id, "COMPLETED", progress=total, total=total, message="Complete"))
    print(f"[worker] completed {job_id} ({total} rows)")


def handle_failure(settings, job_id: str, error: Exception) -> None:
    if isinstance(error, WorkerCliError):
        code, message, details = error.code, error.message, error.details
    else:
        code, message, details = "WORKER_ERROR", str(error), None
    print(f"[worker] FAILED {job_id}: {code} {message}")
    post_progress(settings, build_payload(
        job_id, "FAILED", message=message, error_code=code, error_message=message,
        error_details=json.dumps(details) if details is not None else None))


def main() -> int:
    settings = load_settings()
    storage = Storage(settings.efs_path, settings.storage_subdir)
    db = Db(settings)
    print(f"[worker] {settings.worker_id} polling ro_jobs every {settings.poll_interval_seconds}s")

    while True:
        try:
            job = db.claim_next_job()
        except Exception as error:  # noqa: BLE001 - keep the loop alive on DB blips
            print(f"[worker] claim error: {error}")
            time.sleep(settings.poll_interval_seconds)
            continue

        if job is None:
            time.sleep(settings.poll_interval_seconds)
            continue

        job_id = str(job["JobId"])
        try:
            process_job(settings, storage, job)
        except Exception as error:  # noqa: BLE001 - one job's failure must not kill the worker
            handle_failure(settings, job_id, error)


if __name__ == "__main__":
    raise SystemExit(main())
