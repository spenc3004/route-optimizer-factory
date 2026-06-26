"""Environment loading for the route-optimizer-factory worker."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv optional at runtime
    def load_dotenv():
        return False

# Fixed structural subdir under the shared EFS root (EFS_PATH). Hardcoded (not env)
# so the worker and backend can never drift to different folders; only EFS_PATH is
# configurable. Must match the backend's storageSubdir.
STORAGE_SUBDIR = "route_optimizer"


@dataclass(frozen=True)
class Settings:
    backend_url: str            # team-dashboard-backend base, e.g. http://127.0.0.1:8091
    worker_secret: str          # shared secret -> Authorization: Bearer <secret>
    db_server: str
    db_database: str
    db_user: str
    db_password: str
    efs_path: str
    storage_subdir: str
    worker_id: str
    poll_interval_seconds: int
    lease_seconds: int
    python_bin: str
    cli_path: str


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    load_dotenv()
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return Settings(
        backend_url=os.getenv("RO_BACKEND_URL", "http://127.0.0.1:8091").strip().rstrip("/"),
        worker_secret=_require("RO_WORKER_SECRET"),
        db_server=_require("RO_SQL_SERVER"),
        db_database=_require("RO_SQL_DATABASE"),
        db_user=_require("RO_SQL_USER"),
        db_password=_require("RO_SQL_PASSWORD"),
        efs_path=_require("EFS_PATH"),
        storage_subdir=STORAGE_SUBDIR,
        worker_id=os.getenv("RO_WORKER_ID", "ro-factory-local").strip(),
        poll_interval_seconds=int(os.getenv("RO_POLL_INTERVAL_SECONDS", "5")),
        lease_seconds=int(os.getenv("RO_LEASE_SECONDS", "300")),
        python_bin=os.getenv("ROUTE_OPTIMIZER_PYTHON", sys.executable).strip(),
        cli_path=os.getenv("ROUTE_OPTIMIZER_CLI", os.path.join(repo_root, "optimizer", "cli.py")).strip(),
    )
