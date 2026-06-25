"""Shared-storage (EFS) access for the worker, keyed by jobId.

Mirrors the backend's roStorage.js layout: <EFS_PATH>/<subdir>/<jobId>/. The
backend writes input.* + jobSpec.json; the worker writes result.json + the .xlsx
(cli.py writes the workbook directly into the job dir via --out-dir).
"""
from __future__ import annotations

import json
import os
import shutil

# Run-parts cli.py writes for a score job; an ROI job needs them staged in its
# own dir because cli.py --mode roi reads ranked.pkl + parts from --out-dir.
ROI_PARENT_PARTS = ("ranked.pkl", "audit_summary.pkl", "profiles.pkl", "winsor_details.pkl", "parts.json")


class Storage:
    def __init__(self, efs_path: str, subdir: str):
        self.efs_path = efs_path
        self.subdir = subdir

    def job_dir(self, job_id: str) -> str:
        return os.path.join(self.efs_path, self.subdir, job_id)

    def resolve(self, ref: str) -> str:
        """Resolve a logical ref (e.g. route_optimizer/<jobId>/input.xlsx) to an absolute path."""
        return os.path.join(self.efs_path, ref)

    def ensure_job_dir(self, job_id: str) -> str:
        path = self.job_dir(job_id)
        os.makedirs(path, exist_ok=True)
        return path

    def write_result(self, job_id: str, result: dict, name: str = "result.json") -> None:
        with open(os.path.join(self.job_dir(job_id), name), "w", encoding="utf-8") as handle:
            json.dump(result, handle)

    def stage_roi_parent_parts(self, parent_job_id: str, job_id: str) -> None:
        parent = self.job_dir(parent_job_id)
        dest = self.ensure_job_dir(job_id)
        for name in ROI_PARENT_PARTS:
            src = os.path.join(parent, name)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(dest, name))
