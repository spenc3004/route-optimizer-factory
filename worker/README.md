# worker/ — queue consumer

The poll/claim/run/report loop that turns the optimizer into a queue-driven
service, modeled on `nm-factory-new`.

## Flow

```
loop:
  claim a dbo.ro_jobs row   (db.py: READPAST/UPDLOCK/ROWLOCK + lease, plan §15)
  POST RUNNING              (callback.py -> backend POST /ro/progress)
  resolve input from EFS    (storage.py: route_optimizer/<jobId>/)
  run optimizer/cli.py      (runner.py: subprocess per job, score|roi)
  write result.json         (storage.py)   # cli writes ranked.xlsx/roi.xlsx itself
  POST COMPLETED | FAILED   (callback.py)
```

Status transitions (RUNNING/COMPLETED/FAILED) go through the backend webhook,
which owns the `ro_jobs` status update + realtime emission — the worker only
*claims* via SQL. cli.py runs as a subprocess per job for parity + process
isolation (a pandas blowup dies in the child, not the loop).

## Modules

- `settings.py` — env config (`load_settings()`).
- `db.py` — the atomic claim query (`Db.claim_next_job`).
- `storage.py` — EFS read/write by jobId; stages a parent's run-parts for ROI.
- `runner.py` — build cli args + parse cli output (pure) + `run_cli` (subprocess).
- `callback.py` — `POST /ro/progress` with the shared-secret bearer header.
- `run.py` — the loop (`main()`); the process entrypoint (`python worker/run.py`).

## Run locally

```bash
cp ../.env.example ../.env   # fill RO_* + EFS_PATH + RO_WORKER_SECRET (matching the backend)
pip install -r requirements.txt -r ../optimizer/requirements.txt
python run.py
```

ROI jobs (`Kind='roi'`) read the parent's `ranked.pkl` + run-parts; the worker
stages them into the ROI job's dir before running `cli.py --mode roi`.
