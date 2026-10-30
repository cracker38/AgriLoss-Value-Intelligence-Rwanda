# AgriLoss Rwanda

AgriLoss helps planners, researchers, cooperatives, and agricultural partners decide **which crop patterns may be worth checking more closely** for post-harvest storage and processing in Rwanda.

The dashboard summarizes Rwanda’s 2024 Seasonal Agricultural Survey (SAS). It lets users explore what surveyed households reported about crop harvests, storage, processing, sales, and related practices. The goal is to turn those survey patterns into useful questions for follow-up—not to prescribe an intervention or claim why a loss occurred.

AgriLoss is an independent research prototype, not an official NISR product. Its results describe the survey sample and are not national estimates, forecasts, causal findings, or assessments of individual farmers.

## Explore the dashboard

- **Live dashboard:** [agriloss-rwanda.streamlit.app](https://agriloss-rwanda.streamlit.app/)
- **Demonstration video:** [Watch on Google Drive](https://drive.google.com/file/d/1-0NvNiO9e79e2bfeB5hFv2x5RGYWjobm/view?usp=sharing)

Start at the home page, then:

1. **Find a crop** using the crop directory or search.
2. **Explore storage or processing** to compare crops using one survey measure at a time, such as reported storage, processing, or sales.
3. **Open a crop page** to review its sample summary and available season, practice, or market information.
4. **Compare** season and province sample summaries.
5. **Plan a follow-up** by downloading a note that helps organize questions for local verification.

The charts and downloadable notes support further investigation. They do not identify a cause, prove that a particular solution will work, or establish that a project is profitable.

## Data and how to interpret it

The source is the [NISR Rwanda Seasonal Agricultural Survey 2024](https://microdata.statistics.gov.rw/index.php/catalog/113). The hosted app reads [`public_data/dashboard_aggregates.json`](public_data/dashboard_aggregates.json), a file of grouped summaries rather than respondent- or plot-level records.

Results are **unweighted descriptions of the available sample**. They should not be read as national or province population estimates. Crop and province summaries are separate; a province chart does not filter or recalculate the crop figures. Policy targets shown in the app provide background context and are not calculated from SAS 2024.

The public aggregate release is marked provisional because NISR disclosure review is not recorded. Small-group suppression is a preliminary safeguard, not formal disclosure approval. Confirm NISR’s data-use conditions before sharing or publishing data or derived results.

## Run locally

Use Python 3.10 or later. From the project folder:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

Alternatively, serve `index.html` through XAMPP at `http://localhost/AgriLoss/`.

Do not publish respondent-level survey files, SQLite databases, or raw model inputs.
