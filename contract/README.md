# Config contract

`config.json` is the **read-only, versioned** artifact the Team Dashboard backend
caches so it can serve `GET /config` and validate uploaded columns for
`POST /jobs` **without running Python**.

## Regenerate

```bash
.venv/bin/python contract/generate_config.py          # writes config.json
.venv/bin/python contract/generate_config.py --check  # CI: non-zero if stale
```

The generator imports the same embedded `CATEGORY_CONFIG` as `cli.py`, so the
artifact can't silently drift from the engine. Never hand-edit `config.json`.

## Shape

Mirrors `cli.py:run_config` plus one addition the backend needs for Node-side
validation:

- `contractVersion` — human version; pinned per job (`ro_jobs.ConfigVersion` /
  `ContractVersion`). Bump in `generate_config.py` on any intentional change.
- `sourceHash` — content hash of the categories; drift detector.
- `categories[]` — per category: `name`, `presets`, `features`, `failFilters`,
  `ideals`, `drivers`, `profileDefaults`, `requiredColumnsBase`,
  **`requiredColumnsByPreset`** (the addition), `defaultWeightsByPreset`,
  `fixedStandardOnlyPresets`.

### Node-side validation (no Python)

```
required        = dedupe(requiredColumnsBase + requiredColumnsByPreset[preset])
missingColumns  = required \ fileColumns
disabledFilters = failFilters where required_column ∉ fileColumns
availableDrivers = drivers ∩ fileColumns
ok = missingColumns.length === 0
```
