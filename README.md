# AgriLoss Rwanda — SAS 2024 Crop Intelligence

AgriLoss is an evidence-led dashboard for exploring crop production and reported crop-loss patterns in the 2024 Rwanda Seasonal Agricultural Survey (SAS). It provides interactive, aggregated descriptions and a clearly bounded exploratory classification experiment. It does **not** currently produce official survey estimates, causal findings, or validated forecasts.

## What is in the dashboard

- Filter production records by season, province, and crop.
- Compare production-record counts, reported harvest values, and reported-loss patterns.
- Review missingness, sample sizes, and the model's evaluation protocol.
- Examine an exploratory classifier for whether a production record has a positive `s2q39` value.
- Optionally calculate an illustrative model score from selected crop and survey-context fields. This is not a calibrated probability or a future-loss prediction and must not be used to make decisions about individual farmers.

The app aggregates rows for display and does not render respondent-level records. The project still requires a public-release and disclosure review before deployment.

## Data sources and interpretation

The local source package contains 12 JSON extracts for SAS 2024 production, screening, agricultural practice, and fertilizer/pesticide modules across Seasons A, B, and C. This app reads only the production extracts. The data audit and research design are in `docs/`.

Important boundaries:

- The charts show unweighted sample descriptions, not Rwanda, province, or district population estimates.
- Blank `s2q39` responses are treated as missing, not zero. Its unit is not confirmed in the published field label, so the app does not label these values as kg.
- Season C has a restricted sample. It is included in descriptive views but excluded from the exploratory model.
- The project has not implemented verified survey-weighted estimates, uncertainty intervals, or a complex-survey variance estimator.
- Raw respondent-level data must not be exposed through a public API or deployment. Confirm NISR's current data-use conditions before sharing datasets, derived files, or a hosted application.

## Exploratory model: what it does and does not mean

The training script creates a binary target from the observed survey field: `s2q39 > 0` means “positive reported-loss value,” and `s2q39 == 0` means “zero reported-loss value.” It excludes blank target responses. This is not a loss-severity threshold, and the target's unit and survey response process remain unresolved.

The model is a class-weighted logistic regression using season, reported province/district, farmer/frame category, sex, crop, crop category, and physical plot area. It excludes the loss-stage and downstream production fields to reduce leakage. Evaluation uses five-fold stratified group cross-validation, with all records sharing `Segment_ID + s2q1` kept in the same fold. Metrics are compared with an always-negative baseline because positive records are uncommon.

Accuracy, precision, recall, F1, balanced accuracy, ROC AUC, and average precision are calculated from out-of-fold predictions at a fixed 0.5 threshold. No target metric is guaranteed or tuned to look high. The results are exploratory retrospective discrimination on the 2024 sample—not an external validation, causal model, calibrated risk score, or prediction of future loss. Survey weights are not applied, and the app must not be used to rank or target individual farmers.

## Run locally

Use Python 3.10 or later. From the repository root:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 -m streamlit run app.py
```

The dashboard reads the JSON production extracts from `dataset/nisrdataset/` and displays only aggregates.

## Train or retrain the model

```powershell
py -3 scripts/train_loss_model.py
```

Training writes:

- `artifacts/loss_classifier.joblib` — fitted preprocessing and classifier pipeline
- `artifacts/loss_model_metrics.json` — target definition, split protocol, exclusions, and measured metrics

The app reads those artifacts to display evaluation results and the optional illustrative score. Do not edit the evaluation metrics by hand; regenerate them by running the training command.

## Reproduce the source audit and tests

```powershell
py -3 scripts/audit_sas_2024.py
py -3 -m scripts.ingest_sas_2024
py -3 -m pytest tests -v
```

The SQLite database created by the raw staging loader contains respondent-level survey microdata. Keep it local and out of public deployments.

## Repository structure

- `app.py` — Streamlit dashboard
- `scripts/dashboard_data.py` — production source loading and filtering
- `scripts/train_loss_model.py` — reproducible model training and grouped evaluation
- `scripts/audit_sas_2024.py` — source and data-quality audit
- `scripts/ingest_sas_2024.py` — provenance-preserving raw SQLite staging
- `dataset/nisrdataset/` — local SAS JSON extracts
- `docs/` — audit findings, schema, and research design
- `artifacts/` — generated local database, model, and metrics
- `tests/` — audit, ingestion, and dashboard/model tests
