from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


POOLED_CROP_LABEL = "Other or unreported crops (pooled)"
NST2_PRIORITY_CROPS = {
    "Maize",
    "Bush bean",
    "Climbing bean",
    "Irish potato",
    "Paddy rice",
    "Cassava",
    "Wheat",
    "Cooking banana",
    "Dessert banana",
    "Banana for beer",
}

STORAGE_LENSES = (
    "Crops with the highest share of positive loss reports",
    "Crops with the most positive loss reports",
    "Crops with the most missing loss answers",
)
VALUE_LENSES = (
    "Crops with the highest median harvest",
    "Crops with the most production records",
    "Crops with the most missing loss answers",
)


def _percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1%}"


def _kg(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.0f} kg"


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
    color: str = "#0f6b4e",
):
    figure = px.bar(
        frame,
        x=x,
        y=y,
        title=title,
        labels={x: "", y: y_label},
        hover_data=hover_data,
        color_discrete_sequence=[color],
    )
    if hover_data and percent_axis:
        figure.for_each_trace(
            lambda trace: trace.update(
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + f"{y_label}: %{{y:.1%}}"
                    + "<br>Valid answers: %{customdata[0]:,}"
                    + "<br>Positive answers: %{customdata[1]:,}"
                    + "<extra></extra>"
                )
            )
        )
    if percent_axis:
        figure.update_yaxes(tickformat=".0%")
    figure.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans 3, Segoe UI, sans-serif", color="#16332c"),
        title=dict(font=dict(size=16, color="#16332c")),
        margin=dict(l=12, r=12, t=58, b=12),
        xaxis_title=None,
        yaxis_title=None,
        xaxis_tickangle=x_angle,
        showlegend=False,
        bargap=0.28,
    )
    figure.update_traces(marker_line_width=0, hoverlabel=dict(namelength=-1))
    return figure


def _named_crops(crops: pd.DataFrame) -> pd.DataFrame:
    reviewable = crops[
        (crops["crop"].astype(str) != POOLED_CROP_LABEL)
        & crops["positive_reported_loss_share"].notna()
    ].copy()
    reviewable["loss_missing_share"] = (
        reviewable["loss_missing_records"] / reviewable["records"]
    )
    reviewable["is_priority_crop"] = reviewable["crop"].isin(NST2_PRIORITY_CROPS)
    return reviewable


def _crop_review_table(frame: pd.DataFrame, track: str) -> pd.DataFrame:
    display = frame.head(10)[
        [
            "crop",
            "is_priority_crop",
            "records",
            "loss_reported_records",
            "positive_reported_loss_records",
            "positive_reported_loss_share",
            "loss_missing_share",
            "median_reported_harvest_kg",
        ]
    ].rename(
        columns={
            "crop": "Crop",
            "is_priority_crop": "NST2 priority food crop",
            "records": "Survey records",
            "loss_reported_records": "Valid loss answers",
            "positive_reported_loss_records": "Positive loss answers",
            "positive_reported_loss_share": "Share of valid answers that are positive",
            "loss_missing_share": "Share of records with no loss answer",
            "median_reported_harvest_kg": "Median harvest reported (kg)",
        }
    )
    display["NST2 priority food crop"] = display["NST2 priority food crop"].map(
        lambda flag: "Yes" if flag else "—"
    )
    display["Share of valid answers that are positive"] = display[
        "Share of valid answers that are positive"
    ].map(_percent)
    display["Share of records with no loss answer"] = display[
        "Share of records with no loss answer"
    ].map(_percent)
    if track == "value":
        return display[
            [
                "Crop",
                "NST2 priority food crop",
                "Median harvest reported (kg)",
                "Survey records",
                "Valid loss answers",
                "Share of valid answers that are positive",
                "Share of records with no loss answer",
            ]
        ]
    return display


def _follow_up_brief(
    crop_row: pd.Series,
    review_lens: str,
    release_note: str,
    track: str,
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
        f"({int(crop_row['harvest_reported_records']):,} harvest answers)"
        if pd.notna(harvest_median)
        else "Not available in the released summary"
    )
    priority = (
        "Yes — this crop group is among NST2 priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas)."
        if crop_row["is_priority_crop"]
        else "Not listed as an NST2 priority food-crop group in this dashboard mapping."
    )
    track_title = (
        "Post-harvest collection and storage"
        if track == "storage"
        else "Processing and value addition"
    )
    if track == "storage":
        why = (
            f"Among named crop groups in this SAS 2024 sample, {crop_name} has "
            f"{positive_share} of valid reported-loss answers that are positive "
            f"({positive_records:,} of {valid_records:,}). "
            "That is a reason to verify collection, storage, and loss-stage questions for this crop. "
            "It is not a national post-harvest loss rate."
        )
        checks = """1. Confirm how the total reported-loss question (`s2q39`) is worded, coded, and skipped.
2. Review stored quantity (`s2q36`), facility (`s2q37`), public storage (`s2q38`), and storage-stage loss (`s2q47`) without treating blank as zero.
3. Keep loss-stage fields (`s2q41`–`s2q50`) separate until it is clear whether they overlap.
4. Reproduce any comparison with verified survey weights before using it in a plan.
5. Ask farmers, cooperatives, or agricultural planners whether a verified pattern is worth a storage or collection study."""
    else:
        why = (
            f"{crop_name} has a median reported harvest of {harvest_text} in this sample, "
            f"with {total_records:,} production records. "
            "That is a reason to review processing, sales, and market questions for this crop. "
            "It is not proof of processor demand, profit, or export opportunity."
        )
        checks = """1. Review transformed quantity and uses (`s2q25`, `s2q25_1`–`s2q25_3`) with their own valid counts.
2. Review quantity sold (`s2q26`), market (`s2q27`), and price (`s2q28`). Confirm zero prices that sit beside positive sales.
3. Compare harvest (`s2q21`) with stored quantity (`s2q36`) as context only — not as a processing yield.
4. Reproduce any comparison with verified survey weights before using it in a plan.
5. Ask processors, cooperatives, or planners whether a verified pattern supports a value-addition follow-up."""

    return f"""# AgriLoss follow-up brief: {crop_name}

## Challenge in focus
{track_title}

## Why this crop was selected
{why}

## Sample snapshot (unweighted SAS 2024 production records)
- Crop group: {crop_name}
- NST2 priority food crop: {priority}
- Production records: {total_records:,}
- Valid reported-loss answers: {valid_records:,}
- Positive reported-loss answers: {positive_records:,} ({positive_share} of valid answers)
- Missing reported-loss answers: {missing_records:,} ({missing_share} of records)
- Median reported harvest (`s2q21`): {harvest_text}
- Review lens: {review_lens}

## What to check next
{checks}

## What this brief is not
This is not a national estimate, a farmer ranking, a cause of loss, or a recommendation to build a store, mill, or factory. Season, province, and crop summaries in the public app cannot be combined.

Source: NISR Rwanda Seasonal Agricultural Survey 2024 production data, [NISR Microdata Portal](https://microdata.statistics.gov.rw/index.php/catalog/113).
Public dashboard status: {release_note}
National context: NST2 post-harvest loss target (13.8% to 4.8%) and PSTA 5 2023 study rates are separate published figures, not these sample shares.
"""


def _render_crop_review(
    review_queue: pd.DataFrame,
    reviewable_crops: pd.DataFrame,
    review_lens: str,
    release_note: str,
    track: str,
) -> None:
    st.markdown("##### Crops to look at first")
    st.dataframe(
        _crop_review_table(review_queue, track),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Small unnamed groups are pooled and hidden here. A crop needs at least 100 valid loss answers before a share is shown. "
        "NST2 priority is a label for national relevance, not a ranking from this survey."
    )

    default_crop = str(review_queue.iloc[0]["crop"])
    crop_options = sorted(reviewable_crops["crop"].astype(str).unique().tolist())
    selected_crop = st.selectbox(
        "Choose a crop to inspect",
        options=crop_options,
        index=crop_options.index(default_crop),
        help="The list starts with the crop at the top of your chosen sort. You can pick any named crop with a published summary.",
    )
    crop_row = reviewable_crops.loc[
        reviewable_crops["crop"].astype(str) == selected_crop
    ].iloc[0]

    if crop_row["is_priority_crop"]:
        st.success(
            f"{selected_crop} is mapped to NST2 priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas)."
        )

    crop_metrics = st.columns(4)
    if track == "storage":
        crop_metrics[0].metric(
            "Positive loss answers",
            f"{int(crop_row['positive_reported_loss_records']):,}",
            help="Count of valid s2q39 answers greater than zero in this crop group.",
        )
        crop_metrics[1].metric(
            "Share of valid answers",
            _percent(crop_row["positive_reported_loss_share"]),
            help="Positive answers divided by valid answers. This is not a national loss rate.",
        )
        crop_metrics[2].metric(
            "Valid loss answers",
            f"{int(crop_row['loss_reported_records']):,}",
        )
        crop_metrics[3].metric(
            "No loss answer",
            f"{_percent(crop_row['loss_missing_share'])}",
            help="Blank s2q39 answers as a share of all production records in this crop group.",
        )
    else:
        harvest_median = crop_row["median_reported_harvest_kg"]
        crop_metrics[0].metric(
            "Median harvest reported",
            _kg(harvest_median) if pd.notna(harvest_median) else "—",
            help="Median s2q21 in kilograms per production record. This is not crop yield.",
        )
        crop_metrics[1].metric(
            "Survey records",
            f"{int(crop_row['records']):,}",
        )
        crop_metrics[2].metric(
            "Positive loss share",
            _percent(crop_row["positive_reported_loss_share"]),
        )
        crop_metrics[3].metric(
            "No loss answer",
            f"{_percent(crop_row['loss_missing_share'])}",
        )

    if track == "storage":
        st.info(
            f"**In plain language:** {selected_crop} has "
            f"{_percent(crop_row['positive_reported_loss_share'])} of valid loss answers marked positive "
            f"in this sample. Use that as a prompt to check collection and storage questions — not as a "
            f"claim that this share of Rwanda’s harvest was lost."
        )
    else:
        st.info(
            f"**In plain language:** {selected_crop} shows a median reported harvest of "
            f"{_kg(crop_row['median_reported_harvest_kg'])} in this sample. Use that as a prompt to check "
            f"processing, sales, and storage questions — not as a business case for a factory."
        )

    st.markdown("##### What to do next")
    action_columns = st.columns(3)
    if track == "storage":
        action_columns[0].markdown(
            "**1. Check the loss question**\n\n"
            "Confirm the wording, unit, and skip pattern of the total reported-loss field before comparing crops."
        )
        action_columns[1].markdown(
            "**2. Open the storage fields**\n\n"
            "Look at stored quantity, facility type, public storage, and storage-stage loss separately."
        )
        action_columns[2].markdown(
            "**3. Ask people who use the data**\n\n"
            "A verified pattern is useful only if planners, cooperatives, or partners would act on it."
        )
    else:
        action_columns[0].markdown(
            "**1. Check processing and sales**\n\n"
            "Review transformed quantity, quantity sold, market, and price — each with its own valid count."
        )
        action_columns[1].markdown(
            "**2. Keep harvest as context**\n\n"
            "Median harvest is not yield, profit, or processor capacity. Do not convert it into a business plan."
        )
        action_columns[2].markdown(
            "**3. Ask people who use the data**\n\n"
            "A verified pattern is useful only if processors, cooperatives, or planners would act on it."
        )

    brief = _follow_up_brief(crop_row, review_lens, release_note, track)
    file_stub = "storage" if track == "storage" else "value-addition"
    st.download_button(
        "Download a one-page brief for this crop",
        data=brief,
        file_name=f"agriloss-{file_stub}-{selected_crop.lower().replace(' ', '-')}.md",
        mime="text/markdown",
        type="primary",
        help="Saves the sample snapshot, why the crop was selected, and the evidence checks still required.",
    )


def _render_start_tab(overall: dict[str, Any], crops: pd.DataFrame) -> None:
    st.markdown("### The challenge, in one page")
    st.write(
        "After harvest, food can be lost in collection, drying, storage, transport, processing, and sale. "
        "Rwanda’s **NST2** aims to cut food-crop post-harvest losses from **13.8% to 4.8%**, while raising "
        "productivity and expanding **agro-processing**. This tool does not measure those national targets. "
        "It helps a planner or researcher see **which crop groups in the NISR SAS 2024 sample** are worth "
        "checking first for storage and value-addition follow-up."
    )

    cards = st.columns(3)
    cards[0].markdown(
        """
        <div class="info-card">
          <h4>Who it is for</h4>
          <p>Agricultural planners, NISR and MINAGRI analysts, cooperatives, civil society, and development partners who need a transparent first look — not a farmer score.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cards[1].markdown(
        """
        <div class="info-card">
          <h4>What you can do</h4>
          <p>Pick storage or value addition, sort named crops with one clear rule, inspect harvest and reported-loss coverage, then download a follow-up brief.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cards[2].markdown(
        """
        <div class="info-card">
          <h4>What you should not do</h4>
          <p>Do not treat these shares as national loss rates, rank farmers, site a warehouse, or claim that an intervention works.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### How to use it")
    steps = st.columns(3)
    steps[0].markdown(
        """
        <div class="step-card"><span>1</span><div>
          <strong>Choose a track</strong>
          <p>Open the Crop workspace and select storage or processing.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
    steps[1].markdown(
        """
        <div class="step-card"><span>2</span><div>
          <strong>Sort with one rule</strong>
          <p>Use share, count, harvest, or missing answers — never a hidden score.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
    steps[2].markdown(
        """
        <div class="step-card"><span>3</span><div>
          <strong>Take the next check</strong>
          <p>Download the brief and verify the survey fields before planning use.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Why this matters for Rwanda")
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            **Vision 2050 and NST2** call for productive, market-oriented agriculture. NST2 names
            **post-harvest handling, market linkages, and agro-processing** as ways to reduce loss
            and raise the value of what farmers already grow. Priority food crops include maize,
            beans, potatoes, rice, cassava, wheat, and bananas.
            """
        )
        st.markdown(
            """
            **PSTA 5** cites a 2023 post-harvest study: **13.8% maize**, **12.4% rice**, and
            **11.3% beans** along those value chains. Those published study rates are shown here
            as national context. They are **not** calculated from the SAS 2024 sample in this app.
            """
        )
    with right:
        st.markdown(
            """
            **The SAS 2024 production questionnaire already asks** about stored quantity, public
            storage, transformed quantity, quantity sold, and stage-specific losses (harvest,
            transport, storage, processing, packaging, sales). This public edition publishes
            grouped harvest and reported-loss summaries so users can choose which crops to
            take back to those questions.
            """
        )
        st.caption(
            "Sources: [NST2 abridged](https://www.minecofin.gov.rw/fileadmin/user_upload/Minecofin/Publications/STRATEGIES/NST_2/NST2_2024-2029_Abridged.pdf) · "
            "[PSTA 5](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Fulltext__Final.pdf) · "
            "[NISR SAS 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113)"
        )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Production records in this sample", f"{overall['records']:,}")
    metric_columns[1].metric("Named crop groups with a published share", f"{len(_named_crops(crops)):,}")
    metric_columns[2].metric(
        "Positive loss answers (valid)",
        f"{int(overall['positive_reported_loss_records']):,} · {_percent(overall['positive_reported_loss_share'])}",
    )
    metric_columns[3].metric(
        "Median harvest reported",
        _kg(overall.get("median_reported_harvest_kg")),
    )
    st.caption(
        "These four numbers describe the released sample, not Rwanda’s harvest or national post-harvest loss. "
        "Blank loss answers are kept missing, not turned into zero."
    )

    with st.expander("Plain-language glossary"):
        st.markdown(
            """
            - **Production record:** one crop on one plot in the SAS 2024 production file. It is not a unique farmer.
            - **Valid loss answer:** a filled-in value for the total reported-loss question (`s2q39`). The unit is not confirmed, so we never call it kilograms.
            - **Positive loss answer:** a valid answer greater than zero. This is not loss severity.
            - **Missing answer:** a blank. Blanks stay blank.
            - **Median harvest:** the middle reported harvest (`s2q21`, in kg) among records in that group. It is not yield.
            - **Unweighted sample:** every record counts the same. Official SAS estimates use survey weights; this app does not.
            """
        )


def _render_workspace(
    crops: pd.DataFrame,
    release_note: str,
) -> None:
    st.markdown("### Crop workspace")
    st.write(
        "Start with the challenge you care about. The same crop table is sorted with a different rule so the first row is easier to discuss."
    )
    track_label = st.radio(
        "Challenge in focus",
        options=[
            "Post-harvest collection and storage",
            "Processing and value addition",
        ],
        horizontal=True,
        help="Storage uses reported-loss coverage. Value addition uses reported harvest size and sample coverage.",
    )
    track = "storage" if track_label.startswith("Post-harvest") else "value"

    if track == "storage":
        st.markdown(
            "Farmers and collectors need to know **where reported loss is concentrated in this sample**, "
            "and **where too many loss answers are missing**, before anyone designs a store, dryer, or collection point."
        )
        review_lens = st.selectbox("Sort crops by", options=list(STORAGE_LENSES))
        lens_notes = {
            STORAGE_LENSES[0]: "A high share can come from a small group. Always read it with the number of valid answers.",
            STORAGE_LENSES[1]: "A large count can simply mean the crop is common in the sample, not that it loses more.",
            STORAGE_LENSES[2]: "Missing answers need a look before you compare reported-loss patterns.",
        }
        sort_columns = {
            STORAGE_LENSES[0]: "positive_reported_loss_share",
            STORAGE_LENSES[1]: "positive_reported_loss_records",
            STORAGE_LENSES[2]: "loss_missing_share",
        }
    else:
        st.markdown(
            "Processors and market actors need to know **which crops already show substantial reported harvest in this sample**, "
            "so processing, sales, and storage questions can be checked — not so a mill is sited from this chart."
        )
        review_lens = st.selectbox("Sort crops by", options=list(VALUE_LENSES))
        lens_notes = {
            VALUE_LENSES[0]: "Median harvest is context, not yield, profit, or processor throughput.",
            VALUE_LENSES[1]: "Record counts follow how often the crop appears in the sample.",
            VALUE_LENSES[2]: "Missing loss answers can also limit later processing or storage analysis.",
        }
        sort_columns = {
            VALUE_LENSES[0]: "median_reported_harvest_kg",
            VALUE_LENSES[1]: "records",
            VALUE_LENSES[2]: "loss_missing_share",
        }

    st.caption(lens_notes[review_lens])
    reviewable_crops = _named_crops(crops)
    sort_column = sort_columns[review_lens]
    review_queue = reviewable_crops.sort_values(
        [sort_column, "loss_reported_records"],
        ascending=[False, False],
        na_position="last",
    )
    if review_queue.empty:
        st.info("No named crop groups have a releasable summary.")
        return
    _render_crop_review(
        review_queue,
        reviewable_crops,
        review_lens,
        release_note,
        track,
    )


def _render_explore_tab(
    seasons: pd.DataFrame,
    provinces: pd.DataFrame,
    crops: pd.DataFrame,
    selected_seasons: list[str],
    selected_provinces: list[str],
) -> None:
    st.markdown("### Look around the sample")
    st.caption(
        "Each chart is its own summary. Changing season or province does not change the crop table. Season C is a smaller, restricted sample."
    )
    left, right = st.columns(2)
    with left:
        season_view = seasons[seasons["season"].astype(str).isin(selected_seasons)].copy()
        if season_view.empty:
            st.info("Select at least one season in the sidebar.")
        else:
            st.plotly_chart(
                _bar_chart(
                    season_view,
                    x="season",
                    y="records",
                    title="How many production records are in each season?",
                    y_label="Production records",
                ),
                width="stretch",
            )
    with right:
        province_view = provinces[
            provinces["province"].astype(str).isin(selected_provinces)
        ].sort_values("records", ascending=False)
        if province_view.empty:
            st.info("Select at least one province in the sidebar.")
        else:
            st.plotly_chart(
                _bar_chart(
                    province_view,
                    x="province",
                    y="records",
                    title="Where are the released records from?",
                    y_label="Production records",
                    color="#c9862a",
                ),
                width="stretch",
            )

    named = _named_crops(crops)
    loss_crops = named.sort_values("positive_reported_loss_share", ascending=False).head(12)
    harvest_crops = named.sort_values("median_reported_harvest_kg", ascending=False).head(12)
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        if not loss_crops.empty:
            st.plotly_chart(
                _bar_chart(
                    loss_crops,
                    x="crop",
                    y="positive_reported_loss_share",
                    title="Storage track · positive loss answers (top 12)",
                    y_label="Share of valid loss answers",
                    hover_data=["loss_reported_records", "positive_reported_loss_records"],
                    x_angle=-32,
                    percent_axis=True,
                ),
                width="stretch",
            )
    with bottom_right:
        if not harvest_crops.empty:
            st.plotly_chart(
                _bar_chart(
                    harvest_crops,
                    x="crop",
                    y="median_reported_harvest_kg",
                    title="Value-addition track · median harvest (top 12)",
                    y_label="Median reported harvest (kg)",
                    x_angle=-32,
                    color="#2a7a9b",
                ),
                width="stretch",
            )
    st.caption(
        "Left: frequency of positive reported-loss answers, not kilograms lost. "
        "Right: median harvest in kg, not yield. Both pool seasons and provinces."
    )


def _render_methods_tab(
    seasons: pd.DataFrame,
    selected_seasons: list[str],
) -> None:
    st.markdown("### Data and methods")
    st.markdown(
        "**Primary data:** [NISR Rwanda Seasonal Agricultural Survey 2024 production module]"
        "(https://microdata.statistics.gov.rw/index.php/catalog/113). "
        "**Other public sources:** NST2 and PSTA 5, used only as policy context. "
        "The hosted app reads grouped totals only. It does not load farmer or plot rows."
    )
    quality_columns = [
        "season",
        "records",
        "distinct_crop_values",
        "loss_reported_records",
        "positive_reported_loss_records",
        "loss_missing_records",
    ]
    season_quality = seasons[seasons["season"].astype(str).isin(selected_seasons)]
    quality = season_quality.loc[:, quality_columns].rename(
        columns={
            "season": "Season",
            "records": "Production records",
            "distinct_crop_values": "Distinct crop values",
            "loss_reported_records": "Valid loss answers",
            "positive_reported_loss_records": "Positive answers",
            "loss_missing_records": "Missing loss answers",
        }
    )
    if quality.empty:
        st.info("Select at least one season in the sidebar.")
    else:
        st.dataframe(quality, hide_index=True, width="stretch")

    st.markdown("#### How numbers are built")
    st.markdown(
        """
        - Empty strings stay missing. They are never filled with zero.
        - A positive reported-loss share is positive `s2q39` values divided by valid `s2q39` values in that crop group.
        - The unit of `s2q39` is not confirmed in the published label, so it is never shown as kilograms.
        - Median harvest uses `s2q21` in kilograms. No harvested-area denominator is applied, so this is not yield.
        - Crop, season, and province tables are independent. They cannot be cross-filtered.
        - Groups with fewer than 100 records are pooled without their original names.
        - Survey weights, strata, and cluster variance are not applied.
        - Storage (`s2q36`–`s2q38`, `s2q47`) and processing/sales (`s2q25`–`s2q28`) remain the recommended next fields. They are not crop-ranked in this public file.
        - Season C is a restricted sample and should not be compared with A and B without survey-aware analysis.
        """
    )
    st.markdown("#### Innovation, used carefully")
    st.markdown(
        """
        The public tool is a **guided evidence workspace**: one-track sorting, response coverage,
        NST2 crop tagging, and a downloadable brief. A local research edition can train an
        exploratory classifier for a positive `s2q39` value. That model is retrospective, unweighted,
        and **not shown as a farmer score** in this hosted view.
        """
    )


def render_public_dashboard(payload: dict[str, Any]) -> None:
    """Render a two-track post-harvest and value-addition workspace from aggregates only."""
    overall = payload["overall"]
    seasons = pd.DataFrame(payload["by_season"])
    provinces = pd.DataFrame(payload["by_province"])
    crops = pd.DataFrame(payload["by_crop"])

    season_options = sorted(seasons["season"].astype(str).unique().tolist())
    province_options = sorted(provinces["province"].astype(str).unique().tolist())
    with st.sidebar:
        st.markdown("### AgriLoss Rwanda")
        st.caption("NISR 2026 hackathon · Track 1")
        st.markdown("**Post-harvest storage** and **value addition**, using SAS 2024 production summaries.")
        st.divider()
        st.markdown("#### Charts only")
        selected_seasons = st.multiselect(
            "Season",
            options=season_options,
            default=season_options,
            help="Changes the season chart and the methods table. It does not change the crop workspace.",
        )
        selected_provinces = st.multiselect(
            "Province",
            options=province_options,
            default=province_options,
            help="Changes the province chart only.",
        )
        st.caption("Season and province never filter the crop list. That keeps this public file from becoming a cross-tab of respondents.")
        st.divider()
        st.markdown(
            "[SAS 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113) · "
            "[NST2](https://www.minecofin.gov.rw/fileadmin/user_upload/Minecofin/Publications/STRATEGIES/NST_2/NST2_2024-2029_Abridged.pdf)"
        )

    if payload["release_status"] == "owner_authorized_unreviewed":
        review = payload["review"]
        release_note = "provisional; NISR disclosure review is not recorded."
        st.warning(
            "This public file is a **provisional grouped summary**. It is not an official NISR statistic "
            "and has not recorded NISR disclosure review."
        )
        st.caption(f"Review status: {review.get('status', 'required')}.")
    else:
        review = payload["review"]
        release_note = (
            f"approved; review recorded by {review['reviewed_by']} on "
            f"{review['reviewed_on']} (reference: {review['reference']})."
        )
        st.info(
            "These are unweighted sample descriptions, not population estimates for Rwanda."
        )
        st.caption(
            f"Disclosure review: {review['reviewed_by']} · {review['reviewed_on']} · "
            f"Reference: {review['reference']}"
        )

    start_tab, workspace_tab, explore_tab, methods_tab = st.tabs(
        [
            "Start here",
            "Crop workspace",
            "Explore the sample",
            "Data and methods",
        ]
    )
    with start_tab:
        _render_start_tab(overall, crops)
    with workspace_tab:
        _render_workspace(crops, release_note)
    with explore_tab:
        _render_explore_tab(
            seasons,
            provinces,
            crops,
            selected_seasons,
            selected_provinces,
        )
    with methods_tab:
        _render_methods_tab(seasons, selected_seasons)

    st.caption(
        "AgriLoss Rwanda · NISR SAS 2024 · Track 1: post-harvest collection and storage, processing and value addition · "
        "Research triage prototype — no national loss estimates or intervention effects"
    )
