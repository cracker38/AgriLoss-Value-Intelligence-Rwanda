from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def _bar_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    y_label: str,
):
    figure = px.bar(
        frame,
        x=x,
        y=y,
        title=title,
        labels={x: "", y: y_label},
        color_discrete_sequence=["#16805d"],
    )
    figure.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=55, b=12),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )
    return figure


def render_public_dashboard(payload: dict[str, Any]) -> None:
    """Render only the pre-aggregated, approved public release."""
    overall = payload["overall"]
    seasons = pd.DataFrame(payload["by_season"])
    provinces = pd.DataFrame(payload["by_province"])
    crops = pd.DataFrame(payload["by_crop"])

    st.info(
        "This hosted view uses an approved aggregate release. It contains no respondent-level rows. "
        "Tables are unweighted sample descriptions, not population estimates."
    )
    review = payload["review"]
    st.caption(
        f"Disclosure review: {review['reviewed_by']} · {review['reviewed_on']} · "
        f"Reference: {review['reference']}"
    )

    overview_tab, crop_tab, model_tab, methods_tab = st.tabs(
        ["Overview", "Crop & loss analysis", "Model lab", "Data quality & methods"]
    )

    with overview_tab:
        st.subheader("SAS 2024 production records")
        columns = st.columns(5)
        columns[0].metric("Production records", f"{overall['records']:,}")
        columns[1].metric("Distinct crop values", f"{overall['distinct_crop_values']:,}")
        columns[2].metric("Loss values reported", f"{overall['loss_reported_records']:,}")
        columns[3].metric(
            "Positive reported loss",
            f"{overall['positive_reported_loss_records']:,}",
            _percent(overall["positive_reported_loss_share"]),
        )
        harvest_median = overall["median_reported_harvest_kg"]
        columns[4].metric(
            "Median harvest reported",
            f"{harvest_median:,.0f} kg" if harvest_median is not None else "—",
        )

        st.markdown(
            '<div class="callout"><strong>Interpretation:</strong> These are unweighted sample '
            'descriptions. The unit for reported-loss field <code>s2q39</code> is unconfirmed, so '
            'its values are not labeled as kilograms or a loss rate.</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "The season, province, and crop charts are independent marginal summaries. "
            "They are not cross-filtered against one another."
        )

        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                _bar_chart(
                    seasons,
                    x="season",
                    y="records",
                    title="Production records by season",
                    y_label="Production records",
                ),
                width="stretch",
            )
        with right:
            harvest = crops.dropna(subset=["median_reported_harvest_kg"]).copy()
            if not harvest.empty:
                harvest = harvest.sort_values(
                    "median_reported_harvest_kg", ascending=False
                ).head(15)
                st.plotly_chart(
                    _bar_chart(
                        harvest,
                        x="crop",
                        y="median_reported_harvest_kg",
                        title="Median reported harvest by crop",
                        y_label="Median harvest (kg)",
                    ),
                    width="stretch",
                )
            else:
                st.info("No crop group has enough reported harvest values for this chart.")

        if not provinces.empty:
            province_chart = provinces.sort_values("records", ascending=False)
            st.plotly_chart(
                _bar_chart(
                    province_chart,
                    x="province",
                    y="records",
                    title="Production records by province",
                    y_label="Production records",
                ),
                width="stretch",
            )

    with crop_tab:
        st.subheader("Reported loss patterns by crop")
        st.caption(
            "Values summarize crop groups across all seasons. Small source groups are pooled "
            "without their original labels. The reported-loss unit remains unconfirmed."
        )
        loss = crops.dropna(subset=["positive_reported_loss_share"]).copy()
        if not loss.empty:
            loss = loss.sort_values(
                "positive_reported_loss_share", ascending=False
            ).head(20)
            st.plotly_chart(
                _bar_chart(
                    loss,
                    x="crop",
                    y="positive_reported_loss_share",
                    title="Share of valid records with positive reported loss",
                    y_label="Positive reported-loss share",
                ),
                width="stretch",
            )
            display = loss[
                [
                    "crop",
                    "records",
                    "loss_reported_records",
                    "positive_reported_loss_share",
                    "median_reported_loss_value",
                ]
            ].rename(
                columns={
                    "crop": "Crop group",
                    "records": "Production records",
                    "loss_reported_records": "Valid reported-loss records",
                    "positive_reported_loss_share": "Positive reported-loss share",
                    "median_reported_loss_value": "Median reported value (unit unconfirmed)",
                }
            )
            display["Positive reported-loss share"] = display[
                "Positive reported-loss share"
            ].map(_percent)
            st.dataframe(display, hide_index=True, width="stretch")
        else:
            st.info("No crop group has enough valid loss responses for this chart.")
        st.caption("Missing loss responses are kept separate from zero values.")

    with model_tab:
        st.subheader("Exploratory reported-loss classifier")
        st.info(
            "The public aggregate edition does not include respondent-level model inputs or an "
            "interactive score. The retrospective classifier and its validation results remain "
            "available in the research materials; this hosted view does not score farmers."
        )

    with methods_tab:
        st.subheader("Data quality and analytical safeguards")
        quality_columns = [
            "season",
            "records",
            "distinct_crop_values",
            "loss_reported_records",
            "positive_reported_loss_records",
            "loss_missing_records",
        ]
        quality = seasons.loc[:, quality_columns].rename(
            columns={
                "season": "Season",
                "records": "Production records",
                "distinct_crop_values": "Distinct crop values",
                "loss_reported_records": "Loss values reported",
                "positive_reported_loss_records": "Positive reported-loss values",
                "loss_missing_records": "Missing loss values",
            }
        )
        st.dataframe(quality, hide_index=True, width="stretch")
        st.markdown(
            """
            **Interpretation and known limits**
            - These are unweighted sample descriptions, not province or national estimates.
            - Blank `s2q39` responses remain missing. Its unit is not confirmed in the available field label.
            - Season C has a restricted sample and is shown separately.
            - The published aggregates are independent summaries; they do not support combined season, province, and crop filtering.
            - Small crop and province groups are pooled. This rule does not replace the documented disclosure review.
            - Survey-weighted estimates, uncertainty intervals, causal claims, and intervention recommendations are outside this prototype.
            """
        )

    st.caption(
        "AgriLoss Rwanda · NISR SAS 2024 · Aggregate research prototype with explicit survey limitations"
    )
