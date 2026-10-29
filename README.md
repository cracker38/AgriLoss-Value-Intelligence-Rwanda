# AgriLoss Rwanda — post-harvest storage and value addition

AgriLoss is a Streamlit prototype for **Track 1: Agricultural Productivity** in the NISR 2026 Big Data Hackathon. It uses NISR’s 2024 Rwanda Seasonal Agricultural Survey (SAS) production data to help planners and researchers decide **which named crop groups to verify next** for two challenges:

1. **Post-harvest collection and storage**
2. **Processing and value addition**

The app does not produce official survey estimates, national loss rates, causal findings, or forecasts.

## Purpose and potential relevance

Rwanda’s **NST2** aims to raise productivity on priority food crops and to cut food-crop post-harvest losses from **13.8% to 4.8%**, including through post-harvest handling, market linkages, and agro-processing. **Vision 2050** frames a market-oriented, food-secure agriculture sector. **PSTA 5** cites a 2023 study with value-chain losses of 13.8% (maize), 12.4% (rice), and 11.3% (beans). Those published targets and study rates are shown in the app as national context. They are **not** calculated from the SAS 2024 sample.

AgriLoss answers a practical first question: what do SAS 2024 production records report about storage, transport-stage loss, processing, sales, and market channels for each crop group, and what should planners verify locally? Relevance to NST2 and Vision 2050 is therefore specific to those two track areas. This project is **not** an official policy assessment or NISR endorsement.

The tool is an exploratory prototype, not an operational early-warning or farmer-targeting system.

## What is in the dashboard

- **Start here:** unweighted SAS 2024 sample indicators and their coverage.
- **Crop workspace:** compare reported storage, transport-stage loss, transformation, and sales patterns by crop. Review valid counts and data-quality checks, add a province as separate context and enter a local condition, then download a tailored follow-up brief.
- **Production links:** compare crop and post-harvest patterns with Season A practice/input responses, and inspect Season A sales channels and historical SAS prices by crop. These comparisons are descriptive and unweighted.
- **Explore the sample:** independent season, province, crop, and harvest summaries. Province and crop values are not cross-tabulated.
- **Data and methods:** source, cleaning rules, and interpretation limits.
- The local research edition shows retrospective classifier evaluation only. It does not generate an interactive score or a future-loss forecast. The public aggregate edition does not include respondent-level model inputs.

The hosted dashboard contains aggregate summaries only. Its current release is marked provisional because NISR disclosure review is not recorded; the app displays this status. The local respondent-level extracts and SQLite database are excluded from the public repository.

## NISR 2026 hackathon submission package

The project is aligned with **Track 1: Agricultural Productivity**. NISR's track includes crop production and post-harvest topics; the app offers exploratory survey summaries, evidence-backed investigation priorities, and processing options to evaluate. It does not recommend a specific investment.

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
| Problem Understanding & Relevance (20) | Track 1 focus on post-harvest collection/storage and processing/value addition, tied to NST2 (13.8% → 4.8% food-crop post-harvest loss), Vision 2050, and PSTA 5 study rates, using SAS 2024 production records as the evidence base. Crop briefs explain storage/transport investigation flags and food, drink, or other transformation-use options. | Alignment is documented, not a measured contribution to those targets. The flags are relative sample comparisons; processing routes are hypotheses to validate. Validate usefulness with intended Rwandan users. |
| Data Use & Methodology (20) | SAS production summaries cover storage, transport-stage loss, transformation, sales, and price coverage; Season A practice/input modules are linked at plot level after cardinality and weight checks; market-channel summaries use reported survey prices. | Descriptions are unweighted. No survey-weighted estimates or current market feed; Season A practice/input associations are observational. |
| Tech Innovation (20) | Python, Streamlit, pandas, Plotly, scikit-learn, aggregate release pipeline, two-track workspace, NST2 crop tagging, and downloadable briefs. | The classifier remains a local retrospective experiment and is not a public farmer score or alert system. |
| Usability & Design (20) | Start-here guidance, glossary, two challenge tracks, one-rule sorting, plain-language metrics, charts, recommendation evidence, and a downloadable crop brief. | Complete the required screen recording and a short user check. |
| Tangible Impact (20) | The workflow turns a crop pattern into a written next step for planners, cooperatives, or partners, with explicit non-use rules. | No outcome has been measured. See `docs/impact-and-validation-plan.md`. |

## Data sources and interpretation

The local source package contains 12 JSON extracts for SAS 2024 production, screening, agricultural-practice, and fertilizer/pesticide modules across Seasons A, B, and C. The dashboard summarizes production fields for storage (`s2q36`–`s2q38`), transport and storage losses (`s2q46`–`s2q47`), processing (`s2q25`), sales (`s2q26`–`s2q28`), and reported market channel. Season A agricultural-practice and fertilizer/pesticide responses are joined to production on `Segment_ID + s2q1` after plot-level reduction, exact key matching, response consistency, and plot-weight checks. Season B practice provenance and unresolved grain/linkage issues prevent publishing those comparisons; Season C remains separate because its sample is restricted. Screening is not joined to production because the crop-area linkage is not cleared. Crop and province summaries remain independent; the selected province is context only. See the [NISR SAS 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113), [data audit](docs/dataset-audit-2024.md), and [research design](docs/research-design-2024.md).

The [actionable recommendations note](docs/actionable-recommendations.md) explains the transparent rules behind storage/collection flags and processing options, the evidence shown in the app, Rwanda-based process examples, and the local checks required before a project decision.

No external dataset is currently integrated. NISR's Track 1 permits solutions using NISR data with or without other open/public datasets. An external weather, climate, or geospatial dataset should be added only with verified source terms, spatial/time alignment, and a clear analytical purpose.

Important boundaries:

- The charts show unweighted sample descriptions, not Rwanda, province, or district population estimates.
- Blank `s2q39` responses are treated as missing, not zero. Its unit is not confirmed in the published field label, so the app does not label these values as kg.
- Season C has a restricted sample. It is included in descriptive views but excluded from the exploratory model.
- The project has not implemented verified survey-weighted estimates, uncertainty intervals, or a complex-survey variance estimator.
- Raw respondent-level data must not be exposed through a public API or deployment. Confirm NISR's current data-use conditions before sharing datasets, derived files, or a hosted application.

## Exploratory model: what it does and does not mean

The training script creates a binary target from the observed survey field: `s2q39 > 0` means “positive reported-loss value,” and `s2q39 == 0` means “zero reported-loss value.” It excludes blank, nonnumeric, and negative responses. This is not a loss-severity threshold, and the target's unit and survey response process remain unresolved.

The model is a histogram gradient-boosting classifier using season, reported province/district, farmer/frame category, sex, crop and crop category, plus physical plot area. It excludes loss-stage and downstream production fields. The primary evaluation is five-fold stratified group cross-validation, with all records sharing `Segment_ID + s2q1` kept in one fold. The training script also runs a Season A train / Season B holdout, removing repeated plot groups from training. Both evaluations compare with an always-negative baseline because positive records are uncommon. The app displays aggregate evaluation metrics only; it does not calculate an individual score. The local metrics file must be regenerated with the training command to include the new holdout results.

The target is exactly `s2q39 > 0` versus `s2q39 == 0`, excluding blanks. It marks a positive reported value; it is not a loss-severity threshold or rate, and the field unit and response process remain unresolved. Accuracy, precision, recall, F1, balanced accuracy, ROC AUC, and average precision are calculated at a fixed 0.5 threshold. Because positive records are uncommon, accuracy is shown with recall and an always-negative baseline. Candidate models were compared during development on this sample, so the grouped cross-validation results are exploratory rather than independent. The Season A-to-B holdout measures transfer to a later survey season for the same response; it is **not** a future-period loss forecast because the predictors and target come from contemporaneous survey records and there is only one year of data. New survey waves, a time-appropriate target, confirmed field definitions, and independent prospective evaluation are required before forecasting. Survey weights are not applied; do not use the classifier to rank or target farmers.

## Run locally

Use Python 3.10 or later. From the repository root, install runtime dependencies and launch the app:

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

This writes `artifacts/dashboard_release_candidate.json`, which remains Git-ignored. The candidate contains independent season, province, and crop summaries plus thresholded Season A practice/input and market-channel summaries. It pools or suppresses small groups and omits respondent rows and individual model scores. Its group-size rule is a preliminary safeguard, **not** disclosure approval. Confirm NISR's current data-use conditions and complete the required disclosure review before publication.

After that review, place the approved file at `public_data/dashboard_aggregates.json`, record its review status and reference in the JSON, and commit that aggregate file with the app code. The public app checks for the recorded approval before serving approved mode. A repository owner may explicitly authorize a provisional release before review is recorded; the app then displays a warning and does not label the data NISR-approved. The currently published file uses that provisional status. The aggregate view intentionally omits combined season/province/crop filtering. Do not add `dataset/`, SQLite staging databases, or row-level source files to the hosted repository.

## Train or retrain the model

```powershell
py -3 -m scripts.train_loss_model
```

Training writes:

- `artifacts/loss_classifier.joblib` — fitted preprocessing and classifier pipeline
- `artifacts/loss_model_metrics.json` — target definition, split protocol, exclusions, and measured metrics

The local dashboard reads the metrics for grouped cross-validation and the Season A-to-B holdout, and checks that the fitted model artifact exists. It does not expose a score or forecast. The public aggregate edition omits respondent-level model inputs and does not need the model binary. Regenerate the metrics after changing the training script; do not edit them by hand.

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
