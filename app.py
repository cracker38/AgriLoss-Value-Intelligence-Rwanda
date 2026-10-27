from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from scripts.build_dashboard_snapshot import build_snapshot

ROOT = Path(__file__).resolve().parent
SNAPSHOT_PATH = ROOT / "artifacts" / "dashboard_snapshot.json"


@st.cache_data
def load_snapshot() -> dict:
    if not SNAPSHOT_PATH.exists():
        return build_snapshot()
    with SNAPSHOT_PATH.open("r", encoding="utf-8") as source:
        return json.load(source)


st.set_page_config(page_title="AgriLoss Rwanda Dashboard", page_icon="🌾", layout="wide")
st.title("AgriLoss Rwanda Dashboard")
st.caption("Descriptive, aggregated view of NISR SAS 2024 agricultural production and loss indicators")

snapshot = load_snapshot()

summary = snapshot.get("season_summary", [])
if not summary:
    st.warning("No production summary is available yet. Run the dashboard builder to generate a snapshot.")
    st.stop()

season_option = st.selectbox("Season", options=[item["season"] for item in summary], index=0)
selected = next(item for item in summary if item["season"] == season_option)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Production rows", f"{selected['records']:,}")
with kpi_cols[1]:
    st.metric("Distinct crops", f"{selected['crop_count']}")
with kpi_cols[2]:
    st.metric("Reported loss count", f"{snapshot['loss_summary']['count']:,}")
with kpi_cols[3]:
    st.metric("Average loss (kg)", f"{snapshot['loss_summary']['avg_kg']:.2f}")

season_df = pd.DataFrame(summary)
season_chart = px.bar(
    season_df,
    x="season",
    y="records",
    color="season",
    title="Production rows by season",
    labels={"season": "Season", "records": "Rows"},
)
season_chart.update_layout(showlegend=False)
st.plotly_chart(season_chart, use_container_width=True)

left_col, right_col = st.columns(2)
with left_col:
    top_crops = pd.DataFrame(snapshot.get("top_crops", []))
    if not top_crops.empty:
        fig = px.bar(
            top_crops,
            x="crop",
            y="count",
            title="Most reported crop categories",
            color="crop",
        )
        fig.update_layout(xaxis_tickangle=-35, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No crop summary is available.")

with right_col:
    province_df = pd.DataFrame(snapshot.get("top_provinces", []))
    if not province_df.empty:
        fig2 = px.pie(
            province_df,
            names="province",
            values="count",
            title="Distribution across provinces",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No province summary is available.")

st.subheader("Interpretation note")
for note in snapshot.get("quality_notes", []):
    st.write("- " + note)

st.caption(f"Snapshot generated: {snapshot.get('generated_at_utc', 'unknown')}")
