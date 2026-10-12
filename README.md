# AgriLoss & Value Intelligence Rwanda 🇷🇼

### NISR 2026 Big Data Hackathon — Track 1: Agricultural Productivity

**Turning Rwanda's agricultural survey data into insights for productivity, post-harvest loss reduction, and value addition.**

## Project Overview

AgriLoss & Value Intelligence Rwanda is a data-driven agricultural analysis project developed for the NISR 2026 Big Data Hackathon.

The project uses Rwanda's Seasonal Agricultural Survey (SAS) 2024 datasets to investigate agricultural production, farming practices, fertilizer and pesticide use, crop-area patterns, and seasonal differences.

The long-term goal is to identify useful indicators of agricultural productivity challenges and support evidence-based decisions concerning crop collection, storage, processing, and value addition.

## Problem Statement

Improving agricultural productivity requires more than increasing crop production. It also requires understanding differences between agricultural seasons, farming practices, crop areas, and the conditions that may influence the value of agricultural output.

This project explores how agricultural survey data can reveal meaningful patterns and inform potential interventions.

**Important:** The available survey datasets do not automatically establish actual post-harvest losses. Such losses must be measured using appropriate loss data or validated indicators.

## Project Objectives

- Analyze agricultural survey datasets from Seasons A, B, and C.
- Understand crop production and agricultural practices.
- Investigate fertilizer and pesticide use.
- Examine crop-area patterns and differences between seasons.
- Identify data quality issues, including blank responses, missing values, and duplicate records.
- Engineer meaningful features for agricultural analysis.
- Evaluate suitable machine learning approaches when appropriate target variables are available.
- Develop evidence-based recommendations for productivity and value addition.

## Data Sources

The primary source is the **Rwanda Seasonal Agricultural Survey (SAS) 2024**, provided by the National Institute of Statistics of Rwanda (NISR).

Official source: [National Institute of Statistics of Rwanda](https://www.statistics.gov.rw/)

The project uses 12 JSON datasets covering three agricultural seasons and four dataset categories.

| Season | Dataset categories |
|---|---|
| Season A | Production, Agricultural Practice, Fertilizer and Pesticide, Screening |
| Season B | Production, Agricultural Practice, Fertilizer and Pesticide, Screening |
| Season C | Production, Agricultural Practice, Fertilizer and Pesticide, Screening |

## Methodology

The project follows a structured data science workflow:

1. **Project Objective** — Define the agricultural problem and analytical goals.
2. **Data Sources** — Document the survey datasets and their categories.
3. **Import Libraries** — Prepare the Python analysis environment.
4. **Load Dataset** — Load and validate the 12 JSON files.
5. **Data Understanding** — Inspect dataset dimensions, column types, descriptive statistics, and data quality.
6. **Data Cleaning** — Investigate blank responses, missing values, duplicates, and inconsistent records.
7. **Exploratory Data Analysis** — Analyze crop categories, crop areas, seasonal patterns, and district-level indicators where supported by the data.
8. **Feature Engineering** — Prepare analytical variables for further investigation.
9. **Machine Learning** — Develop suitable predictive models if the data supports a valid prediction task.
10. **Model Evaluation** — Assess models using appropriate metrics and validation methods.
11. **Conclusions** — Summarize verified findings, limitations, and practical recommendations.

## Technology Stack

- **Language:** Python
- **Environment:** Google Colab
- **Data processing:** Pandas, NumPy
- **Visualization:** Matplotlib
- **Machine learning:** Scikit-learn
- **Data format:** JSON
- **Storage:** Google Drive
- **Version control:** Git and GitHub

## Repository Structure

```text
AgriLoss-Value-Intelligence-Rwanda/
├── NISR_2026_Agri_Productivity_Analysis.ipynb
├── README.md
├── requirements.txt
├── .gitignore
├── src/
├── reports/
└── visualizations/
```

The notebook is the main analytical workflow. Additional folders can be populated as reusable code, reports, and visualizations are developed.

## Current Progress

The following activities have been demonstrated in the notebook:

- [x] Defined the project objective and data sources.
- [x] Identified the 12 SAS 2024 JSON datasets.
- [x] Configured Google Drive dataset storage.
- [x] Validated the existing JSON files.
- [x] Loaded and inspected agricultural datasets.
- [x] Examined data types, missing values, duplicates, and blank responses.
- [x] Classified columns by blank-response percentage.
- [x] Started exploratory analysis of crop categories and crop-area patterns.
- [ ] Complete and validate data cleaning.
- [ ] Complete exploratory data analysis.
- [ ] Develop and validate meaningful features.
- [ ] Select and train suitable machine learning models.
- [ ] Evaluate model performance.
- [ ] Finalize findings and recommendations.

*Progress reflects the notebook content documented in this project description; check the latest runtime outputs before marking additional stages complete.*

## Getting Started

### 1. Open the notebook

Open the notebook from the GitHub repository or upload it to Google Colab.

[Open Google Colab](https://colab.research.google.com/)

### 2. Install dependencies

Run the following command in a notebook cell:

```python
%pip install pandas numpy matplotlib scikit-learn
```

### 3. Configure dataset storage

The current notebook uses Google Drive for persistent dataset storage.

Example path:

```python
DATASET_PATH = (
    "/content/gdrive/MyDrive/M Training Deliverables/"
    "NISR_Hackathon/datasets"
)
```

Update the path if your Google Drive folder differs.

### 4. Run the notebook

Execute the notebook cells in order, ensuring that Google Drive is mounted and the required datasets are accessible.

## Expected Outcomes

- A reproducible analysis of the SAS 2024 datasets.
- Insights into crop production, agricultural practices, and seasonal patterns.
- Visualizations of crop categories and crop-area distributions.
- Data-supported identification of potential productivity challenges.
- Validated machine learning results if a suitable prediction target is established.
- Recommendations for further investigation into post-harvest management and agricultural value addition.

## Project Team

**NISR 2026 Big Data Hackathon — Track 1: Agricultural Productivity**

- **Elias DUKUZUMUREMYI**
- **MASENGESHO Pacifique**

## Responsible Data Use

- Respect NISR data access and licensing conditions.
- Do not publish sensitive or restricted records.
- Distinguish observed results from hypotheses and recommendations.
- Avoid interpreting correlation as causation.
- Report model limitations and validation results transparently.

## License

The project license will be determined after reviewing the applicable dataset terms and confirming the team's preferred software license.

---

**AgriLoss & Value Intelligence Rwanda**

*Data-driven insights for agricultural productivity, resilience, and value addition in Rwanda.*
