# worker/ — queue consumer (Phase 4)

Not implemented yet. This is the poll/claim/run/report loop that turns the
extracted optimizer into a queue-driven service, modeled on `nm-factory-new`.

Planned modules (see `route-optimizer-decoupling-plan.md` §10):

- `run.py` — main loop: claim a `dbo.ro_jobs` row (READPAST/UPDLOCK/ROWLOCK +
  lease), read `input` + `jobSpec.json` from EFS, run `optimizer/cli.py` as a
  subprocess, write `result.json` + `ranked.xlsx` (+ `roi.xlsx`) to EFS, then
  `POST /ro/progress` to the backend.
- `storage.py` — EFS read/write keyed by `jobId` under `route_optimizer/`.
- `callback.py` — `POST /ro/progress` client with the shared-secret bearer header
  (`RO_WORKER_SECRET`); see plan §7a.

Configuration is documented in `../.env.example`.

Until this lands, the backend continues to exec its own copy of `optimizer/`
in-process (strangler); this repo's `optimizer/` is independently runnable and
parity-tested via `../tests/`.
