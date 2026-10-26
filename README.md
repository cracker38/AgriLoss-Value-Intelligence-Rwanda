# AgriLoss & Value Intelligence Rwanda

AgriLoss is an evidence-led agricultural data project for Rwanda. It is currently in its data-audit stage: the workspace contains NISR SAS 2024 extracts and audit artifacts, plus a local raw-staging loader. It does not yet have a canonical analytical database, backend, frontend, trained model, or notebook.

## Verified starting point

- `dataset/nisrdataset/` contains 12 JSON extracts for screening, production, agricultural practices, and fertilizer/pesticide modules across Seasons A, B, and C. The extracts contain 248,778 rows in total.
- `dataset/publicdataset/sas_2024_seasonB_production.csv` is a second representation of the Season B production JSON, not an extra sample.
- `docs/dataset-audit-2024.md` records the current field interpretation, sampling caveats, quality findings, and analysis limits.
- `docs/research-design-2024.md` defines the initial questions, indicator gates, and rules for separating observations from scenarios and future predictions.
- `docs/schema-inventory.json` and `docs/field-quality-summary.csv` describe the local schemas and field-level missingness/value checks.
- NISR's catalog lists 11 matching SAS 2024 files. The local Season B agricultural-practice extract is not listed in that dictionary and needs provenance confirmation.

The data supports descriptive analysis of crop production, reported crop losses, storage, sales, current transformation/use, and agricultural practices. The published label for `s2q39` does not state a unit. Survey weights, strata, clusters, and the restricted Season C design must be handled before results are described as population estimates. These files do not include verified processor capacity, conversion yields, costs, or demand, so they do not support profit prediction.

## Reproduce the source audit

The audit uses Python 3.10+ and only the standard library. Its tests use pytest. Neither the audit nor its tests modify raw survey files.

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 scripts/audit_sas_2024.py
py -3 -m scripts.ingest_sas_2024
py -3 -m pytest tests -v
```

The audit regenerates the schema inventory and field-quality CSV, and writes `docs/data-quality-checks.json` with checksums, row-level structural checks, duplicate-key diagnostics, crop-area formula checks, candidate production-screening linkage coverage, and the JSON/CSV mirror comparison. The module-linkage output is diagnostic; it does not authorize a join where coverage or cardinality is unresolved.

The SQLite command creates a local raw staging database at `artifacts/agri_loss_sas_2024.sqlite`. It stores each JSON record unchanged in meaning, with its source filename and row number, and records the source hash and row count. Re-running it skips unchanged files and replaces changed files in one transaction. It does not normalize values, merge modules, or calculate indicators. The database contains respondent-level microdata; keep it local and out of public deployments.

## Current implementation sequence

1. Reproduce and finalize the source audit and complete the variable dictionary.
2. Resolve questionnaire definitions, response codes, join grain, survey weights, and the Season B practice file's provenance.
3. Define canonical season-aware data mappings and validated descriptive indicators.
4. Extend raw staging into a canonical SQLite model and verify it against the raw sources.
5. Evaluate whether the verified data supports a supervised-learning task; keep scenario estimates separate from predictions.
6. Implement the FastAPI API and React/TypeScript client around validated, disclosure-reviewed indicators.

Raw SQLite staging is available before these analysis gates because it preserves the source rows without assigning statistical meaning to them. The audit, metadata, and mapping gates still block analytical outputs.

Raw respondent-level files must not be exposed through a public API or dashboard. Keep derived public outputs aggregated and review them for disclosure risk.
