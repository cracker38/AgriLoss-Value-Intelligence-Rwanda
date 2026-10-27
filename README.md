# AgriLoss Rwanda: Hackathon Dashboard Prototype

AgriLoss Rwanda is a public-facing analytics prototype for the NISR 2026 Big Data Hackathon. It turns the raw SAS 2024 seasonal agricultural data into an aggregated, evidence-led dashboard that communicates agricultural production, crop concentration, and reported loss patterns without exposing respondent-level microdata.

## What this project does

This repository combines:
- the verified NISR SAS 2024 source extracts in `dataset/nisrdataset/`
- the raw staging and audit logic in `scripts/`
- an interactive Streamlit dashboard in `app.py`
- a local summary snapshot in `artifacts/dashboard_snapshot.json`
- a lightweight demo GIF in `demo/agri_loss_dashboard_demo.gif`

The dashboard is intentionally designed to be descriptive and aggregated. It focuses on the kinds of questions the project can responsibly answer from local, audit-verified survey records while staying clear on the limits of the data.

## Data sources and usage limits

The local data package includes 12 seasonal JSON extracts from the SAS 2024 survey, plus a Season B production CSV mirror. These are source files used for audit, validation, and descriptive analysis only.

Important boundaries:
- Raw microdata stays local and is not exposed through the dashboard.
- The app reports aggregated patterns only.
- It does not present weighted national estimates or causal findings.
- It is designed for public communication and hackathon demonstration, not for production decision-making without additional survey-design validation.

## App overview

The dashboard includes:
- total production rows by season
- top crops by reported counts
- distribution across provinces
- summary trends for reported loss values
- a clear interpretation note explaining the public-safe nature of the output

This makes the project suitable for a hackathon submission where the goal is to demonstrate relevance, clarity, and data use while staying transparent about method limits.

## Repository structure

- `app.py` — Streamlit dashboard entry point
- `scripts/build_dashboard_snapshot.py` — prepares aggregated summary data
- `scripts/generate_demo_gif.py` — creates a demo GIF for the repository
- `dataset/nisrdataset/` — NISR JSON source files
- `dataset/publicdataset/` — public mirror for Season B production CSV
- `docs/` — audit, schema, and research design notes
- `artifacts/` — generated outputs such as the raw SQLite DB and dashboard snapshot
- `demo/agri_loss_dashboard_demo.gif` — proof-of-concept visual demo

## Run the app locally

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 scripts/build_dashboard_snapshot.py
py -3 -m streamlit run app.py
```

## Generate the demo GIF

```powershell
py -3 scripts/generate_demo_gif.py
```

## Run the validation checks

```powershell
py -3 -m pytest tests -v
```

## Project intent

This prototype is designed to show a strong data-science and public-information story for Rwanda's agricultural sector:
- diagnose patterns in reported crop production and loss
- turn raw survey data into a visual narrative
- support policy relevance and user-friendly interpretation
- keep all outputs disclosure-aware and transparent about statistical limits

## Data access note

The source datasets are retained locally for audit and analytical preparation. Any public deployment must use aggregated results only and must remain consistent with NISR dissemination rules and the project's disclosure safeguards.
