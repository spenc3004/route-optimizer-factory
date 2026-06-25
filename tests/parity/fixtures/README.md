# Parity fixtures

This directory holds the inputs and captured baselines the parity harness diffs
against. **Client report data is proprietary and is git-ignored** — only the
`synthetic/` fixture and this README are committed.

## Layout (per case)

```
fixtures/
  synthetic/home_services.csv      # committed; used by tests/test_smoke.py
  cc-myers/                        # git-ignored (real client data)
    input.xlsx                     #   the penetration report
    baseline.result.json           #   captured `cli.py --mode score` stdout from the ORIGINAL tool
    baseline.ranked.xlsx           #   (optional) captured ranked workbook
  ...                              # bay-cities, ace-handyman, etc. (the 4 known pairs)
```

## Capturing a baseline

Run the **original** implementation (pre-extraction backend, or the archived
Streamlit tool) for each client and save its `score` result JSON as
`baseline.result.json`, and the produced workbook as `baseline.ranked.xlsx`.
Then describe each case in a manifest (copy `../manifest.example.json` to
`../manifest.json`) and run:

```bash
.venv/bin/python tests/parity/run_parity.py tests/parity/manifest.json
```

The harness compares `dashboardModel`, `rankedRows`, `rankedColumns` (and ROI
fields for `mode:"roi"`) numerically within `floatTolerance`, plus every cell of
the ranked sheet if `baselineXlsx` is given. **C&C Myers must match** — it is the
case that exposed the weight-renormalization bug (`_effective_weights`).

## Output-vs-output comparison (when you only have ranked workbooks)

When you have the **original Streamlit** ranked workbook and the **current**
dashboard ranked workbook (but not the raw penetration-report input), use the
output comparator instead. Drop each pair under a case folder and list them in
`../outputs_manifest.json` (copy `../outputs_manifest.example.json`):

```
fixtures/
  cc-myers/      original.xlsx  current.xlsx
  4front-energy/ original.xlsx  current.xlsx
  cba-broomfield/original.xlsx  current.xlsx
```

```bash
.venv/bin/python tests/parity/compare_outputs.py
```

It diffs the **Ranked Geocodes** sheet exactly (every column, ranking order,
Composite Score), and reports **Dashboard Data** / **Summary** after excluding
three known-benign deltas: sheet order (Ranked-first), the `$`-prefixed
income/home-value bracket labels, and Summary audit rows in a different order
with identical per-label values.

**Validated 2026-06-25:** 4Front Energy, C&C Myers, CBA Broomfield — Ranked
Geocodes byte-identical (incl. C&C Myers Composite Score post-`_effective_weights`).
