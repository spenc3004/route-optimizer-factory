# route-optimizer-factory

Standalone worker service for the Mail Shark **Route Optimizer**. It owns the
Python scoring/ROI engine (`optimizer/`) and — once the queue plane lands — a
poll/claim/run/report loop (`worker/`) modeled on `nm-factory-new`.

This repo is the result of decoupling the optimizer out of
`team-dashboard-backend-v3`, where it previously ran in-process via `execFile`.
See `route-optimizer-decoupling-plan.md` and `route-optimizer-phase0-contracts.md`
(in the planning drop) for the full architecture and frozen contracts.

## Status

Complete and the sole home of the optimizer. The backend (`team-dashboard-backend-v3`)
no longer contains any Python — it is a Node control plane that creates jobs in
`dbo.ro_jobs`; this repo's `worker/` polls that table, runs `cli.py`, writes
artifacts to shared storage, and posts status back. Output parity with the
original tool is verified (`tests/parity/`).

Run the worker with `python worker/run.py` (see `worker/README.md`). Deployment
runs it as a long-lived process on a host that can reach the SQL DB + the shared
EFS mount; configuration is in `.env` (see `.env.example`).

## Layout

```
optimizer/            # the engine — COPIED VERBATIM from the backend. Do NOT refactor.
  cli.py              #   JSON entrypoint: --mode config|validate|score|roi
  utilities/*.py      #   scoring, normalization, ROI, Excel (parity-critical)
  assets/             #   logo for the Excel dashboard sheet
  requirements.txt    #   runtime deps (pandas, numpy, openpyxl, pillow)
contract/             # published, versioned config contract for the backend
  generate_config.py  #   regenerates config.json from CATEGORY_CONFIG
  config.json         #   the artifact the backend caches to serve /config + validate (Node)
worker/               # the queue consumer (poll ro_jobs -> run cli.py -> post status)
tests/
  test_smoke.py       # standalone runnability checks on synthetic data (CI-safe)
  test_worker.py      # worker pure-helper + storage tests
  parity/             # diff cli.py output vs committed client baselines
```

## The CLI contract

```
python optimizer/cli.py --mode <config|validate|score|roi> --args-file <json> --out-dir <dir>
```

Reads a JSON job spec (from `--args-file` or stdin), prints a JSON result to
stdout, writes any `.xlsx` (+ intermediate `.pkl`) into `--out-dir`. Exit codes:
`0` success, `2` validation failure, `1` internal error. Non-fatal issues come
back in a `warnings[]` array. This contract is **frozen** and versioned by
`contract/config.json:contractVersion`.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r optimizer/requirements.txt -r requirements-dev.txt

# regenerate the published config contract (after any CATEGORY_CONFIG change)
.venv/bin/python contract/generate_config.py
.venv/bin/python contract/generate_config.py --check   # CI: fail if stale

# run the standalone smoke tests
.venv/bin/python -m pytest tests/test_smoke.py -q
```

## Parity

`tests/parity/run_parity.py` diffs `cli.py` output against captured client
baselines (`result.json` + optional `ranked.xlsx`). Client data is **never
committed** — drop the 4 known pairs under `tests/parity/fixtures/` and list them
in a manifest (see `tests/parity/fixtures/README.md`), then:

```bash
.venv/bin/python tests/parity/run_parity.py tests/parity/manifest.json
```

C&C Myers must match (the 0.9× Composite Score case fixed by `_effective_weights`).
