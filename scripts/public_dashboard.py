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
NO_LOCAL_CONDITION = "Not specified"


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


def _rank_crop_review(crops: pd.DataFrame, sort_column: str) -> pd.DataFrame:
    available = crops.loc[crops[sort_column].notna()]
    return available.sort_values(
        [sort_column, "records"],
        ascending=[False, False],
        na_position="last",
    ).reset_index(drop=True)


def _review_signal(
    crop_row: pd.Series,
    review_lens: str,
    track: str,
    *,
    rank: int,
    ranked_crops: int,
) -> str:
    if track == "storage":
        if review_lens == STORAGE_LENSES[0]:
            evidence = (
                f"{_percent(crop_row['stored_positive_share'])} "
                f"({ _int(crop_row['stored_positive_records']):,} of "
                f"{_int(crop_row['stored_reported_records']):,} valid answers)"
            )
        elif review_lens == STORAGE_LENSES[1]:
            evidence = (
                f"{_percent(crop_row['storage_loss_positive_share'])} "
                f"({ _int(crop_row['storage_loss_positive_records']):,} of "
                f"{_int(crop_row['storage_loss_reported_records']):,} valid answers)"
            )
        elif review_lens == STORAGE_LENSES[2]:
            evidence = (
                f"{_int(crop_row['stored_positive_records']):,} records with stored quantity > 0 "
                f"out of {_int(crop_row['records']):,} production records"
            )
        else:
            evidence = (
                f"{_percent(crop_row['stored_missing_share'])} missing "
                f"({_int(crop_row['stored_missing_records']):,} of "
                f"{_int(crop_row['records']):,} production records)"
            )
    elif review_lens == VALUE_LENSES[0]:
        evidence = (
            f"{_percent(crop_row['transformed_positive_share'])} "
            f"({ _int(crop_row['transformed_positive_records']):,} of "
            f"{_int(crop_row['transformed_reported_records']):,} valid answers)"
        )
    elif review_lens == VALUE_LENSES[1]:
        evidence = (
            f"{_percent(crop_row['sold_positive_share'])} "
            f"({ _int(crop_row['sold_positive_records']):,} of "
            f"{_int(crop_row['sold_reported_records']):,} valid answers)"
        )
    else:
        evidence = (
            f"{_kg(crop_row['median_reported_harvest_kg'])} median harvest "
            f"({_int(crop_row['harvest_reported_records']):,} valid records)"
        )

    return (
        f"{crop_row['crop']} ranks {rank} of {ranked_crops} named crop groups for "
        f"“{review_lens}”: {evidence}. This is a descriptive sample signal for follow-up, "
        "not an intervention ranking."
    )


def _follow_up_checks(
    crop_row: pd.Series,
    track: str,
    local_condition: str = NO_LOCAL_CONDITION,
) -> list[str]:
    checks: list[str] = []
    if track == "storage":
        missing = _int(crop_row["stored_missing_records"])
        negative = _int(crop_row["storage_loss_negative_records"])
        if missing:
            checks.append(
                f"Verify stored-quantity blanks and skip logic (`s2q36`): {missing:,} records are missing."
            )
        if negative:
            checks.append(
                f"Review {_int(crop_row['storage_loss_negative_records']):,} negative storage-stage loss values (`s2q47`) against the source records."
            )
        if _int(crop_row["public_stored_positive_records"]):
            checks.append(
                "Check reported public-storage use and facility responses (`s2q37`–`s2q38`) with local facilities."
            )
        if not checks:
            checks.append(
                "Verify local storage capacity and peak-season collection volumes; the survey does not measure facility capacity."
            )
        condition_checks = {
            "Storage capacity": "Compare the survey summary with verified local storage capacity and peak-season volume; neither is measured in SAS.",
            "Collection or transport": "Verify collection distances, transport costs, and seasonal access locally; these are not measured in SAS.",
            "Facility condition": "Inspect facility condition and capacity locally; SAS facility responses do not measure either.",
            "Other / unknown": "Verify the additional local issue with field evidence; it is not measured in the survey summary.",
        }
    else:
        zero_prices = _int(crop_row["sold_with_zero_price_records"])
        missing_prices = _int(crop_row["sold_with_missing_price_records"])
        if zero_prices:
            checks.append(
                f"Validate {_int(crop_row['sold_with_zero_price_records']):,} zero-price responses beside positive sales before valuing output."
            )
        if missing_prices:
            checks.append(
                f"Check price coverage: {_int(crop_row['sold_with_missing_price_records']):,} records with positive sales have no reported price."
            )
        checks.append(
            "Confirm current buyer prices, demand, processing yields, and costs with local operators; SAS 2024 does not provide current market data or profitability."
        )
        condition_checks = {
            "Processing equipment / capacity": "Verify equipment capacity, conversion yields, and operating costs with processors; SAS does not measure them.",
            "Product quality / yield": "Check buyer quality standards and processing conversion yields with operators; these are not measured in the released summary.",
            "Market access / prices": "Verify current buyer prices, sales outlets, and transport costs locally; survey prices are historical reports, not a current market feed.",
            "Other / unknown": "Verify the additional local issue with field evidence; it is not measured in the survey summary.",
        }

    if local_condition in condition_checks:
        checks.append(condition_checks[local_condition])
    return checks


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
    missing_price = _int(crop_row["sold_with_missing_price_records"])
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
        f"{zero_price:,} report a zero price and {missing_price:,} have no price. "
        "Zero prices next to positive sales need a coding check before any value calculation."
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
    *,
    review_signal: str | None = None,
    province_context: dict[str, Any] | None = None,
    local_condition: str = NO_LOCAL_CONDITION,
    local_notes: str = "",
) -> str:
    crop_name = str(crop_row["crop"])
    priority = (
        "Yes — mapped to NST2 priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas)."
        if crop_row["is_priority_crop"]
        else "Not listed as an NST2 priority food-crop group in this dashboard mapping."
    )
    if track == "storage":
        why = _storage_reading(crop_row)
        track_title = "Post-harvest collection and storage"
    else:
        why = _value_reading(crop_row)
        track_title = "Processing and value addition"

    signal = review_signal or (
        f"Selected sort: {review_lens}. This is a descriptive, unweighted sample signal."
    )
    checks = _follow_up_checks(crop_row, track, local_condition)
    if local_notes.strip():
        local_notes = local_notes.strip()
    if province_context:
        province_name = str(province_context["province"])
        province_description = (
            f"{province_name}: {_int(province_context['records']):,} unweighted production records; "
            f"{_percent(province_context.get('stored_positive_share'))} positive stored-quantity share "
            f"among valid province records."
        )
    else:
        province_description = "No province selected."

    return f"""# AgriLoss follow-up brief: {crop_name}

## Challenge in focus
{track_title}

## Review signal
{signal}

## What the SAS 2024 sample shows
{why}

## Location context
{province_description}
Province values are a separate marginal summary; they are not joined to this crop's values.

## Local condition supplied for review
- Condition: {local_condition}
- Notes: {local_notes or "None supplied"}

## Recommended evidence checks
{chr(10).join(f"- {check}" for check in checks)}

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
Use the evidence checks above before planning an intervention.

## What this brief is not
This is not a national estimate, a farmer ranking, a cause of loss, or a recommendation to build a store, mill, or factory. Season, province, and crop summaries cannot be combined in this public file.

Source: NISR Rwanda Seasonal Agricultural Survey 2024 production data, [NISR Microdata Portal](https://microdata.statistics.gov.rw/index.php/catalog/113).
Public dashboard status: {release_note}
"""


def _render_crop_review(
    review_queue: pd.DataFrame,
    review_lens: str,
    release_note: str,
    track: str,
    provinces: pd.DataFrame,
) -> None:
    st.markdown("##### Crops from the SAS 2024 sample")
    st.dataframe(
        _crop_review_table(review_queue, track),
        hide_index=True,
        width="stretch",
    )

    crop_options = review_queue["crop"].astype(str).tolist()
    selected_crop = st.selectbox(
        "Choose a crop to inspect",
        options=crop_options,
    )
    crop_position = crop_options.index(selected_crop)
    crop_row = review_queue.iloc[crop_position]
    review_signal = _review_signal(
        crop_row,
        review_lens,
        track,
        rank=crop_position + 1,
        ranked_crops=len(review_queue),
    )
    st.info(review_signal)

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
        condition_options = (
            NO_LOCAL_CONDITION,
            "Storage capacity",
            "Collection or transport",
            "Facility condition",
            "Other / unknown",
        )
    else:
        crop_metrics[0].metric("Transformed > 0", f"{_int(crop_row['transformed_positive_records']):,}")
        crop_metrics[1].metric("Share transformed (valid)", _percent(crop_row["transformed_positive_share"]))
        crop_metrics[2].metric("Sold > 0", f"{_int(crop_row['sold_positive_records']):,}")
        crop_metrics[3].metric("Share sold (valid)", _percent(crop_row["sold_positive_share"]))
        price_columns = st.columns(2)
        price_columns[0].metric(
            "Positive sales, zero price",
            f"{_int(crop_row['sold_with_zero_price_records']):,}",
        )
        price_columns[1].metric(
            "Positive sales, price missing",
            f"{_int(crop_row['sold_with_missing_price_records']):,}",
        )
        condition_options = (
            NO_LOCAL_CONDITION,
            "Processing equipment / capacity",
            "Product quality / yield",
            "Market access / prices",
            "Other / unknown",
        )

    st.markdown("#### Planning context")
    province_options = ["Not specified"]
    if "province" in provinces:
        province_options.extend(
            sorted(provinces["province"].dropna().astype(str).unique().tolist())
        )
    selected_province = st.selectbox("Province context", options=province_options)
    province_context = None
    if selected_province != "Not specified":
        province_rows = provinces.loc[
            provinces["province"].astype(str) == selected_province
        ]
        if not province_rows.empty:
            province_context = province_rows.iloc[0].to_dict()
            st.caption(
                f"{selected_province}: {_int(province_context['records']):,} unweighted records · "
                f"{_percent(province_context.get('stored_positive_share'))} with stored quantity > 0. "
                "Province results are separate from the selected crop."
            )
    local_condition = st.selectbox(
        "Local condition to investigate",
        options=condition_options,
    )
    local_notes = st.text_area(
        "Local notes (optional; do not enter personal information)",
        max_chars=500,
    )
    checks = _follow_up_checks(crop_row, track, local_condition)
    st.markdown("#### Recommended evidence checks")
    for check in checks:
        st.markdown(f"- {check}")

    brief = _follow_up_brief(
        crop_row,
        review_lens,
        release_note,
        track,
        review_signal=review_signal,
        province_context=province_context,
        local_condition=local_condition,
        local_notes=local_notes,
    )
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
    facilities: list[dict[str, Any]],
) -> None:
    st.markdown("### SAS 2024 sample")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Production records", f"{overall['records']:,}")
    metric_columns[1].metric(
        "Stored quantity > 0",
        f"{_int(overall['stored_positive_records']):,} · {_percent(overall['stored_positive_share'])}",
    )
    metric_columns[2].metric(
        "Transformed quantity > 0",
        f"{_int(overall['transformed_positive_records']):,} · {_percent(overall['transformed_positive_share'])}",
    )
    metric_columns[3].metric(
        "Quantity sold > 0",
        f"{_int(overall['sold_positive_records']):,} · {_percent(overall['sold_positive_share'])}",
    )
    extra = st.columns(4)
    extra[0].metric(
        "Storage-stage loss > 0",
        f"{_int(overall['storage_loss_positive_records']):,} · {_percent(overall.get('storage_loss_positive_share'))}",
    )
    extra[1].metric(
        "Negative storage-stage values",
        f"{_int(overall.get('storage_loss_negative_records')):,}",
    )
    extra[2].metric(
        "Public-storage quantity > 0",
        f"{_int(overall['public_stored_positive_records']):,}",
    )
    extra[3].metric(
        "Median harvest reported",
        _kg(overall.get("median_reported_harvest_kg")),
    )
    st.caption("Unweighted sample summaries; not national estimates. Blank answers are excluded.")

    if facilities:
        st.markdown("##### Reported storage facility (`s2q37`)")
        facility_frame = pd.DataFrame(facilities).rename(
            columns={"facility": "Facility response", "records": "Production records"}
        )
        st.dataframe(facility_frame, hide_index=True, width="stretch")


def _render_workspace(
    crops: pd.DataFrame,
    provinces: pd.DataFrame,
    release_note: str,
) -> None:
    st.markdown("### Crop workspace")
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
        review_lens = st.selectbox("Sort crops by", options=list(STORAGE_LENSES))
        sort_columns = {
            STORAGE_LENSES[0]: "stored_positive_share",
            STORAGE_LENSES[1]: "storage_loss_positive_share",
            STORAGE_LENSES[2]: "stored_positive_records",
            STORAGE_LENSES[3]: "stored_missing_share",
        }
    else:
        review_lens = st.selectbox("Sort crops by", options=list(VALUE_LENSES))
        sort_columns = {
            VALUE_LENSES[0]: "transformed_positive_share",
            VALUE_LENSES[1]: "sold_positive_share",
            VALUE_LENSES[2]: "median_reported_harvest_kg",
        }

    review_queue = _rank_crop_review(
        _named_crops(crops),
        sort_columns[review_lens],
    )
    if review_queue.empty:
        st.info("No named crop groups have a published value for this sort.")
        return
    _render_crop_review(
        review_queue,
        review_lens,
        release_note,
        track,
        provinces,
    )


def _render_explore_tab(
    seasons: pd.DataFrame,
    provinces: pd.DataFrame,
    crops: pd.DataFrame,
    selected_seasons: list[str],
    selected_provinces: list[str],
) -> None:
    st.markdown("### Look around the sample")
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
            has_published_shares = (
                "stored_positive_share" in province_view.columns
                and province_view["stored_positive_share"].notna().any()
            )
            y_column = "stored_positive_share" if has_published_shares else "records"
            if has_published_shares:
                province_view = province_view.dropna(subset=[y_column])
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
    stored = _rank_crop_review(named, "stored_positive_share").head(12)
    transformed = _rank_crop_review(named, "transformed_positive_share").head(12)
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
        st.divider()
        selected_seasons = st.multiselect(
            "Season",
            options=season_options,
            default=season_options,
        )
        selected_provinces = st.multiselect(
            "Province",
            options=province_options,
            default=province_options,
        )
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
        _render_start_tab(overall, facilities)
    with workspace_tab:
        _render_workspace(crops, provinces, release_note)
    with explore_tab:
        _render_explore_tab(
            seasons, provinces, crops, selected_seasons, selected_provinces
        )
    with methods_tab:
        _render_methods_tab(seasons, selected_seasons)

    st.caption(
        "AgriLoss Rwanda · NISR SAS 2024 production extracts · Track 1: post-harvest collection and storage, processing and value addition"
    )
