"""Worker -> backend status callback (POST /ro/progress).

Mounted outside /api/v3 on the backend; authenticated with the shared secret as
a bearer token (see route-optimizer-decoupling-plan.md §7a). Best-effort with a
few retries for terminal states so a transient blip doesn't strand a job.
"""
from __future__ import annotations

import time

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}


def build_payload(job_id, status, *, progress=0, total=0, eta=None, message=None,
                  error_code=None, error_message=None, error_details=None) -> dict:
    return {
        "jobId": job_id,
        "status": status,
        "progress": progress,
        "total": total,
        "eta": eta,
        "message": message,
        "errorCode": error_code,
        "errorMessage": error_message,
        "errorDetails": error_details,
    }


def post_progress(settings, payload: dict) -> bool:
    if requests is None:
        print("[callback] requests not installed; skipping progress post")
        return False
    url = f"{settings.backend_url}/ro/progress"
    headers = {"Authorization": f"Bearer {settings.worker_secret}"}
    attempts = 3 if payload.get("status") in TERMINAL else 1
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 202:
                return True
            print(f"[callback] {payload.get('status')} -> HTTP {resp.status_code}: {resp.text[:300]}")
        except Exception as error:  # noqa: BLE001 - best-effort callback
            print(f"[callback] post failed (attempt {attempt}/{attempts}): {error}")
        if attempt < attempts:
            time.sleep(2 * attempt)
    return False
