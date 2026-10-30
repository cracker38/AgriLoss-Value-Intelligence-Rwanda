# AgriLoss Rwanda — post-harvest storage and value addition

AgriLoss is a public website (and optional Streamlit host) for **Track 1: Agricultural Productivity** in the NISR 2026 Big Data Hackathon. It uses NISR’s 2024 Rwanda Seasonal Agricultural Survey (SAS) production data to help planners and researchers decide **which named crop groups to verify next** for two challenges:

1. **Post-harvest collection and storage**
2. **Processing and value addition**

The app does not produce official survey estimates, national loss rates, causal findings, or forecasts.

## Purpose and potential relevance

Rwanda’s **NST2** aims to raise productivity on priority food crops and to cut food-crop post-harvest losses from **13.8% to 4.8%**, including through post-harvest handling, market linkages, and agro-processing. **Vision 2050** frames a market-oriented, food-secure agriculture sector. **PSTA 5** cites a 2023 study with value-chain losses of 13.8% (maize), 12.4% (rice), and 11.3% (beans). Those published targets and study rates are shown in the app as national context. They are **not** calculated from the SAS 2024 sample.

AgriLoss answers a practical first question: given the SAS 2024 production sample, which crop groups have reported-loss coverage or harvest patterns that justify opening the survey’s storage, collection, processing, and sales fields next? Relevance to NST2 and Vision 2050 is therefore specific to those two track areas. This project is **not** an official policy assessment or NISR endorsement.

The tool is an exploratory prototype, not an operational early-warning or farmer-targeting system.

## What is in the website

Open `index.html` through XAMPP at `http://localhost/AgriLoss/` (or run Streamlit, which embeds the same site).

- **Home:** the challenge in everyday language, who it is for, and what the 2024 survey recorded.
- **Find a crop / header search:** look up maize, beans, cassava, and other named crops.
- **Storage and processing:** sort crops by stored harvest, storage-stage loss, processing, or sales.
- **Crop page:** plain-language readings, season comparison, Season A sales places and practices, and a downloadable follow-up note.
- **Compare / practices / about:** season charts, a selectable province summary, district summaries when present in the reviewed public aggregate release, practice tables, and how to read the numbers.
- The public file contains grouped SAS 2024 summaries only. No farmer or plot rows are shown.

The hosted dashboard contains aggregate summaries only. Its current release is marked provisional because NISR disclosure review is not recorded; the app displays this status. The local respondent-level extracts and SQLite database are excluded from the public repository.

## NISR 2026 hackathon submission package

The project is aligned with **Track 1: Agricultural Productivity**. NISR's track includes crop production and post-harvest topics; the app offers exploratory survey summaries, not intervention recommendations.

See the [official NISR 2026 competition rules and timeline](https://www.statistics.gov.rw/about/hackathon/2026-hackathon-competition).

- **Public GitHub repository:** [AgriLoss Rwanda](https://github.com/cracker38/AgriLoss-Value-Intelligence-Rwanda)
- **Deployed app:** [agriloss-rwanda.streamlit.app](https://agriloss-rwanda.streamlit.app/)
- **Data artifact:** [`public_data/dashboard_aggregates.json`](public_data/dashboard_aggregates.json), a derived, aggregate-only file.
- **Original NISR data source:** [Rwanda Seasonal Agricultural Survey 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113). The local source extracts are not committed.
- **Screen recording:** required by the submission instructions and limited to three minutes. It is not included yet; use the [demo recording script](docs/demo-recording-script.md).
- **AI-use disclosure:** a draft is in [`docs/ai-use-disclosure.md`](docs/ai-use-disclosure.md); the team must verify it against all tools and work used.
- **Impact pathway:** [`docs/impact-and-validation-plan.md`](docs/impact-and-validation-plan.md) describes intended users, validation tasks, and evidence needed before making impact claims.
- **Submission checks:** eligibility, registration, originality, IP terms, and deadline are tracked in [`docs/hackathon-submission-checklist.md`](docs/hackathon-submission-checklist.md).

NISR's current page lists the registration deadline as 20 October 2026 and the submission deadline as 30 October 2026 at 11:59 PM. The registration date has passed. If the team did not register, contact the organizer rather than assuming late entry is allowed. Read the official rules before submitting, including the IP assignment requirement.

## Evaluation-criteria readiness

| NISR judging criterion | Current evidence | Readiness and remaining work |
|---|---|---|
| Problem Understanding & Relevance (20) | Track 1 focus on post-harvest collection/storage and processing/value addition, tied to NST2 (13.8% → 4.8% food-crop post-harvest loss), Vision 2050, and PSTA 5 study rates, using SAS 2024 production records as the evidence base. | Alignment is documented, not a measured contribution to those targets. Validate usefulness with intended Rwandan users. |
| Data Use & Methodology (20) | NISR SAS 2024 production extracts, source audit, missing values kept missing, independent crop/season/province aggregates, and public NST2/PSTA 5 context that is labelled as non-sample. | No survey-weighted estimates. Storage and processing fields are specified as next checks, not yet published as crop ranks. |
| Tech Innovation (20) | Python, Streamlit, pandas, Plotly, scikit-learn, aggregate release pipeline, two-track workspace, NST2 crop tagging, and downloadable briefs. | The classifier remains a local retrospective experiment and is not a public farmer score or alert system. |
| Usability & Design (20) | Start-here guidance, glossary, two challenge tracks, one-rule sorting, plain-language metrics, charts, and a crop brief. | Complete the required screen recording and a short user check. |
| Tangible Impact (20) | The workflow turns a crop pattern into a written next step for planners, cooperatives, or partners, with explicit non-use rules. | No outcome has been measured. See `docs/impact-and-validation-plan.md`. |

## Data sources and interpretation

The local source package contains 12 JSON extracts for SAS 2024 production, screening, agricultural practice, and fertilizer/pesticide modules across Seasons A, B, and C. The hosted dashboard reads disclosure-reviewed aggregate summaries. Crop and province summaries are separate marginal tables; the selected province is context only and is never combined with crop values. The other respondent-level modules are not joined: the audit found unresolved grain and match-rate issues, including for Season B. The [NISR SAS 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113) is the source link for the data used. The data audit and research design are in `docs/`.

No external dataset is currently integrated. NISR's Track 1 permits solutions using NISR data with or without other open/public datasets. An external weather, climate, or geospatial dataset should be added only with verified source terms, spatial/time alignment, and a clear analytical purpose.

Important boundaries:

- The charts show unweighted sample descriptions, not Rwanda, province, or district population estimates.
- Blank `s2q39` responses are treated as missing, not zero. Its unit is not confirmed in the published field label, so the app does not label these values as kg.
- Season C has a restricted sample. It is included in descriptive views but excluded from the exploratory model.
- The project has not implemented verified survey-weighted estimates, uncertainty intervals, or a complex-survey variance estimator.
- Raw respondent-level data must not be exposed through a public API or deployment. Confirm NISR's current data-use conditions before sharing datasets, derived files, or a hosted application.

## Exploratory model: what it does and does not mean

The training script creates a binary target from the observed survey field: `s2q39 > 0` means “positive reported-loss value,” and `s2q39 == 0` means “zero reported-loss value.” It excludes blank target responses. This is not a loss-severity threshold, and the target's unit and survey response process remain unresolved.

The model is a histogram gradient-boosting classifier using one-hot-encoded season, reported province/district, farmer/frame category, sex, crop and crop category, plus physical plot area. It excludes the loss-stage and downstream production fields to reduce leakage. Evaluation uses five-fold stratified group cross-validation, with all records sharing `Segment_ID + s2q1` kept in the same fold. Metrics are compared with an always-negative baseline because positive records are uncommon. The app displays evaluation metrics only; it does not calculate an individual score.

Accuracy, precision, recall, F1, balanced accuracy, ROC AUC, and average precision are calculated from out-of-fold predictions at a fixed 0.5 threshold. The positive class is uncommon, so accuracy is shown with recall and an always-negative baseline; a high accuracy alone does not mean positive-loss records are reliably detected. Candidate models were compared during development on this same sample, so these cross-validation scores are exploratory rather than an independent estimate. Validate against new data before operational use. The results are retrospective discrimination on the 2024 sample—not a causal model, calibrated risk score, or prediction of future loss. Survey weights are not applied, and the app must not be used to rank or target individual farmers.

## Run locally

Use Python 3.10 or later. The public website is `index.html`. From XAMPP, open `http://localhost/AgriLoss/`.

To host the same site in Streamlit:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

The dashboard reads the JSON production extracts from `dataset/nisrdataset/` and displays only aggregates.

For tests and audit development, install the development dependencies instead:

```powershell
py -3 -m pip install -r requirements-dev.txt
```

## Deploy on Streamlit Community Cloud

The app entrypoint is `app.py` and runtime dependencies are in the root `requirements.txt`. Connect the GitHub repository to Streamlit Community Cloud and select `app.py` as the entrypoint; the existing Dockerfile is not needed for this host.

The local respondent-level extracts and generated artifacts are intentionally Git-ignored. A hosted checkout therefore cannot use the local loader. To prepare an aggregate release candidate from authorized local source files, run:

```powershell
py -3 -m scripts.build_public_dashboard
```

This writes `artifacts/dashboard_release_candidate.json`, which remains Git-ignored. The candidate contains only independent season, province, and crop summaries, pools small groups, and omits respondent rows and individual model scores. Its group-size suppression is a preliminary safeguard, **not** disclosure approval. Confirm NISR's current data-use conditions and complete the required disclosure review before publishing any derived data.

After that review, place the approved file at `public_data/dashboard_aggregates.json`, record its review status and reference in the JSON, and commit that aggregate file with the app code. The public app checks for the recorded approval before serving approved mode. A repository owner may explicitly authorize a provisional release before review is recorded; the app then displays a warning and does not label the data NISR-approved. The currently published file uses that provisional status. The aggregate view intentionally omits combined season/province/crop filtering. Do not add `dataset/`, SQLite staging databases, or row-level source files to the hosted repository.

## Train or retrain the model

```powershell
py -3 -m scripts.train_loss_model
```

Training writes:

- `artifacts/loss_classifier.joblib` — fitted preprocessing and classifier pipeline
- `artifacts/loss_model_metrics.json` — target definition, split protocol, exclusions, and measured metrics

The local dashboard reads the metrics for retrospective evaluation and checks that the fitted model artifact exists. It does not expose a score or forecast. The public aggregate edition omits respondent-level model inputs and does not need the model binary. Do not edit the evaluation metrics by hand; regenerate them by running the training command.

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
- `scripts/build_public_dashboard.py` — local aggregate release-candidate builder
- `scripts/public_dashboard.py` — public aggregate-only dashboard renderer
- `scripts/train_loss_model.py` — reproducible model training and grouped evaluation
- `scripts/audit_sas_2024.py` — source and data-quality audit
- `scripts/ingest_sas_2024.py` — provenance-preserving raw SQLite staging
- `dataset/nisrdataset/` — local SAS JSON extracts
- `docs/` — audit findings, schema, and research design
- `docs/hackathon-submission-checklist.md` — NISR 2026 requirements and last-mile checklist
- `docs/demo-recording-script.md` — timed plan for the required short app demonstration
- `docs/ai-use-disclosure.md` — draft disclosure for team review
- `docs/impact-and-validation-plan.md` — intended users and proposed evidence checks
- `artifacts/` — generated local database, model, and metrics
- `public_data/` — aggregate-only dashboard release; current release status is stated in the data file and app
- `tests/` — audit, ingestion, and dashboard/model tests
