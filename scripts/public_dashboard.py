from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


POOLED_CROP_LABEL = "Other or unreported crops (pooled)"


def _percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1%}"


def _bar_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    y_label: str,
    hover_data: list[str] | None = None,
    x_angle: int = 0,
    percent_axis: bool = False,
):
    figure = px.bar(
        frame,
        x=x,
        y=y,
        title=title,
        labels={x: "", y: y_label},
        hover_data=hover_data,
        color_discrete_sequence=["#16805d"],
    )
    if hover_data:
        figure.for_each_trace(
            lambda trace: trace.update(
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + f"{y_label}: %{{y:.1%}}"
                    + "<br>Valid responses: %{customdata[0]:,}"
                    + "<br>Positive responses: %{customdata[1]:,}"
                    + "<extra></extra>"
                )
            )
        )
    if percent_axis:
        figure.update_yaxes(tickformat=".0%")
    figure.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=58, b=12),
        xaxis_title=None,
        yaxis_title=None,
        xaxis_tickangle=x_angle,
        showlegend=False,
    )
    figure.update_traces(marker_line_width=0, hoverlabel=dict(namelength=-1))
    return figure


def _crop_review_table(frame: pd.DataFrame) -> pd.DataFrame:
    display = frame[
        [
            "crop",
            "records",
            "loss_reported_records",
            "positive_reported_loss_records",
            "positive_reported_loss_share",
            "loss_missing_share",
            "harvest_reported_records",
            "median_reported_harvest_kg",
        ]
    ].rename(
        columns={
            "crop": "Crop group",
            "records": "Production records in sample",
            "loss_reported_records": "Valid loss responses",
            "positive_reported_loss_records": "Positive reports",
            "positive_reported_loss_share": "Positive share of valid responses",
            "loss_missing_share": "Share missing",
            "harvest_reported_records": "Harvest responses",
            "median_reported_harvest_kg": "Median reported harvest (kg)",
        }
    )
    display["Positive share of valid responses"] = display[
        "Positive share of valid responses"
    ].map(_percent)
    display["Share missing"] = display["Share missing"].map(_percent)
    return display


def _follow_up_brief(
    crop_row: pd.Series,
    review_lens: str,
    release_note: str,
) -> str:
    crop_name = str(crop_row["crop"])
    positive_share = _percent(crop_row["positive_reported_loss_share"])
    total_records = int(crop_row["records"])
    valid_records = int(crop_row["loss_reported_records"])
    positive_records = int(crop_row["positive_reported_loss_records"])
    missing_records = int(crop_row["loss_missing_records"])
    missing_share = _percent(crop_row["loss_missing_share"])
    harvest_median = crop_row["median_reported_harvest_kg"]
    harvest_text = (
        f"{float(harvest_median):,.1f} kg per production record "
        f"(n={int(crop_row['harvest_reported_records']):,})"
        if pd.notna(harvest_median)
        else "Not available in the released summary"
    )

    return f"""# Crop follow-up brief: {crop_name}

## Purpose

This brief records a candidate question from the NISR SAS 2024 production sample. It is for research follow-up, not an estimate of national crop loss or a recommendation to farmers or planners.

## Observed sample summary

- Crop group: {crop_name}
- Production records in the released summary: {total_records:,}
- Valid reported-loss responses: {valid_records:,}
- Positive reported-loss responses: {positive_records:,}
- Positive responses among valid reports: {positive_share}
- Missing reported-loss responses: {missing_records:,} ({missing_share} of production records)
- Median reported harvest (`s2q21`): {harvest_text}
- Review lens used in the dashboard: {review_lens}

The share is calculated from valid responses to `s2q39`. Its unit and denominator are unconfirmed, and the summary is unweighted. It must not be described as a loss rate, loss quantity, or population estimate. The median harvest is context only; it is not a crop yield because no crop-specific harvested-area denominator is used here.

## Recommended evidence checks

1. Confirm the `s2q39` question wording, unit, skip logic, and response coding against NISR documentation.
2. Reproduce the crop summary with the verified plot weights, strata, cluster structure, and an appropriate variance method.
3. Check missingness and compare with the reported loss-stage fields (`s2q41`–`s2q50`) without summing stages until their overlap is understood.
4. Ask intended agricultural data users whether the validated result points to a useful follow-up study.

## Boundaries

This release contains independent crop, season, and province summaries. It cannot show this crop's joint pattern by season or province. No cause, intervention effect, farmer ranking, or productivity outcome is established.

Source: NISR Rwanda Seasonal Agricultural Survey 2024 production data, via the [NISR Microdata Portal](https://microdata.statistics.gov.rw/index.php/catalog/113). Public dashboard release status: {release_note}
"""


def _render_crop_review(
    review_queue: pd.DataFrame,
    reviewable_crops: pd.DataFrame,
    review_lens: str,
    release_note: str,
) -> None:
    st.markdown("#### Crop groups for review")
    st.dataframe(
        _crop_review_table(review_queue.head(10)),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "The pooled ‘Other or unreported crops’ category is excluded because its records cannot be attributed to a named crop. "
        "Groups with fewer than 100 valid loss responses have no published crop-level loss share."
    )

    default_crop = str(review_queue.iloc[0]["crop"])
    crop_options = sorted(reviewable_crops["crop"].astype(str).unique().tolist())
    selected_crop = st.selectbox(
        "Build a follow-up brief for a crop group",
        options=crop_options,
        index=crop_options.index(default_crop),
    )
    crop_row = reviewable_crops.loc[
        reviewable_crops["crop"].astype(str) == selected_crop
    ].iloc[0]

    st.markdown("### 2 · Review the selected crop group")
    crop_metrics = st.columns(5)
    crop_metrics[0].metric(
        "Positive share of valid responses",
        _percent(crop_row["positive_reported_loss_share"]),
    )
    crop_metrics[1].metric(
        "Positive responses",
        f"{int(crop_row['positive_reported_loss_records']):,}",
    )
    crop_metrics[2].metric(
        "Valid loss responses",
        f"{int(crop_row['loss_reported_records']):,}",
    )
    crop_metrics[3].metric(
        "Missing responses (% of records)",
        f"{int(crop_row['loss_missing_records']):,} · "
        f"{_percent(crop_row['loss_missing_share'])}",
    )
    harvest_median = crop_row["median_reported_harvest_kg"]
    crop_metrics[4].metric(
        "Median reported harvest",
        f"{float(harvest_median):,.1f} kg" if pd.notna(harvest_median) else "—",
        help=(
            f"Median `s2q21` per production record, based on "
            f"{int(crop_row['harvest_reported_records']):,} valid harvest responses. "
            "This is not a yield estimate because the crop-specific harvested-area denominator is not used."
            if pd.notna(harvest_median)
            else "No median is available in the released summary."
        ),
    )
    st.caption(
        "The crop summary pools seasons and provinces. `s2q39` is reported without a unit; its positive-response share is not a loss rate. Median harvest (`s2q21`) is context only, not crop yield."
    )

    st.markdown("### 3 · Turn the signal into a defensible next step")
    action_columns = st.columns(3)
    action_columns[0].markdown(
        "**Verify the measure**\n\n"
        "Confirm the `s2q39` unit, denominator, skip pattern, and response coding with the survey documentation."
    )
    action_columns[1].markdown(
        "**Re-estimate correctly**\n\n"
        "Use verified plot weights, strata, clusters, and a survey-appropriate variance method before making geographic or population comparisons."
    )
    action_columns[2].markdown(
        "**Validate the use**\n\n"
        "Review loss-stage fields and ask agricultural data users whether the validated result supports a worthwhile follow-up study."
    )

    brief = _follow_up_brief(crop_row, review_lens, release_note)
    st.download_button(
        "Download crop follow-up brief",
        data=brief,
        file_name="agriloss-crop-follow-up-brief.md",
        mime="text/markdown",
        help="Exports the selected crop summary, review lens, recommended evidence checks, and interpretation limits.",
    )


def render_public_dashboard(payload: dict[str, Any]) -> None:
    """Render a guided crop follow-up workflow from aggregate summaries only."""
    overall = payload["overall"]
    seasons = pd.DataFrame(payload["by_season"])
    provinces = pd.DataFrame(payload["by_province"])
    crops = pd.DataFrame(payload["by_crop"])

    season_options = sorted(seasons["season"].astype(str).unique().tolist())
    province_options = sorted(provinces["province"].astype(str).unique().tolist())
    with st.sidebar:
        st.markdown("## Explore the evidence")
        selected_seasons = st.multiselect(
            "Season summaries",
            options=season_options,
            default=season_options,
            help="Filters the season chart and season quality table only.",
        )
        selected_provinces = st.multiselect(
            "Province summaries",
            options=province_options,
            default=province_options,
            help="Filters the province record-count chart only.",
        )
        st.caption(
            "These are independent summaries. Season and province selections do not filter crop results."
        )

    review = payload["review"]
    if payload["release_status"] == "owner_authorized_unreviewed":
        release_note = "provisional; NISR disclosure review is not recorded."
        st.warning(
            "Provisional aggregate release: it was published before NISR disclosure review was recorded. "
            "It contains grouped summaries only and must not be interpreted as NISR-approved statistics."
        )
        st.caption("Disclosure review status: not recorded.")
    else:
        release_note = (
            f"approved; review recorded by {review['reviewed_by']} on "
            f"{review['reviewed_on']} (reference: {review['reference']})."
        )
        st.info(
            "This hosted view uses aggregate summaries only. Counts and percentages are unweighted sample descriptions, not population estimates."
        )
        st.caption(
            f"Disclosure review: {review['reviewed_by']} · {review['reviewed_on']} · "
            f"Reference: {review['reference']}"
        )

    workspace_tab, explore_tab, methods_tab = st.tabs(
        ["Follow-up workspace", "Explore patterns", "Data & methods"]
    )

    with workspace_tab:
        st.subheader("Find crop patterns that merit verification")
        st.markdown(
            "**Problem:** planners and researchers need a transparent way to decide which reported crop-loss patterns "
            "deserve a closer look. **Solution:** this workspace sorts grouped sample summaries using a review lens "
            "you choose, then creates a short evidence brief with the checks needed before the pattern informs planning."
        )
        st.caption(
            "The tool supports research triage only. It does not estimate national loss, explain causes, select interventions, or rank farmers."
        )
        st.info(
            "The public aggregate edition does not include respondent-level model inputs or an interactive score. "
            "This hosted view does not score or rank farmers."
        )

        metric_columns = st.columns(4)
        metric_columns[0].metric("Production records", f"{overall['records']:,}")
        metric_columns[1].metric("Valid loss responses", f"{overall['loss_reported_records']:,}")
        metric_columns[2].metric(
            "Positive reports (% of valid)",
            f"{int(overall['positive_reported_loss_records']):,} · "
            f"{_percent(overall['positive_reported_loss_share'])}",
        )
        metric_columns[3].metric(
            "Missing responses (% of records)",
            f"{int(overall['loss_missing_records']):,} · "
            f"{_percent(overall['loss_missing_records'] / overall['records'])}",
        )

        st.markdown("### 1 · Choose how to review the evidence")
        st.write(
            "The decision supported here is which crop-specific measurement to verify first. The review list "
            "shows named crop groups only and does not calculate a composite priority score; choose one transparent lens."
        )
        review_lens = st.selectbox(
            "Sort crop groups by",
            options=[
                "Highest positive-response share",
                "Most positive responses in the sample",
                "Highest missing-response share",
            ],
            help="Each option sorts a different descriptive measure. None is a national risk or impact ranking.",
        )

        reviewable_crops = crops[
            (crops["crop"].astype(str) != POOLED_CROP_LABEL)
            & crops["positive_reported_loss_share"].notna()
        ].copy()
        reviewable_crops["loss_missing_share"] = (
            reviewable_crops["loss_missing_records"]
            / reviewable_crops["records"]
        )
        sort_columns = {
            "Highest positive-response share": "positive_reported_loss_share",
            "Most positive responses in the sample": "positive_reported_loss_records",
            "Highest missing-response share": "loss_missing_share",
        }
        sort_column = sort_columns[review_lens]
        review_queue = reviewable_crops.sort_values(
            [sort_column, "loss_reported_records"], ascending=[False, False]
        )
        lens_notes = {
            "Highest positive-response share": "Shows the proportion of valid `s2q39` responses that are positive. A high share can be based on fewer records and does not measure severity.",
            "Most positive responses in the sample": "Shows the count of positive responses in these sample records. Counts are affected by how many records each crop group contains.",
            "Highest missing-response share": "Shows the proportion of production records in the crop group with a blank `s2q39` response. Review missingness before comparing reported-loss patterns.",
        }
        st.info(lens_notes[review_lens])

        if review_queue.empty:
            st.info("No named crop groups have a releasable reported-loss summary.")
        else:
            _render_crop_review(
                review_queue,
                reviewable_crops,
                review_lens,
                release_note,
            )

    with explore_tab:
        st.subheader("Explore the published sample summaries")
        st.caption(
            "Use these charts for context. Each chart is a separate one-dimensional summary; the filters do not create cross-tabulations."
        )
        left, right = st.columns(2)
        with left:
            season_view = seasons[
                seasons["season"].astype(str).isin(selected_seasons)
            ].copy()
            if not season_view.empty:
                st.plotly_chart(
                    _bar_chart(
                        season_view,
                        x="season",
                        y="records",
                        title="Production records by season",
                        y_label="Production records in sample",
                    ),
                    width="stretch",
                )
            else:
                st.info("Select at least one season summary in the sidebar.")
        with right:
            province_view = provinces[
                provinces["province"].astype(str).isin(selected_provinces)
            ].sort_values("records", ascending=False)
            if not province_view.empty:
                st.plotly_chart(
                    _bar_chart(
                        province_view,
                        x="province",
                        y="records",
                        title="Production records by province",
                        y_label="Production records in sample",
                    ),
                    width="stretch",
                )
            else:
                st.info("Select at least one province summary in the sidebar.")
        st.caption(
            "Province bars describe where released records occur, not provincial production or loss levels. Season C has a restricted sample and is shown separately."
        )

        chart_crops = crops[
            (crops["crop"].astype(str) != POOLED_CROP_LABEL)
            & crops["positive_reported_loss_share"].notna()
        ].sort_values("positive_reported_loss_share", ascending=False).head(15)
        if not chart_crops.empty:
            st.plotly_chart(
                _bar_chart(
                    chart_crops,
                    x="crop",
                    y="positive_reported_loss_share",
                    title="Positive reported-loss responses among valid reports · top 15 crop groups",
                    y_label="Share of valid s2q39 responses",
                    hover_data=["loss_reported_records", "positive_reported_loss_records"],
                    x_angle=-35,
                    percent_axis=True,
                ),
                width="stretch",
            )
            st.caption(
                "Crop groups are pooled across all seasons and provinces. The bar shows response frequency, not loss quantity, severity, or a national rate."
            )

    with methods_tab:
        st.subheader("How to interpret this dashboard")
        st.markdown(
            "**Source:** [NISR Rwanda Seasonal Agricultural Survey 2024 production data](https://microdata.statistics.gov.rw/index.php/catalog/113). "
            "The hosted dashboard reads a grouped aggregate file and does not load respondent-level records."
        )
        quality_columns = [
            "season",
            "records",
            "distinct_crop_values",
            "loss_reported_records",
            "positive_reported_loss_records",
            "loss_missing_records",
        ]
        season_quality = seasons[
            seasons["season"].astype(str).isin(selected_seasons)
        ]
        quality = season_quality.loc[:, quality_columns].rename(
            columns={
                "season": "Season",
                "records": "Production records",
                "distinct_crop_values": "Distinct crop values",
                "loss_reported_records": "Valid loss responses",
                "positive_reported_loss_records": "Positive responses",
                "loss_missing_records": "Missing loss responses",
            }
        )
        if quality.empty:
            st.info("Select at least one season summary in the sidebar.")
        else:
            st.dataframe(quality, hide_index=True, width="stretch")

        st.markdown("#### Indicators and boundaries")
        st.markdown(
            "- **Positive-response share:** positive `s2q39` values divided by valid `s2q39` responses in that crop group. The field's unit and denominator are unconfirmed; this is not a loss rate.\n"
            "- **Missing responses:** blank `s2q39` values remain separate from zero. Crop-level missingness is shown against all production records in the group.\n"
            "- **Counts:** rows are production records, not unique farmers, national production, or economic value.\n"
            "- **Harvest context:** median `s2q21` is reported in kilograms per production record. It is not crop yield because a crop-specific harvested-area denominator is not used.\n"
            "- **Pooling:** crop groups below the release threshold are pooled without their original labels; the pooled category is not included in the named-crop review list.\n"
            "- **Independent summaries:** season, province, and crop results cannot be combined or cross-filtered in this release.\n"
            "- **Survey design:** weights and design-based uncertainty are not applied. No causal effect, intervention recommendation, or farmer-level score is produced.\n"
            "- **Season C:** this season uses a restricted sample and must not be treated as directly comparable without survey-aware analysis."
        )
        st.info(
            "Before using a pattern in planning, confirm the indicator definition and data-use conditions with NISR, then reproduce it using the validated survey design and consult intended users."
        )

    st.caption(
        "AgriLoss Rwanda · NISR SAS 2024 · Research triage prototype · No national loss estimates or intervention effects"
    )
