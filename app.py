from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from scripts.dashboard_data import (
    PUBLIC_DASHBOARD_PATH,
    available_values,
    filter_production_data,
    load_production_data,
    load_public_dashboard_data,
)
from scripts.public_dashboard import render_public_dashboard
from scripts.train_loss_model import METRICS_PATH, MODEL_PATH


ROOT = Path(__file__).resolve().parent
st.set_page_config(
    page_title="AgriLoss Rwanda | Post-harvest & value addition",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", sans-serif;
        color: #18352d;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(221, 239, 229, 0.6), transparent 34rem),
            #f5f8f6;
    }
    .block-container { max-width: 1320px; padding-top: 1.6rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] {
        background: #102c24;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * { color: #edf6f1; }
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label { color: #c8ddd3 !important; }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] > div,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.17);
    }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.2rem 1.8rem;
        border: 1px solid rgba(255,255,255,0.13);
        border-radius: 24px;
        color: #f6fbf7;
        background:
            radial-gradient(ellipse at 92% 8%, rgba(215, 187, 111, 0.3), transparent 38%),
            linear-gradient(120deg, #102c24 0%, #155640 62%, #1c7655 100%);
        margin: 0 0 1.5rem;
        box-shadow: 0 18px 42px rgba(16, 44, 36, 0.15);
    }
    .hero .eyebrow {
        display: inline-block;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        padding: 0.3rem 0.72rem;
        border-radius: 999px;
        margin-bottom: 0.85rem;
    }
    .hero h1 {
        font-size: clamp(2rem, 4vw, 3rem);
        letter-spacing: -0.045em;
        line-height: 1.08;
        margin: 0 0 0.65rem;
    }
    .hero p { color: #e0eee7; margin: 0; max-width: 52rem; font-size: 1.08rem; line-height: 1.55; }
    .hero-meta { margin-top: 1rem; color: #cbe0d5; font-size: 0.88rem; }
    .callout {
        padding: 1rem 1.1rem;
        border: 1px solid #f0dfc3;
        border-left: 4px solid #c9862a;
        border-radius: 12px;
        background: #fffaf1;
        color: #493d2d;
        margin: 0.9rem 0 1.2rem;
    }
    .info-card, .step-card {
        background: linear-gradient(145deg, #fff 0%, #fbfdfb 100%);
        border: 1px solid #e1ebe5;
        border-radius: 18px;
        padding: 1.2rem;
        min-height: 8.5rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 5px 16px rgba(22, 61, 47, 0.045);
    }
    .info-card h4 { margin: 0 0 0.45rem; color: #126246; font-size: 1.04rem; }
    .info-card p, .step-card p { margin: 0; color: #456157; line-height: 1.55; }
    .step-card { display: flex; gap: 0.85rem; align-items: flex-start; min-height: 7rem; }
    .step-card span {
        flex: 0 0 1.7rem;
        height: 1.7rem;
        border-radius: 999px;
        background: #e6f3eb;
        border: 1px solid #cfe5d8;
        color: #126246;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
    }
    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid #e1ebe5;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        box-shadow: 0 5px 16px rgba(22, 61, 47, 0.04);
    }
    [data-testid="stTabs"] [role="tablist"] {
        gap: 0.4rem;
        border-bottom: 1px solid #dfe9e3;
    }
    [data-testid="stTabs"] button {
        font-weight: 650;
        color: #5b7068;
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1rem;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #126246;
        background: #eaf4ee;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] [role="combobox"],
    [data-testid="stMultiSelect"] [role="combobox"] {
        border-radius: 10px;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #16805d;
        box-shadow: 0 0 0 2px rgba(22, 128, 93, 0.15);
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid #e1ebe5;
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stPlotlyChart"] {
        background: rgba(255,255,255,0.75);
        border: 1px solid #e7eee9;
        border-radius: 16px;
        padding: 0.35rem;
    }
    div[data-testid="stAlert"] { border-radius: 12px; }
    button[kind="primary"] {
        border-radius: 10px;
        font-weight: 650;
        box-shadow: 0 4px 10px rgba(15, 107, 78, 0.14);
    }
    @media (max-width: 700px) {
        .block-container { padding: 1rem 0.85rem 2rem; }
        .hero { padding: 1.4rem 1.25rem; border-radius: 18px; }
        .hero p { font-size: 1rem; }
        .info-card, .step-card { min-height: 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading and validating the SAS production extracts...")
def load_data() -> pd.DataFrame:
    return load_production_data()


@st.cache_data(show_spinner=False)
def load_model_metrics() -> dict[str, Any]:
    if not METRICS_PATH.is_file():
        return {}
    with METRICS_PATH.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError(f"Model metrics file must contain a JSON object: {METRICS_PATH}")
    return payload


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _bar_chart(data: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        labels={
            "s2q4": "Reported crop",
            "s1q1": "Province",
            "season": "Season",
            "records": "Production records",
            "positive_share": "Records reporting positive loss",
            "median_harvest": "Median reported harvest (kg)",
        },
        color_discrete_sequence=["#16805d", "#8abf43", "#d9a441", "#477c91"],
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=55, b=12),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )
    return fig


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">NISR 2026 Big Data Hackathon · Track 1: Agricultural Productivity</div>
      <h1>AgriLoss Rwanda</h1>
      <p>A clear first look at which crops in the SAS 2024 sample deserve follow-up on
      post-harvest collection and storage, and on processing and value addition.</p>
      <div class="hero-meta">NISR Seasonal Agricultural Survey 2024 · unweighted sample summaries · not official estimates</div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    if PUBLIC_DASHBOARD_PATH.is_file():
        public_data = load_public_dashboard_data()
        render_public_dashboard(public_data)
        st.stop()
    data = load_data()
except FileNotFoundError:
    st.error("This deployment has no authorized aggregate dashboard data file.")
    st.write(
        "Respondent-level SAS extracts are intentionally excluded from hosted deployments. "
        "The public dashboard requires an approved or owner-authorized aggregate file at:"
    )
    st.code("public_data/dashboard_aggregates.json", language="text")
    st.write(
        "To prepare a local review candidate from authorized source files, run "
        "`py -3 -m scripts.build_public_dashboard`. The generated file is kept under "
        "`artifacts/` and is not ready for public release until the required review is recorded."
    )
    st.stop()
except (OSError, ValueError, json.JSONDecodeError) as error:
    st.error(f"Could not load dashboard data: {error}")
    st.stop()

with st.sidebar:
    st.markdown("## Explore the survey")
    selected_seasons = st.multiselect(
        "Survey seasons",
        options=["A", "B", "C"],
        default=["A", "B", "C"],
        help="Season C has a restricted sample and is shown separately in the charts.",
    )
    if not selected_seasons:
        st.warning("Choose at least one season to view the dashboard.")
        st.stop()

    season_data = data[data["season"].isin(selected_seasons)]
    provinces = available_values(season_data, "s1q1")
    selected_provinces = st.multiselect("Province", provinces, default=provinces)
    province_data = season_data[season_data["s1q1"].isin(selected_provinces)]
    crops = available_values(province_data, "s2q4")
    selected_crops = st.multiselect("Crop", crops, default=[])
    st.divider()
    st.caption("Filters update descriptive aggregates only. No respondent records are displayed.")

filtered = filter_production_data(
    data,
    seasons=selected_seasons,
    provinces=selected_provinces,
    crops=selected_crops if selected_crops else None,
)

if filtered.empty:
    st.info("No records match these filters. Adjust the season or province selection.")
    st.stop()

loss = filtered["s2q39"].dropna()
positive_loss_count = int(loss.gt(0).sum())
positive_share = positive_loss_count / len(loss) if len(loss) else 0.0
reported_harvest = filtered["s2q21"].dropna()

metric_columns = st.columns(5)
metric_columns[0].metric("Production records", f"{len(filtered):,}")
metric_columns[1].metric("Distinct crops", f"{filtered['s2q4'].nunique():,}")
metric_columns[2].metric("Loss values reported", f"{len(loss):,}")
metric_columns[3].metric("Positive reported loss", f"{positive_loss_count:,}")
metric_columns[4].metric("Median harvest reported", f"{reported_harvest.median():,.0f} kg" if len(reported_harvest) else "—")

st.markdown(
    '<div class="callout"><strong>A quick note about these numbers:</strong> They describe the survey records '
    'shown here and are not estimates for Rwanda’s whole population. The unit for the reported-loss field '
    '<code>s2q39</code> has not been confirmed, so we show it as reported—not as kilograms or a loss rate.</div>',
    unsafe_allow_html=True,
)

overview_tab, loss_tab, model_tab, methods_tab = st.tabs(
    ["Overview", "Crop & loss analysis", "Model lab", "Data quality & methods"]
)

with overview_tab:
    st.subheader("What the survey records")
    st.write(
        "Intended users include public planners, researchers, civil society, and development partners. "
        "Use these aggregate views to identify questions for deeper analysis—not to rank farmers, allocate "
        "support, or claim that a particular intervention works."
    )
    season_counts = (
        filtered.groupby("season", as_index=False)
        .size()
        .rename(columns={"size": "records"})
    )
    crop_harvest = (
        filtered.dropna(subset=["s2q4", "s2q21"])
        .groupby("s2q4", as_index=False)
        .agg(median_harvest=("s2q21", "median"), records=("s2q21", "size"))
        .query("records >= 30")
        .sort_values("median_harvest", ascending=False)
        .head(15)
    )
    province_counts = (
        filtered.groupby("s1q1", as_index=False)
        .size()
        .rename(columns={"size": "records"})
        .sort_values("records", ascending=False)
    )
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            _bar_chart(season_counts, "season", "records", "Production records by season", "season"),
            width="stretch",
        )
    with right:
        if not crop_harvest.empty:
            st.plotly_chart(
                _bar_chart(crop_harvest, "s2q4", "median_harvest", "Median reported harvest by crop"),
                width="stretch",
            )
        else:
            st.info("Not enough records to display crop harvest groups under the 30-record display threshold.")

    if not province_counts.empty:
        st.plotly_chart(
            _bar_chart(province_counts, "s1q1", "records", "Records by province", "s1q1"),
            width="stretch",
        )
    st.caption(
        "Crop groups with fewer than 30 valid harvest records are omitted from this chart. "
        "The threshold is a display safeguard, not a survey-design or disclosure review."
    )

with loss_tab:
    st.subheader("Reported loss patterns")
    st.caption("s2q39 unit is undocumented in the available dictionary. The chart uses raw reported values, not kilograms.")
    loss_by_crop = (
        filtered.dropna(subset=["s2q4", "s2q39"])
        .groupby("s2q4", as_index=False)
        .agg(
            positive_share=("s2q39", lambda values: float(values.gt(0).mean())),
            records=("s2q39", "size"),
            median_reported_loss=("s2q39", "median"),
        )
        .query("records >= 30")
        .sort_values("positive_share", ascending=False)
        .head(20)
    )
    if not loss_by_crop.empty:
        st.plotly_chart(
            _bar_chart(loss_by_crop, "s2q4", "positive_share", "Share of valid records with positive reported loss"),
            width="stretch",
        )
        display_loss = loss_by_crop.rename(
            columns={
                "s2q4": "Crop",
                "records": "Valid reported-loss records",
                "positive_share": "Positive reported-loss share",
                "median_reported_loss": "Median reported value (unit unconfirmed)",
            }
        ).copy()
        display_loss["Positive reported-loss share"] = display_loss[
            "Positive reported-loss share"
        ].map(_format_percent)
        st.dataframe(display_loss, hide_index=True, width="stretch")
    else:
        st.info("No crop group meets the 30-record display threshold for loss comparisons.")
    st.caption("Missing loss responses are excluded from the denominator, not converted to zero.")

with model_tab:
    st.subheader("Retrospective classifier evaluation")
    metrics = load_model_metrics()
    if not metrics or not MODEL_PATH.is_file():
        st.warning("The model has not been trained yet.")
        st.code("py -3 -m scripts.train_loss_model", language="powershell")
    else:
        st.markdown(
            '<div class="callout"><strong>Research use only:</strong> This retrospective classifier distinguishes '
            'records where s2q39 is greater than zero from records where it is zero. It is not a forecast, '
            'causal analysis, calibrated risk estimate, or a score for individual farmers.</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"{metrics['model']} · {metrics['evaluation']} · seasons {', '.join(metrics['training_seasons'])} · "
            f"{metrics['rows_evaluated']:,} records · {metrics['groups']:,} plot groups"
        )
        st.write(
            f"Positive class prevalence: {_format_percent(metrics['positive_prevalence'])}. "
            f"Classification threshold: {metrics['threshold']:.2f} (fixed before evaluation)."
        )

        model_metrics = metrics["metrics"]
        baseline = metrics["majority_class_baseline"]
        metric_names = (
            ("Accuracy", "accuracy"),
            ("Precision", "precision"),
            ("Recall / sensitivity", "recall"),
            ("F1", "f1"),
            ("Balanced accuracy", "balanced_accuracy"),
            ("ROC AUC", "roc_auc"),
            ("Average precision", "average_precision"),
        )
        metric_table = pd.DataFrame(
            [
                {"Metric": label, "Classifier": model_metrics[key], "Always-negative baseline": baseline[key]}
                for label, key in metric_names
            ]
        )
        metric_table["Classifier"] = metric_table["Classifier"].map(_format_percent)
        metric_table["Always-negative baseline"] = metric_table[
            "Always-negative baseline"
        ].map(_format_percent)
        st.dataframe(metric_table, hide_index=True, width="stretch")
        st.info(
            f"Accuracy is {_format_percent(model_metrics['accuracy'])}, compared with "
            f"{_format_percent(baseline['accuracy'])} for the always-negative baseline. "
            f"The model detects {_format_percent(model_metrics['recall'])} of positive records; "
            "because positive records are uncommon, accuracy alone is not a measure of useful loss detection."
        )
        st.caption(
            "Validation caveat: candidate models were compared during development on this same SAS 2024 sample. "
            "These cross-validation results are exploratory, not independent validation."
        )

        season_holdout = metrics.get("season_holdout_evaluation")
        if season_holdout:
            st.markdown("#### Season A to Season B holdout")
            st.caption(
                f"Trained on {season_holdout['rows_trained']:,} Season A records and evaluated on "
                f"{season_holdout['rows_evaluated']:,} Season B records. "
                f"{season_holdout['repeated_plot_groups_removed_from_training']:,} repeated plot groups were removed from training."
            )
            st.write(
                f"Season B positive-response prevalence: "
                f"{_format_percent(season_holdout['positive_prevalence'])}. "
                f"This is an out-of-season check of the same `s2q39 > 0` response, not a forecast of a future loss outcome. "
                "Model development has already used these 2024 records, so this is not independent validation."
            )
            holdout_metrics = season_holdout["metrics"]
            holdout_baseline = season_holdout["always_negative_baseline"]
            holdout_table = pd.DataFrame(
                [
                    {
                        "Metric": label,
                        "Classifier": holdout_metrics[key],
                        "Always-negative baseline": holdout_baseline[key],
                    }
                    for label, key in metric_names
                ]
            )
            holdout_table["Classifier"] = holdout_table["Classifier"].map(_format_percent)
            holdout_table["Always-negative baseline"] = holdout_table[
                "Always-negative baseline"
            ].map(_format_percent)
            st.dataframe(holdout_table, hide_index=True, width="stretch")
        else:
            st.info(
                "The current metrics file has no Season A to Season B holdout. "
                "Regenerate it with `py -3 -m scripts.train_loss_model` to add that evaluation."
            )

        confusion = model_metrics["confusion_matrix"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("True positives", f"{confusion['true_positive']:,}")
        c2.metric("False positives", f"{confusion['false_positive']:,}")
        c3.metric("False negatives", f"{confusion['false_negative']:,}")
        c4.metric("True negatives", f"{confusion['true_negative']:,}")
        st.write("**Input variables used:** " + ", ".join(metrics["features"]))
        st.write("**Leakage controls:**")
        for control in metrics["leakage_controls"]:
            st.write(f"- {control}")
        st.write(f"**Important limitation:** {metrics['interpretation']}")

        st.info("No future-loss forecast is available. The target is a retrospective same-survey response, not a future outcome.")

with methods_tab:
    st.subheader("Data quality and analytical safeguards")
    st.markdown(
        "**Data source:** [NISR Rwanda Seasonal Agricultural Survey 2024 catalog]"
        "(https://microdata.statistics.gov.rw/index.php/catalog/113). "
        "This local edition reads the production extracts and displays aggregated descriptions."
    )
    quality = (
        data.groupby("season", as_index=False)
        .agg(
            production_rows=("s2q39", "size"),
            loss_values_reported=("s2q39", "count"),
            positive_loss_values=("s2q39", lambda values: int(values.gt(0).sum())),
            loss_values_missing=("s2q39", lambda values: int(values.isna().sum())),
            distinct_crops=("s2q4", "nunique"),
        )
    )
    st.dataframe(quality, hide_index=True, width="stretch")
    st.markdown(
        """
        **Interpretation and known limits**
        - These are unweighted survey-row descriptions. No district/province/national estimator or variance calculation is implemented.
        - Blank s2q39 responses remain missing. Positive/zero classification is a coding choice for exploratory evaluation, not a definition of loss severity.
        - The s2q39 unit is not stated in the available published field label. It is never labeled as kilograms in this app.
        - Season C uses a restricted sample. It is shown only in descriptive views and excluded from model training/evaluation.
        - The classifier uses season, reported location/frame/crop context, and physical plot area. It excludes loss-stage and post-harvest fields.
        - Survey identifiers are used only to keep plot groups together across evaluation folds; they are not model inputs.
        - Survey-weighted estimates, causal claims, yield estimates, profit prediction, and intervention recommendations are outside this prototype.
        - Public release still requires review against NISR's data-use and disclosure requirements.
        """
    )
    st.write("**Model evaluation protocol:**")
    st.write(
        "A fixed 0.5 threshold is evaluated using five-fold stratified group cross-validation. "
        "All records sharing the Segment_ID + plot key are held in one fold. The metrics are out-of-fold "
        "descriptive performance on this 2024 sample and are not an external validation. The training script "
        "also reports a Season A train / Season B holdout after removing repeated plot groups from training; "
        "it evaluates transfer across survey seasons, not a future-period loss forecast."
    )

st.caption("AgriLoss Rwanda · NISR SAS 2024 · Research prototype with explicit survey and model limitations")
