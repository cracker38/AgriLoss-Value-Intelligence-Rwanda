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
    "Share of records with stored quantity (kg)",
    "Share of records with storage-stage loss (kg)",
    "Number of records with stored quantity",
    "Share missing a stored-quantity answer",
)
VALUE_LENSES = (
    "Share of records with transformed quantity (kg)",
    "Share of records with quantity sold (kg)",
    "Median reported harvest (kg)",
)


def _percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1%}"


def _kg(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.0f} kg"


def _int(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    return int(value)


def _bar_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    y_label: str,
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
        color_discrete_sequence=[color],
    )
    if percent_axis:
        figure.update_yaxes(tickformat=".0%")
        figure.update_traces(
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y:.1%}<extra></extra>"
        )
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
    reviewable = crops[crops["crop"].astype(str) != POOLED_CROP_LABEL].copy()
    published = (
        reviewable["stored_positive_share"].notna()
        | reviewable["transformed_positive_share"].notna()
        | reviewable["sold_positive_share"].notna()
        | reviewable["positive_reported_loss_share"].notna()
    )
    reviewable = reviewable.loc[published].copy()
    reviewable["stored_missing_share"] = (
        reviewable["stored_missing_records"] / reviewable["records"]
    )
    reviewable["is_priority_crop"] = reviewable["crop"].isin(NST2_PRIORITY_CROPS)
    return reviewable


def _crop_review_table(frame: pd.DataFrame, track: str) -> pd.DataFrame:
    if track == "storage":
        display = frame.head(10)[
            [
                "crop",
                "is_priority_crop",
                "records",
                "stored_positive_records",
                "stored_positive_share",
                "stored_median_positive_kg",
                "storage_loss_positive_records",
                "storage_loss_positive_share",
                "storage_loss_negative_records",
            ]
        ].rename(
            columns={
                "crop": "Crop",
                "is_priority_crop": "NST2 priority",
                "records": "Survey records",
                "stored_positive_records": "Stored quantity > 0",
                "stored_positive_share": "Share stored (valid s2q36)",
                "stored_median_positive_kg": "Median stored kg (when > 0)",
                "storage_loss_positive_records": "Storage-stage loss > 0",
                "storage_loss_positive_share": "Share storage-stage loss (valid s2q47)",
                "storage_loss_negative_records": "Negative s2q47 values",
            }
        )
        display["Share stored (valid s2q36)"] = display["Share stored (valid s2q36)"].map(_percent)
        display["Share storage-stage loss (valid s2q47)"] = display[
            "Share storage-stage loss (valid s2q47)"
        ].map(_percent)
    else:
        display = frame.head(10)[
            [
                "crop",
                "is_priority_crop",
                "records",
                "transformed_positive_records",
                "transformed_positive_share",
                "transformed_median_positive_kg",
                "sold_positive_records",
                "sold_positive_share",
                "sold_median_positive_kg",
                "median_reported_harvest_kg",
            ]
        ].rename(
            columns={
                "crop": "Crop",
                "is_priority_crop": "NST2 priority",
                "records": "Survey records",
                "transformed_positive_records": "Transformed > 0",
                "transformed_positive_share": "Share transformed (valid s2q25)",
                "transformed_median_positive_kg": "Median transformed kg (when > 0)",
                "sold_positive_records": "Sold > 0",
                "sold_positive_share": "Share sold (valid s2q26)",
                "sold_median_positive_kg": "Median sold kg (when > 0)",
                "median_reported_harvest_kg": "Median harvest kg",
            }
        )
        display["Share transformed (valid s2q25)"] = display[
            "Share transformed (valid s2q25)"
        ].map(_percent)
        display["Share sold (valid s2q26)"] = display["Share sold (valid s2q26)"].map(_percent)
    display["NST2 priority"] = display["NST2 priority"].map(lambda flag: "Yes" if flag else "—")
    return display


def _storage_reading(crop_row: pd.Series) -> str:
    crop = str(crop_row["crop"])
    stored_share = crop_row["stored_positive_share"]
    stored_n = _int(crop_row["stored_positive_records"])
    stored_valid = _int(crop_row["stored_reported_records"])
    loss_share = crop_row["storage_loss_positive_share"]
    loss_n = _int(crop_row["storage_loss_positive_records"])
    negatives = _int(crop_row["storage_loss_negative_records"])
    public_n = _int(crop_row["public_stored_positive_records"])
    parts = [
        f"In this unweighted SAS 2024 sample, {crop} has {_percent(stored_share)} of valid stored-quantity answers "
        f"greater than zero ({stored_n:,} of {stored_valid:,}). Median stored quantity among those positive answers is "
        f"{_kg(crop_row['stored_median_positive_kg'])}."
    ]
    parts.append(
        f"Storage-stage loss (`s2q47`, kg) is positive in {_percent(loss_share)} of valid answers "
        f"({loss_n:,} records). {negatives:,} records have a negative storage-stage quantity; those are kept as a quality flag, not clipped."
    )
    if public_n:
        parts.append(
            f"{public_n:,} records report public-storage quantity greater than zero. That count is small and is not a warehouse siting result."
        )
    if pd.notna(stored_share) and stored_share == 0 and pd.notna(loss_share) and loss_share > 0:
        parts.append(
            "Stored quantity is not reported as positive in this group, but storage-stage loss is. "
            "That skip-pattern should be checked in the questionnaire before anyone infers a storage gap."
        )
    parts.append(
        "These shares describe production records in the sample. They are not Rwanda’s national post-harvest loss rate."
    )
    return " ".join(parts)


def _value_reading(crop_row: pd.Series) -> str:
    crop = str(crop_row["crop"])
    trans_share = crop_row["transformed_positive_share"]
    sold_share = crop_row["sold_positive_share"]
    trans_n = _int(crop_row["transformed_positive_records"])
    sold_n = _int(crop_row["sold_positive_records"])
    zero_price = _int(crop_row["sold_with_zero_price_records"])
    pos_price = _int(crop_row["sold_with_positive_price_records"])
    parts = [
        f"In this unweighted SAS 2024 sample, {crop} has {_percent(trans_share)} of valid transformed-quantity answers "
        f"greater than zero ({trans_n:,} records). Median transformed quantity among those positive answers is "
        f"{_kg(crop_row['transformed_median_positive_kg'])}."
    ]
    parts.append(
        f"{_percent(sold_share)} of valid sold-quantity answers are greater than zero ({sold_n:,} records). "
        f"Median sold quantity among those positive answers is {_kg(crop_row['sold_median_positive_kg'])}."
    )
    parts.append(
        f"Among records with sold quantity > 0, {pos_price:,} also report a positive price (RWF/kg) and "
        f"{zero_price:,} report a zero price. Zero prices next to positive sales need a coding check before any value calculation."
    )
    parts.append(
        f"Median reported harvest is {_kg(crop_row['median_reported_harvest_kg'])} per production record. That is not yield, profit, or processor demand."
    )
    return " ".join(parts)


def _follow_up_brief(
    crop_row: pd.Series,
    review_lens: str,
    release_note: str,
    track: str,
) -> str:
    crop_name = str(crop_row["crop"])
    priority = (
        "Yes — mapped to NST2 priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas)."
        if crop_row["is_priority_crop"]
        else "Not listed as an NST2 priority food-crop group in this dashboard mapping."
    )
    if track == "storage":
        why = _storage_reading(crop_row)
        checks = """1. Confirm skip logic between harvest (`s2q21`), stored quantity (`s2q36`), facility (`s2q37`), and public storage (`s2q38`).
2. Investigate negative and zero storage-stage loss values (`s2q47`) without clipping them.
3. Keep stage losses (`s2q41`–`s2q50`) separate; do not add them to `s2q39`.
4. Reproduce any comparison with verified survey weights before using it in a plan.
5. Ask farmers, cooperatives, or planners whether the verified storage pattern is worth a collection or storage study."""
        track_title = "Post-harvest collection and storage"
    else:
        why = _value_reading(crop_row)
        checks = """1. Review transformed quantity and uses (`s2q25`, `s2q25_1`–`s2q25_3`) with their own valid counts.
2. Review quantity sold (`s2q26`), market (`s2q27`), and price (`s2q28`). Confirm zero prices beside positive sales.
3. Do not treat transformed or sold kilograms as processor yield, capacity, or profit.
4. Reproduce any comparison with verified survey weights before using it in a plan.
5. Ask processors, cooperatives, or planners whether the verified pattern supports a value-addition follow-up."""
        track_title = "Processing and value addition"

    return f"""# AgriLoss follow-up brief: {crop_name}

## Challenge in focus
{track_title}

## What the SAS 2024 sample shows
{why}

## Sample snapshot (unweighted production records)
- Crop group: {crop_name}
- NST2 priority food crop: {priority}
- Production records: {_int(crop_row['records']):,}
- Stored quantity > 0 (`s2q36`, kg): {_int(crop_row['stored_positive_records']):,} · {_percent(crop_row['stored_positive_share'])} of valid answers · median when > 0: {_kg(crop_row['stored_median_positive_kg'])}
- Storage-stage loss > 0 (`s2q47`, kg): {_int(crop_row['storage_loss_positive_records']):,} · {_percent(crop_row['storage_loss_positive_share'])} of valid answers · negative values: {_int(crop_row['storage_loss_negative_records']):,}
- Transformed quantity > 0 (`s2q25`, kg): {_int(crop_row['transformed_positive_records']):,} · {_percent(crop_row['transformed_positive_share'])} of valid answers · median when > 0: {_kg(crop_row['transformed_median_positive_kg'])}
- Quantity sold > 0 (`s2q26`, kg): {_int(crop_row['sold_positive_records']):,} · {_percent(crop_row['sold_positive_share'])} of valid answers · median when > 0: {_kg(crop_row['sold_median_positive_kg'])}
- Median harvest (`s2q21`, kg): {_kg(crop_row['median_reported_harvest_kg'])}
- Positive total reported-loss answers (`s2q39`, unit unconfirmed): {_int(crop_row['positive_reported_loss_records']):,} · {_percent(crop_row['positive_reported_loss_share'])} of valid answers
- Review lens: {review_lens}

## What to check next
{checks}

## What this brief is not
This is not a national estimate, a farmer ranking, a cause of loss, or a recommendation to build a store, mill, or factory. Season, province, and crop summaries cannot be combined in this public file.

Source: NISR Rwanda Seasonal Agricultural Survey 2024 production data, [NISR Microdata Portal](https://microdata.statistics.gov.rw/index.php/catalog/113).
Public dashboard status: {release_note}
"""


def _render_crop_review(
    review_queue: pd.DataFrame,
    reviewable_crops: pd.DataFrame,
    review_lens: str,
    release_note: str,
    track: str,
) -> None:
    st.markdown("##### Crops from the SAS 2024 sample")
    st.dataframe(
        _crop_review_table(review_queue, track),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "These are grouped SAS 2024 production records, not mock data. A share is published only when the crop group has at least 100 valid answers. "
        "NST2 priority is a policy label, not a survey ranking."
    )

    default_crop = str(review_queue.iloc[0]["crop"])
    crop_options = sorted(reviewable_crops["crop"].astype(str).unique().tolist())
    selected_crop = st.selectbox(
        "Choose a crop to inspect",
        options=crop_options,
        index=crop_options.index(default_crop),
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
        crop_metrics[0].metric("Stored quantity > 0", f"{_int(crop_row['stored_positive_records']):,}")
        crop_metrics[1].metric("Share of valid stored answers", _percent(crop_row["stored_positive_share"]))
        crop_metrics[2].metric(
            "Median stored (when > 0)",
            _kg(crop_row["stored_median_positive_kg"]),
        )
        crop_metrics[3].metric(
            "Storage-stage loss > 0",
            f"{_int(crop_row['storage_loss_positive_records']):,} · {_percent(crop_row['storage_loss_positive_share'])}",
        )
        st.info(_storage_reading(crop_row))
        actions = (
            "**1. Check stored quantity**\n\nConfirm `s2q36` skip logic and keep blanks missing.",
            "**2. Check storage-stage loss**\n\nReview `s2q47` positives and the negative-value flag separately.",
            "**3. Check facility type**\n\n`s2q37` is mostly own storage in this sample; unmapped codes 12–14 stay unmapped.",
        )
    else:
        crop_metrics[0].metric("Transformed > 0", f"{_int(crop_row['transformed_positive_records']):,}")
        crop_metrics[1].metric("Share transformed", _percent(crop_row["transformed_positive_share"]))
        crop_metrics[2].metric("Sold > 0", f"{_int(crop_row['sold_positive_records']):,}")
        crop_metrics[3].metric("Share sold", _percent(crop_row["sold_positive_share"]))
        st.info(_value_reading(crop_row))
        actions = (
            "**1. Check transformation**\n\n`s2q25` is kilograms already processed or used, not factory capacity.",
            "**2. Check sales and price**\n\nKeep zero prices beside positive `s2q26` sales visible.",
            "**3. Keep harvest as context**\n\nMedian `s2q21` is not yield or a business case.",
        )

    st.markdown("##### What to do next")
    for column, text in zip(st.columns(3), actions):
        column.markdown(text)

    brief = _follow_up_brief(crop_row, review_lens, release_note, track)
    file_stub = "storage" if track == "storage" else "value-addition"
    st.download_button(
        "Download a one-page brief for this crop",
        data=brief,
        file_name=f"agriloss-{file_stub}-{selected_crop.lower().replace(' ', '-')}.md",
        mime="text/markdown",
        type="primary",
    )


def _render_start_tab(
    overall: dict[str, Any],
    crops: pd.DataFrame,
    facilities: list[dict[str, Any]],
) -> None:
    st.markdown("### The challenge, in one page")
    st.write(
        "After harvest, crops are stored, processed, or sold. Rwanda’s **NST2** aims to cut food-crop post-harvest losses "
        "from **13.8% to 4.8%** and to expand agro-processing. This dashboard does not measure those national targets. "
        "It shows **what the NISR SAS 2024 production sample actually recorded** for stored quantity, storage-stage loss, "
        "transformed quantity, and quantity sold."
    )

    cards = st.columns(3)
    cards[0].markdown(
        """
        <div class="info-card"><h4>Who it is for</h4>
        <p>Planners, NISR and MINAGRI analysts, cooperatives, and partners who need a first look at real survey patterns — not a farmer score.</p></div>
        """,
        unsafe_allow_html=True,
    )
    cards[1].markdown(
        """
        <div class="info-card"><h4>What you can do</h4>
        <p>Compare named crops on stored kilograms, storage-stage loss, household processing, and sales, then download a brief.</p></div>
        """,
        unsafe_allow_html=True,
    )
    cards[2].markdown(
        """
        <div class="info-card"><h4>What you should not do</h4>
        <p>Do not treat sample shares as NST2 rates, rank farmers, or site a warehouse or factory from this screen.</p></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### What SAS 2024 recorded in this sample")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Production records", f"{overall['records']:,}")
    metric_columns[1].metric(
        "Stored quantity > 0",
        f"{_int(overall['stored_positive_records']):,} · {_percent(overall['stored_positive_share'])}",
        help="Valid s2q36 answers greater than zero. Unit is kilograms.",
    )
    metric_columns[2].metric(
        "Transformed quantity > 0",
        f"{_int(overall['transformed_positive_records']):,} · {_percent(overall['transformed_positive_share'])}",
        help="Valid s2q25 answers greater than zero. Unit is kilograms.",
    )
    metric_columns[3].metric(
        "Quantity sold > 0",
        f"{_int(overall['sold_positive_records']):,} · {_percent(overall['sold_positive_share'])}",
        help="Valid s2q26 answers greater than zero. Unit is kilograms.",
    )
    extra = st.columns(4)
    extra[0].metric(
        "Storage-stage loss > 0",
        f"{_int(overall['storage_loss_positive_records']):,} · {_percent(overall.get('storage_loss_positive_share'))}",
        help="Valid s2q47 answers greater than zero, in kilograms. Negative values are counted separately.",
    )
    extra[1].metric(
        "Negative storage-stage values",
        f"{_int(overall.get('storage_loss_negative_records')):,}",
        help="Kept as a quality flag. NISR metadata also includes negative minima.",
    )
    extra[2].metric(
        "Public-storage quantity > 0",
        f"{_int(overall['public_stored_positive_records']):,}",
        help="s2q38 in kilograms. Rare in this sample.",
    )
    extra[3].metric(
        "Median harvest reported",
        _kg(overall.get("median_reported_harvest_kg")),
        help="Median s2q21 in kilograms per production record. Not yield.",
    )
    st.caption(
        "All figures are unweighted SAS 2024 production records. Blanks stay missing. "
        "NST2’s 13.8% to 4.8% target and PSTA 5’s 2023 study rates are separate published numbers, not these sample shares."
    )

    if facilities:
        st.markdown("##### Reported storage facility (`s2q37`)")
        facility_frame = pd.DataFrame(facilities).rename(
            columns={"facility": "Facility response", "records": "Production records"}
        )
        st.dataframe(facility_frame, hide_index=True, width="stretch")
        st.caption(
            "Handbook codes are own, public, cooperative/private, and other. Values 12, 13, and 14 are left as unmapped. "
            "Most production records have no facility answer, including many with stored quantity of zero."
        )

    st.markdown("### How to use it")
    steps = st.columns(3)
    steps[0].markdown(
        '<div class="step-card"><span>1</span><div><strong>Choose a track</strong><p>Storage uses s2q36 and s2q47. Value addition uses s2q25 and s2q26.</p></div></div>',
        unsafe_allow_html=True,
    )
    steps[1].markdown(
        '<div class="step-card"><span>2</span><div><strong>Sort with one rule</strong><p>Each sort is one survey field. Nothing is combined into a hidden score.</p></div></div>',
        unsafe_allow_html=True,
    )
    steps[2].markdown(
        '<div class="step-card"><span>3</span><div><strong>Read coverage</strong><p>A high share with few valid answers is not a national priority list.</p></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Why this matters for Rwanda")
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            **Vision 2050 and NST2** call for productive, market-oriented agriculture, including post-harvest handling
            and agro-processing. Priority food crops include maize, beans, potatoes, rice, cassava, wheat, and bananas.
            """
        )
        st.markdown(
            """
            **PSTA 5** cites a 2023 study: 13.8% maize, 12.4% rice, and 11.3% beans along those value chains.
            Those study rates are **not** calculated from this SAS sample.
            """
        )
    with right:
        named = _named_crops(crops)
        maize = named.loc[named["crop"] == "Maize"]
        beans = named.loc[named["crop"] == "Bush bean"]
        beer = named.loc[named["crop"] == "Banana for beer"]
        bullets = []
        if not maize.empty:
            bullets.append(
                f"**Maize:** {_percent(maize.iloc[0]['stored_positive_share'])} of valid stored-quantity answers are > 0, "
                f"and {_percent(maize.iloc[0]['transformed_positive_share'])} of valid transformed-quantity answers are > 0."
            )
        if not beans.empty:
            bullets.append(
                f"**Bush bean:** {_percent(beans.iloc[0]['stored_positive_share'])} stored and "
                f"{_percent(beans.iloc[0]['sold_positive_share'])} sold, among valid answers."
            )
        if not beer.empty:
            bullets.append(
                f"**Banana for beer:** {_percent(beer.iloc[0]['transformed_positive_share'])} transformed and "
                f"{_percent(beer.iloc[0]['sold_positive_share'])} sold; stored quantity > 0 is "
                f"{_percent(beer.iloc[0]['stored_positive_share'])}."
            )
        st.markdown("\n\n".join(f"- {item}" for item in bullets) or "Crop summaries will appear once the aggregate file includes storage and processing fields.")
        st.caption(
            "Sources: [NST2 abridged](https://www.minecofin.gov.rw/fileadmin/user_upload/Minecofin/Publications/STRATEGIES/NST_2/NST2_2024-2029_Abridged.pdf) · "
            "[PSTA 5](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Fulltext__Final.pdf) · "
            "[NISR SAS 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113)"
        )

    with st.expander("Plain-language glossary"):
        st.markdown(
            """
            - **Production record:** one crop on one plot in SAS 2024. It is not a unique farmer.
            - **Stored quantity (`s2q36`):** kilograms reported as stored. Zero is zero; blank is missing.
            - **Storage-stage loss (`s2q47`):** kilograms reported lost at the storage stage. Negative values are flagged.
            - **Transformed quantity (`s2q25`):** kilograms already processed or used. Not factory throughput.
            - **Quantity sold (`s2q26`):** kilograms sold. Price (`s2q28`) is RWF/kg and is often missing.
            - **Total reported loss (`s2q39`):** shown without a unit because the published label does not confirm one.
            - **Unweighted sample:** every record counts equally. Official SAS estimates use survey weights.
            """
        )


def _render_workspace(crops: pd.DataFrame, release_note: str) -> None:
    st.markdown("### Crop workspace")
    st.write(
        "Choose the Track 1 challenge. Sorting uses the real SAS 2024 field for that challenge — stored kilograms, storage-stage loss, transformed kilograms, or quantity sold."
    )
    track_label = st.radio(
        "Challenge in focus",
        options=[
            "Post-harvest collection and storage",
            "Processing and value addition",
        ],
        horizontal=True,
    )
    track = "storage" if track_label.startswith("Post-harvest") else "value"

    if track == "storage":
        st.markdown(
            "Storage follow-up uses **stored quantity (`s2q36`, kg)** and **storage-stage loss (`s2q47`, kg)**. "
            "Total reported loss (`s2q39`) is shown as context only because its unit is unconfirmed."
        )
        review_lens = st.selectbox("Sort crops by", options=list(STORAGE_LENSES))
        lens_notes = {
            STORAGE_LENSES[0]: "Share of valid s2q36 answers that are greater than zero. A high share can still be a small group.",
            STORAGE_LENSES[1]: "Share of valid s2q47 answers that are greater than zero. This is not total post-harvest loss.",
            STORAGE_LENSES[2]: "Count of records with stored quantity > 0. Common crops can dominate counts.",
            STORAGE_LENSES[3]: "Blank stored-quantity answers as a share of production records in the crop group.",
        }
        sort_columns = {
            STORAGE_LENSES[0]: "stored_positive_share",
            STORAGE_LENSES[1]: "storage_loss_positive_share",
            STORAGE_LENSES[2]: "stored_positive_records",
            STORAGE_LENSES[3]: "stored_missing_share",
        }
    else:
        st.markdown(
            "Value-addition follow-up uses **transformed quantity (`s2q25`, kg)** and **quantity sold (`s2q26`, kg)**. "
            "Harvest is context, not a mill-siting input."
        )
        review_lens = st.selectbox("Sort crops by", options=list(VALUE_LENSES))
        lens_notes = {
            VALUE_LENSES[0]: "Share of valid s2q25 answers greater than zero — household processing/use, not factory output.",
            VALUE_LENSES[1]: "Share of valid s2q26 answers greater than zero — market participation in this sample.",
            VALUE_LENSES[2]: "Median s2q21 in kilograms per production record. Not yield or profit.",
        }
        sort_columns = {
            VALUE_LENSES[0]: "transformed_positive_share",
            VALUE_LENSES[1]: "sold_positive_share",
            VALUE_LENSES[2]: "median_reported_harvest_kg",
        }

    st.caption(lens_notes[review_lens])
    reviewable_crops = _named_crops(crops)
    review_queue = reviewable_crops.sort_values(
        [sort_columns[review_lens], "records"],
        ascending=[False, False],
        na_position="last",
    )
    if review_queue.empty:
        st.info("No named crop groups have a releasable summary.")
        return
    _render_crop_review(review_queue, reviewable_crops, review_lens, release_note, track)


def _render_explore_tab(
    seasons: pd.DataFrame,
    provinces: pd.DataFrame,
    crops: pd.DataFrame,
    selected_seasons: list[str],
    selected_provinces: list[str],
) -> None:
    st.markdown("### Look around the sample")
    st.caption(
        "Each chart is its own SAS 2024 summary. Changing season or province does not change the crop table."
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
                    title="Production records by season",
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
            y_column = (
                "stored_positive_share"
                if "stored_positive_share" in province_view.columns
                else "records"
            )
            st.plotly_chart(
                _bar_chart(
                    province_view,
                    x="province",
                    y=y_column,
                    title="Stored quantity > 0 by province"
                    if y_column == "stored_positive_share"
                    else "Production records by province",
                    y_label="Share of valid stored answers"
                    if y_column == "stored_positive_share"
                    else "Production records",
                    percent_axis=y_column == "stored_positive_share",
                    color="#c9862a",
                ),
                width="stretch",
            )

    named = _named_crops(crops)
    stored = named.sort_values("stored_positive_share", ascending=False).head(12)
    transformed = named.sort_values("transformed_positive_share", ascending=False).head(12)
    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        if not stored.empty:
            st.plotly_chart(
                _bar_chart(
                    stored,
                    x="crop",
                    y="stored_positive_share",
                    title="Storage · share with stored quantity > 0",
                    y_label="Share of valid s2q36 answers",
                    x_angle=-32,
                    percent_axis=True,
                ),
                width="stretch",
            )
    with bottom_right:
        if not transformed.empty:
            st.plotly_chart(
                _bar_chart(
                    transformed,
                    x="crop",
                    y="transformed_positive_share",
                    title="Value addition · share transformed > 0",
                    y_label="Share of valid s2q25 answers",
                    x_angle=-32,
                    percent_axis=True,
                    color="#2a7a9b",
                ),
                width="stretch",
            )
    st.caption(
        "Left: household stored kilograms. Right: transformed kilograms. Neither chart is a national loss rate or a factory forecast."
    )


def _render_methods_tab(seasons: pd.DataFrame, selected_seasons: list[str]) -> None:
    st.markdown("### Data and methods")
    st.markdown(
        "**Primary data:** [NISR Rwanda Seasonal Agricultural Survey 2024 production module]"
        "(https://microdata.statistics.gov.rw/index.php/catalog/113). "
        "The hosted app reads grouped totals only. It does not load farmer or plot rows."
    )
    quality_columns = [
        column
        for column in (
            "season",
            "records",
            "stored_positive_records",
            "stored_positive_share",
            "storage_loss_positive_records",
            "storage_loss_negative_records",
            "transformed_positive_records",
            "transformed_positive_share",
            "sold_positive_records",
            "sold_positive_share",
        )
        if column in seasons.columns
    ]
    season_quality = seasons[seasons["season"].astype(str).isin(selected_seasons)]
    if season_quality.empty or not quality_columns:
        st.info("Select at least one season in the sidebar.")
    else:
        display = season_quality.loc[:, quality_columns].copy()
        for column in display.columns:
            if column.endswith("_share"):
                display[column] = display[column].map(_percent)
        st.dataframe(display, hide_index=True, width="stretch")

    st.markdown("#### How numbers are built")
    st.markdown(
        """
        - Empty strings stay missing. They are never filled with zero.
        - A “positive share” is values > 0 divided by valid answers for that field in the crop group.
        - Median kilograms for stored, transformed, sold, and storage-stage loss are medians **among positive values**, so zeros do not pull them to zero.
        - Median harvest uses all valid `s2q21` values, including zeros if any.
        - `s2q36`, `s2q38`, `s2q25`, `s2q26`, and `s2q47` are labelled in kilograms. `s2q39` is not.
        - Negative `s2q47` values are counted and not clipped.
        - Facility codes 12, 13, and 14 are not mapped to a storage type.
        - Crop, season, and province tables are independent. They cannot be cross-filtered.
        - Groups with fewer than 100 records are pooled without their original names.
        - Survey weights are not applied.
        - Season C is a restricted sample.
        """
    )


def render_public_dashboard(payload: dict[str, Any]) -> None:
    """Render storage and value-addition summaries from SAS 2024 aggregates only."""
    overall = payload["overall"]
    seasons = pd.DataFrame(payload["by_season"])
    provinces = pd.DataFrame(payload["by_province"])
    crops = pd.DataFrame(payload["by_crop"])
    facilities = payload.get("by_storage_facility") or []

    season_options = sorted(seasons["season"].astype(str).unique().tolist())
    province_options = sorted(provinces["province"].astype(str).unique().tolist())
    with st.sidebar:
        st.markdown("### AgriLoss Rwanda")
        st.caption("NISR 2026 hackathon · Track 1")
        st.markdown("Real SAS 2024 production summaries for **storage** and **value addition**.")
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
        st.caption("Season and province never filter the crop list.")
        st.divider()
        st.markdown(
            "[SAS 2024 catalog](https://microdata.statistics.gov.rw/index.php/catalog/113)"
        )

    if payload["release_status"] == "owner_authorized_unreviewed":
        review = payload["review"]
        release_note = "provisional; NISR disclosure review is not recorded."
        st.warning(
            "This public file is a **provisional grouped summary of real SAS 2024 production records**. "
            "It is not an official NISR statistic."
        )
        st.caption(f"Review status: {review.get('status', 'required')}.")
    else:
        review = payload["review"]
        release_note = (
            f"approved; review recorded by {review['reviewed_by']} on "
            f"{review['reviewed_on']} (reference: {review['reference']})."
        )
        st.info("These are unweighted sample descriptions, not population estimates for Rwanda.")

    start_tab, workspace_tab, explore_tab, methods_tab = st.tabs(
        ["Start here", "Crop workspace", "Explore the sample", "Data and methods"]
    )
    with start_tab:
        _render_start_tab(overall, crops, facilities)
    with workspace_tab:
        _render_workspace(crops, release_note)
    with explore_tab:
        _render_explore_tab(
            seasons, provinces, crops, selected_seasons, selected_provinces
        )
    with methods_tab:
        _render_methods_tab(seasons, selected_seasons)

    st.caption(
        "AgriLoss Rwanda · NISR SAS 2024 production extracts · Track 1: post-harvest collection and storage, processing and value addition"
    )
