# route-optimizer-factory — Contributor Rules

Standalone worker service for the Route Optimizer. Owns the Python engine
(`optimizer/`) and, from Phase 4, the queue worker (`worker/`).

## Parity is the prime directive
- `optimizer/cli.py` and `optimizer/utilities/*` are **copied verbatim** from
  `team-dashboard-backend-v3` and must stay **byte-identical**. Do NOT refactor,
  reformat, or "clean up" these files. Output parity with the original tool is a
  hard requirement (see the C&C Myers / `_effective_weights` case).
- The only sanctioned way to change scoring behavior is to change it in the
  source-of-truth engine and re-copy, then re-run the parity harness.
- `cli.py` reads its embedded `CATEGORY_CONFIG`. Config is **read-only** in v1;
  do not add a `--config-file` path (editable config is deferred).

## Contract
- `contract/config.json` is generated from `CATEGORY_CONFIG` by
  `contract/generate_config.py`. Never hand-edit it. After any config change:
  regenerate and commit; CI runs `generate_config.py --check`.
- Bump `CONTRACT_VERSION` in `generate_config.py` for any intentional change to
  config values or the `cli.py` JSON I/O shape. Jobs pin it for reproducibility.

## Worker (Phase 4)
- Mirror `nm-factory-new`: poll/claim `dbo.ro_jobs` (READPAST/UPDLOCK/ROWLOCK),
  run `cli.py` as a subprocess (per-job isolation), write artifacts to EFS,
  `POST /ro/progress` to the backend with the shared-secret bearer header.
- Keep secrets out of logs (no tokens, passwords, connection strings, PII).

## Tests
- `tests/test_smoke.py` must pass on synthetic data with no client files.
- Real parity runs via `tests/parity/run_parity.py` against committed baselines;
  client report data is proprietary and must never be committed.

## Boundaries
- This repo contains **no backend HTTP routes and no frontend**. It talks to the
  backend only via the `POST /ro/progress` callback and to the queue via SQL.
