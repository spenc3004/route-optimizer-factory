"""SQL Server adapter for the worker: claim the next ro_jobs row.

Only the claim touches SQL here. Status transitions (RUNNING progress, COMPLETED,
FAILED) flow through the backend's POST /ro/progress webhook, which owns the
ro_jobs status update + realtime emission. This keeps a single writer for status
while the worker owns claiming (SQL-as-queue, mirroring nm-factory-new).
"""
from __future__ import annotations

try:
    import mssql_python
except ImportError:  # pragma: no cover - resolved at runtime
    mssql_python = None

# Atomic claim: take the oldest QUEUED job, or reclaim a RUNNING job whose lease
# expired (dead worker) while attempts remain. READPAST skips rows another worker
# holds; UPDLOCK/ROWLOCK claim this one. (See plan §15.)
CLAIM_SQL = """
WITH next AS (
    SELECT TOP (1) *
    FROM dbo.ro_jobs WITH (READPAST, UPDLOCK, ROWLOCK)
    WHERE Status = 'QUEUED'
       OR (Status = 'RUNNING' AND LockedUntil < SYSUTCDATETIME() AND Attempts < MaxAttempts)
    ORDER BY CreatedAt
)
UPDATE next
SET Status      = 'RUNNING',
    ClaimedBy   = ?,
    StartedAt   = COALESCE(StartedAt, SYSUTCDATETIME()),
    LockedUntil = DATEADD(SECOND, ?, SYSUTCDATETIME()),
    Attempts    = Attempts + 1,
    UpdatedAt   = SYSUTCDATETIME()
OUTPUT inserted.JobId, inserted.Kind, inserted.ParentJobId, inserted.InputRef,
       inserted.StoragePrefix, inserted.JobSpec, inserted.Category, inserted.Preset,
       inserted.ConfigVersion;
"""

CLAIM_COLUMNS = ["JobId", "Kind", "ParentJobId", "InputRef", "StoragePrefix",
                 "JobSpec", "Category", "Preset", "ConfigVersion"]


class Db:
    def __init__(self, settings):
        self.settings = settings

    def _connection_string(self) -> str:
        s = self.settings
        return (
            f"SERVER={s.db_server};"
            f"DATABASE={s.db_database};"
            f"UID={s.db_user};"
            f"PWD={s.db_password};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )

    def _connect(self):
        if mssql_python is None:
            raise RuntimeError("mssql-python is not installed")
        connection = mssql_python.connect(self._connection_string())
        connection.autocommit = False
        return connection

    def claim_next_job(self) -> dict | None:
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute(CLAIM_SQL, (self.settings.worker_id, self.settings.lease_seconds))
            row = cursor.fetchone()
            connection.commit()
            if row is None:
                return None
            return {col: row[i] for i, col in enumerate(CLAIM_COLUMNS)}
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                cursor.close()
            finally:
                connection.close()
