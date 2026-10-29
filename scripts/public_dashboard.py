from __future__ import annotations

from datetime import datetime, timezone
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
    "Share of records with transport-stage loss (kg)",
    "Number of records with stored quantity",
    "Share missing a stored-quantity answer",
)
VALUE_LENSES = (
    "Share of records with transformed quantity (kg)",
    "Share of records with quantity sold (kg)",
    "Median reported harvest (kg)",
)
NO_LOCAL_CONDITION = "Not specified"
ALL_SURVEY_SEASONS = "All published SAS 2024 seasons"
USER_ROLE_OPTIONS = (
    "Farmer or producer",
    "Cooperative staff",
    "Agricultural planner",
    "Researcher or analyst",
    "Other project partner",
)
STORAGE_LOCAL_CONDITIONS = (
    "Storage capacity",
    "Drying or handling",
    "Facility condition or pest/moisture issue",
    "Collection or transport",
    "Peak-season volume exceeds collection",
    "Other / unknown",
)
PROCESSING_LOCAL_CONDITIONS = (
    "Processing equipment / capacity",
    "Product quality / yield",
    "Market access / prices",
    "Seasonal supply volume",
    "Processor or buyer access",
    "Other / unknown",
)
LOCAL_INPUT_LABELS = {
    "available_supply_kg": ("Expected crop supply for this planning period", "kg"),
    "storage_capacity_kg": ("Usable storage capacity", "kg"),
    "processing_capacity_kg": ("Processing capacity for this planning period", "kg"),
    "buyer_quote_rwf_per_kg": ("Current buyer quote supplied by user", "RWF/kg"),
    "processing_cost_rwf_per_kg": ("Estimated processing operating cost supplied by user", "RWF/kg"),
}
MIN_RECOMMENDATION_RECORDS = 100
PROCESSING_USE_METRICS = (
    (
        "food",
        "Food use",
        "transformed_food_positive_records",
        "transformed_food_positive_share",
        "transformed_food_reported_records",
        "transformed_food_median_positive_kg",
    ),
    (
        "drink",
        "Drink use",
        "transformed_drink_positive_records",
        "transformed_drink_positive_share",
        "transformed_drink_reported_records",
        "transformed_drink_median_positive_kg",
    ),
    (
        "other",
        "Other reported use",
        "transformed_other_positive_records",
        "transformed_other_positive_share",
        "transformed_other_reported_records",
        "transformed_other_median_positive_kg",
    ),
)
PROCESSING_EXAMPLES = {
    ("Maize", "food"): (
        "Compare local or contract milling into maize flour",
        "Rwanda Agriculture Board example: maize flour processing",
        "https://www.rab.gov.rw/1-1/news-details/the-director-general-visits-agro-processing-industries-in-gisagara-district",
    ),
    ("Cassava", "food"): (
        "Evaluate cassava flour products with an existing processor",
        "Rwanda Agriculture Board example: cassava flour and porridge research",
        "https://www.rab.gov.rw/fileadmin/user_upload/RAB/Publications/Reports/RAB-Annual_report___2012_2013.pdf",
    ),
    ("Cassava", "other"): (
        "Clarify the reported other use; if peels are available, assess a safe peel-to-feed route",
        "Rwanda Agriculture Board example: cassava peels for animal feed",
        "https://www.rab.gov.rw/1-1/news-details/rab-iita-train-farmers-on-processing-cassava-peels-into-animal-feed",
    ),
    ("Bush bean", "food"): (
        "Compare bean flour or blended products with existing processors",
        "Rwanda Agriculture Board report: beans used in flour and blended products",
        "https://www.rab.gov.rw/fileadmin/user_upload/RAB/Publications/Reports/RAB_Annual_2018-2019_FY.pdf",
    ),
    ("Climbing bean", "food"): (
        "Compare bean flour or blended products with existing processors",
        "Rwanda Agriculture Board report: beans used in flour and blended products",
        "https://www.rab.gov.rw/fileadmin/user_upload/RAB/Publications/Reports/RAB_Annual_2018-2019_FY.pdf",
    ),
    ("Banana for beer", "drink"): (
        "Evaluate banana juice or fermented beverage processing",
        "Rwanda Agriculture Board example: banana juice and beer processing",
        "https://www.rab.gov.rw/1-1/news-details/the-director-general-visits-agro-processing-industries-in-gisagara-district",
    ),
    ("Cooking banana", "drink"): (
        "Evaluate banana juice or fermented beverage processing",
        "Rwanda Agriculture Board example: banana juice and beer processing",
        "https://www.rab.gov.rw/1-1/news-details/the-director-general-visits-agro-processing-industries-in-gisagara-district",
    ),
    ("Dessert banana", "drink"): (
        "Evaluate banana juice or fermented beverage processing",
        "Rwanda Agriculture Board example: banana juice and beer processing",
        "https://www.rab.gov.rw/1-1/news-details/the-director-general-visits-agro-processing-industries-in-gisagara-district",
    ),
}


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
    reviewable = crops.loc[
        ~crops["crop"].astype(str).isin({POOLED_CROP_LABEL, "Not reported"})
    ].copy()
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


def _upper_quartile(crops: pd.DataFrame, field: str) -> float | None:
    if field not in crops:
        return None
    values = pd.to_numeric(crops[field], errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.quantile(0.75))


def _storage_investigation_queue(crops: pd.DataFrame) -> pd.DataFrame:
    """Flag named crops in the upper quartile of reported storage/transport loss shares."""
    peers = _named_crops(crops)
    if peers.empty:
        return pd.DataFrame()
    signals = (
        (
            "storage_loss_positive_share",
            "storage_loss_positive_records",
            "storage_loss_reported_records",
            "Storage-stage loss",
        ),
        (
            "transport_loss_positive_share",
            "transport_loss_positive_records",
            "transport_loss_reported_records",
            "Transport-stage loss",
        ),
    )
    rows: list[dict[str, Any]] = []
    for _, crop_row in peers.iterrows():
        reasons: list[str] = []
        for share_field, count_field, valid_field, label in signals:
            cutoff = _upper_quartile(peers, share_field)
            share = crop_row.get(share_field)
            if cutoff is None or share is None or pd.isna(share) or float(share) <= 0:
                continue
            if float(share) >= cutoff:
                reasons.append(
                    f"{label}: {_percent(float(share))} "
                    f"({_int(crop_row.get(count_field)):,}/{_int(crop_row.get(valid_field)):,} valid; "
                    f"named-crop 75th percentile {_percent(cutoff)})"
                )
        if reasons:
            rows.append(
                {
                    "Crop": str(crop_row["crop"]),
                    "Why investigate": "; ".join(reasons),
                    "Stored quantity > 0": (
                        f"{_percent(crop_row.get('stored_positive_share'))} "
                        f"({_int(crop_row.get('stored_positive_records')):,}/"
                        f"{_int(crop_row.get('stored_reported_records')):,} valid)"
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values("Crop").reset_index(drop=True) if rows else pd.DataFrame()


def _market_evidence(crop: str, market_rows: list[dict[str, Any]]) -> str:
    options = [
        row
        for row in market_rows
        if str(row.get("crop")) == crop
        and row.get("median_positive_price_rwf_per_kg") is not None
        and not pd.isna(row.get("median_positive_price_rwf_per_kg"))
    ]
    if not options:
        return "No crop/channel price group meets the display threshold."
    best = max(options, key=lambda row: _int(row.get("positive_price_records")))
    return (
        f"Season A {best['market_channel']}: median reported price "
        f"{float(best['median_positive_price_rwf_per_kg']):,.0f} RWF/kg "
        f"({ _int(best.get('positive_price_records')):,} positive-price records; historical only)."
    )


def _processing_use_options(
    crop_row: pd.Series,
    market_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    crop = str(crop_row["crop"])
    options: list[dict[str, Any]] = []
    for use_key, use_label, count_field, share_field, valid_field, median_field in PROCESSING_USE_METRICS:
        positive_count = _int(crop_row.get(count_field, 0))
        valid_count = _int(crop_row.get(valid_field, 0))
        share = crop_row.get(share_field)
        if positive_count < MIN_RECOMMENDATION_RECORDS or valid_count < MIN_RECOMMENDATION_RECORDS:
            continue
        option, source_label, source_url = PROCESSING_EXAMPLES.get(
            (crop, use_key),
            (
                f"Work with an existing processor to specify a crop-specific {use_key} product before comparing processes",
                "",
                "",
            ),
        )
        evidence = (
            f"SAS 2024 reports {positive_count:,} positive {use_key}-use quantities "
            f"({_percent(share)} of {valid_count:,} valid answers; median positive quantity "
            f"{_kg(crop_row.get(median_field))})."
        )
        market = _market_evidence(crop, market_rows)
        options.append(
            {
                "crop": crop,
                "use_key": use_key,
                "use_label": use_label,
                "option": option,
                "evidence": evidence,
                "market_evidence": market,
                "source_label": source_label,
                "source_url": source_url,
            }
        )
    return options


def _processing_option_queue(
    crops: pd.DataFrame,
    market_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    peers = _named_crops(crops)
    rows: list[dict[str, Any]] = []
    for _, crop_row in peers.iterrows():
        for option in _processing_use_options(crop_row, market_rows):
            rows.append(
                {
                    "Crop": option["crop"],
                    "Reported transformation use": option["use_label"],
                    "Option to evaluate": option["option"],
                    "Why it surfaced": option["evidence"],
                    "Documented Rwanda example": option["source_label"] or "No crop-specific example linked",
                    "Sale evidence": (
                        f"{_percent(crop_row.get('sold_positive_share'))} of valid sale answers "
                        f"positive ({_int(crop_row.get('sold_positive_records')):,}/"
                        f"{_int(crop_row.get('sold_reported_records')):,}). {option['market_evidence']}"
                    ),
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["Crop", "Reported transformation use"]
    ).reset_index(drop=True)


def _actionable_recommendations(
    crop_row: pd.Series,
    peer_crops: pd.DataFrame,
    track: str,
    market_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if track == "storage":
        recommendations: list[dict[str, str]] = []
        for share_field, count_field, valid_field, label, action in (
            (
                "storage_loss_positive_share",
                "storage_loss_positive_records",
                "storage_loss_reported_records",
                "Storage handling",
                "Inspect drying, storage duration, pests, facility condition, and the questionnaire skip pattern with farmers and facility operators.",
            ),
            (
                "transport_loss_positive_share",
                "transport_loss_positive_records",
                "transport_loss_reported_records",
                "Collection and transport",
                "Map collection handoffs, routes, handling damage, travel time, volumes, and cost with cooperatives or buyers; the survey records no route or cost.",
            ),
        ):
            cutoff = _upper_quartile(peer_crops, share_field)
            share = crop_row.get(share_field)
            if (
                cutoff is not None
                and share is not None
                and not pd.isna(share)
                and float(share) > 0
                and float(share) >= cutoff
            ):
                recommendations.append(
                    {
                        "title": f"Investigate {label.lower()} before proposing capacity or equipment",
                        "evidence": (
                            f"{_percent(float(share))} of valid {label.lower()} answers were positive "
                            f"({_int(crop_row.get(count_field)):,} of {_int(crop_row.get(valid_field)):,}); "
                            f"this is at or above the 75th percentile ({_percent(cutoff)}) among named crop groups."
                        ),
                        "action": action,
                    }
                )
        if not recommendations:
            recommendations.append(
                {
                    "title": "No above-quartile storage or transport-loss flag",
                    "evidence": "Neither positive storage-stage loss nor positive transport-stage loss is at or above the named-crop 75th percentile in the published sample summaries.",
                    "action": "Check local complaints, facility records, and collection conditions before dismissing a local issue. This comparative flag is not a safe-loss threshold.",
                }
            )
        return recommendations

    options = _processing_use_options(crop_row, market_rows)
    if options:
        return [
            {
                "title": option["option"],
                "evidence": f"{option['evidence']} {option['market_evidence']}",
                "action": "First compare contract processing with equipment purchase, then verify current buyer demand and prices, seasonal input volume, conversion yield, energy and packaging costs, quality standards, and food-safety requirements.",
                "source_label": option["source_label"],
                "source_url": option["source_url"],
            }
            for option in options
        ]
    transformed = _int(crop_row.get("transformed_positive_records", 0))
    if transformed:
        evidence = (
            f"{transformed:,} records report a positive transformed quantity, but no food, drink, or other-use category has 100 positive records in the published crop summary."
        )
    else:
        evidence = "The published crop summary has no food, drink, or other transformed-use category with 100 positive records."
    return [
        {
            "title": "No crop-specific process clears the evidence rule",
            "evidence": f"{evidence} Sales are positive in {_percent(crop_row.get('sold_positive_share'))} of valid quantity-sold answers. {_market_evidence(str(crop_row['crop']), market_rows)}",
            "action": "Ask processors and buyers to name a product and verify reliable seasonal supply before selecting a process. Do not infer demand or profitability from the sales share or historical survey price.",
        }
    ]


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
                f"{_percent(crop_row['transport_loss_positive_share'])} "
                f"({ _int(crop_row['transport_loss_positive_records']):,} of "
                f"{_int(crop_row['transport_loss_reported_records']):,} valid answers)"
            )
        elif review_lens == STORAGE_LENSES[3]:
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


def _local_condition_checks(
    track: str,
    local_conditions: str | list[str],
) -> list[str]:
    selected = (
        [local_conditions]
        if isinstance(local_conditions, str)
        else list(local_conditions)
    )
    if track == "storage":
        condition_actions = {
            "Storage capacity": "Compare the survey summary with verified local storage capacity and peak-season volume; neither is measured in SAS. Measure usable capacity against expected storage duration.",
            "Drying or handling": "Review drying surfaces, moisture checks, handling damage, and the time from harvest to storage.",
            "Facility condition or pest/moisture issue": "Inspect roofs, ventilation, pest controls, moisture protection, and storage records with facility operators.",
            "Facility condition": "Inspect facility condition and capacity locally; SAS facility responses do not measure either. Review roofs, ventilation, pest controls, moisture protection, and storage records with operators.",
            "Collection or transport": "Verify collection distances, transport costs, and seasonal access locally; map collection handoffs, route time, and handling damage with cooperatives and buyers.",
            "Peak-season volume exceeds collection": "Compare weekly peak-season harvest volumes with collection schedules, vehicle capacity, and storage intake capacity.",
            "Other / unknown": "Describe the additional local issue and verify it with field records or the people directly involved.",
        }
    else:
        condition_actions = {
            "Processing equipment / capacity": "Ask processors to verify available capacity, seasonal utilization, conversion yield, and operating cost for a small trial.",
            "Product quality / yield": "Compare trial product quality and conversion yield with buyer specifications and food-safety requirements.",
            "Market access / prices": "Collect current buyer quotes, sales terms, delivery requirements, and transport costs for the proposed product.",
            "Seasonal supply volume": "Estimate reliable monthly supply and seasonal gaps before comparing equipment or processing contracts.",
            "Processor or buyer access": "Identify existing processors and buyers, then document their product requirements, available capacity, and interest.",
            "Other / unknown": "Describe the additional local issue and verify it with field records or the people directly involved.",
        }
    return [
        condition_actions[condition]
        for condition in selected
        if condition in condition_actions
    ]


def _follow_up_checks(
    crop_row: pd.Series,
    track: str,
    local_condition: str | list[str] = NO_LOCAL_CONDITION,
) -> list[str]:
    checks: list[str] = []
    if track == "storage":
        missing = _int(crop_row["stored_missing_records"])
        negative = _int(crop_row["storage_loss_negative_records"])
        transport_negative = _int(crop_row.get("transport_loss_negative_records", 0))
        if missing:
            checks.append(
                f"Verify stored-quantity blanks and skip logic (`s2q36`): {missing:,} records are missing."
            )
        if negative:
            checks.append(
                f"Review {_int(crop_row['storage_loss_negative_records']):,} negative storage-stage loss values (`s2q47`) against the source records."
            )
        if transport_negative:
            checks.append(
                f"Review {_int(crop_row.get('transport_loss_negative_records')):,} negative transport-stage loss values (`s2q46`) against the source records."
            )
        if _int(crop_row.get("transport_loss_positive_records", 0)):
            checks.append(
                "Check reported transport-stage loss (`s2q46`) alongside local collection routes and transport records; the survey does not measure distance or cost."
            )
        if _int(crop_row["public_stored_positive_records"]):
            checks.append(
                "Check reported public-storage use and facility responses (`s2q37`–`s2q38`) with local facilities."
            )
        if not checks:
            checks.append(
                "Verify local storage capacity and peak-season collection volumes; the survey does not measure facility capacity."
            )
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
    checks.extend(_local_condition_checks(track, local_condition))
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
                "transport_loss_positive_records",
                "transport_loss_positive_share",
                "transport_loss_negative_records",
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
                "transport_loss_positive_records": "Transport-stage loss > 0",
                "transport_loss_positive_share": "Share transport-stage loss (valid s2q46)",
                "transport_loss_negative_records": "Negative s2q46 values",
            }
        )
        display["Share stored (valid s2q36)"] = display["Share stored (valid s2q36)"].map(_percent)
        display["Share storage-stage loss (valid s2q47)"] = display[
            "Share storage-stage loss (valid s2q47)"
        ].map(_percent)
        display["Share transport-stage loss (valid s2q46)"] = display[
            "Share transport-stage loss (valid s2q46)"
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


def _render_crop_season_comparison(
    season_crops: pd.DataFrame,
    crop: str,
    track: str,
) -> None:
    crop_rows = season_crops.loc[season_crops["crop"].astype(str) == crop].copy()
    if crop_rows.empty:
        st.caption("No season-specific crop comparison is available for this published group.")
        return
    if crop == POOLED_CROP_LABEL:
        st.caption(
            "The pooled row combines different uncommon or unreported crops in each season, so it cannot be compared as one crop."
        )
        return

    if track == "storage":
        measures = {
            "Storage-stage loss > 0": "storage_loss_positive_share",
            "Transport-stage loss > 0": "transport_loss_positive_share",
        }
        display_rows = []
        for _, row in crop_rows.sort_values("season").iterrows():
            display_rows.append(
                {
                    "SAS season": row["season"],
                    "Production records": _int(row["records"]),
                    "Storage-stage positive": (
                        f"{_int(row['storage_loss_positive_records']):,}/"
                        f"{_int(row['storage_loss_reported_records']):,} valid · "
                        f"{_percent(row['storage_loss_positive_share'])}"
                    ),
                    "Transport-stage positive": (
                        f"{_int(row['transport_loss_positive_records']):,}/"
                        f"{_int(row['transport_loss_reported_records']):,} valid · "
                        f"{_percent(row['transport_loss_positive_share'])}"
                    ),
                }
            )
    else:
        measures = {
            "Transformed quantity > 0": "transformed_positive_share",
            "Quantity sold > 0": "sold_positive_share",
        }
        display_rows = []
        for _, row in crop_rows.sort_values("season").iterrows():
            display_rows.append(
                {
                    "SAS season": row["season"],
                    "Production records": _int(row["records"]),
                    "Transformed positive": (
                        f"{_int(row['transformed_positive_records']):,}/"
                        f"{_int(row['transformed_reported_records']):,} valid · "
                        f"{_percent(row['transformed_positive_share'])}"
                    ),
                    "Sold positive": (
                        f"{_int(row['sold_positive_records']):,}/"
                        f"{_int(row['sold_reported_records']):,} valid · "
                        f"{_percent(row['sold_positive_share'])}"
                    ),
                }
            )

    chart_data = crop_rows.melt(
        id_vars=["season"],
        value_vars=list(measures.values()),
        var_name="measure",
        value_name="share",
    ).dropna(subset=["share"])
    chart_data["measure"] = chart_data["measure"].map(
        {value: label for label, value in measures.items()}
    )
    st.markdown("#### Compare this crop across SAS seasons")
    if chart_data.empty:
        st.info("Season comparisons are suppressed because these groups do not meet the publication threshold.")
    else:
        figure = px.bar(
            chart_data,
            x="season",
            y="share",
            color="measure",
            barmode="group",
            title=f"{crop}: reported positive-response shares by SAS season",
            labels={"season": "SAS 2024 season", "share": "Share of valid answers", "measure": "Measure"},
            color_discrete_sequence=["#0f6b4e", "#c9862a"],
        )
        figure.update_yaxes(tickformat=".0%")
        figure.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Source Sans 3, Segoe UI, sans-serif", color="#16332c"),
            margin=dict(l=12, r=12, t=58, b=12),
            xaxis_title=None,
            yaxis_title="Share of valid answers",
            legend_title_text=None,
        )
        st.plotly_chart(figure, width="stretch")
    st.dataframe(pd.DataFrame(display_rows), hide_index=True, width="stretch")
    st.caption(
        "Season-by-crop summaries are unweighted, independent seasonal samples, not farm-level trends. A missing crop-season row is suppressed, not zero. Season C is restricted; blank responses stay out of each valid denominator."
    )


def _storage_reading(crop_row: pd.Series) -> str:
    crop = str(crop_row["crop"])
    stored_share = crop_row["stored_positive_share"]
    stored_n = _int(crop_row["stored_positive_records"])
    stored_valid = _int(crop_row["stored_reported_records"])
    loss_share = crop_row["storage_loss_positive_share"]
    loss_n = _int(crop_row["storage_loss_positive_records"])
    negatives = _int(crop_row["storage_loss_negative_records"])
    transport_n = _int(crop_row.get("transport_loss_positive_records", 0))
    transport_share = crop_row.get("transport_loss_positive_share")
    transport_negative = _int(crop_row.get("transport_loss_negative_records", 0))
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
    parts.append(
        f"Transport-stage loss (`s2q46`, kg) is positive in {_percent(transport_share)} of valid answers "
        f"({transport_n:,} records); {transport_negative:,} negative values are retained as a quality flag. "
        "This does not identify a collection route, distance, or transport cost."
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
    local_condition: str | list[str] = NO_LOCAL_CONDITION,
    local_notes: str = "",
    planning_location: str = "",
    planning_period: str = "",
    survey_season: str = ALL_SURVEY_SEASONS,
    user_role: str = "Not specified",
    local_inputs: dict[str, float | None] | None = None,
    recommendations: list[dict[str, str]] | None = None,
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
    conditions = (
        [local_condition]
        if isinstance(local_condition, str)
        else list(local_condition)
    )
    conditions = [condition for condition in conditions if condition != NO_LOCAL_CONDITION]
    checks = _follow_up_checks(crop_row, track)
    condition_actions = _local_condition_checks(track, conditions)
    if recommendations is None:
        if track == "storage":
            recommendations = [
                {
                    "title": "Verify storage and collection conditions locally",
                    "evidence": (
                        f"The crop summary reports positive storage-stage loss in "
                        f"{_int(crop_row.get('storage_loss_positive_records')):,} records and "
                        f"positive transport-stage loss in "
                        f"{_int(crop_row.get('transport_loss_positive_records')):,} records. "
                        "This brief has no peer-group comparison, so it makes no relative priority claim."
                    ),
                    "action": "Review drying, storage, handling, collection routes, and local facility records with farmers, facility operators, cooperatives, and buyers.",
                }
            ]
        else:
            recommendations = _actionable_recommendations(
                crop_row,
                pd.DataFrame(),
                track,
                [],
            )
    recommendation_text = "\n".join(
        f"- **{item['title']}**\n  - Why: {item['evidence']}\n  - Next: {item['action']}"
        + (
            f"\n  - Rwanda example: [{item['source_label']}]({item['source_url']}) "
            "(documented example only; it does not establish feasibility or demand)."
            if item.get("source_url")
            else ""
        )
        for item in recommendations
    )
    planning_location = planning_location.strip() or "Not specified"
    planning_period = planning_period.strip() or "Not specified"
    local_notes = local_notes.strip()
    condition_text = ", ".join(conditions) if conditions else "None selected"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    local_inputs = local_inputs or {}
    local_input_keys = (
        ("available_supply_kg", "storage_capacity_kg")
        if track == "storage"
        else (
            "available_supply_kg",
            "processing_capacity_kg",
            "buyer_quote_rwf_per_kg",
            "processing_cost_rwf_per_kg",
        )
    )
    local_input_lines = []
    for key in local_input_keys:
        label, unit = LOCAL_INPUT_LABELS[key]
        value = local_inputs.get(key)
        local_input_lines.append(
            f"- {label}: {float(value):,.2f} {unit}"
            if value is not None
            else f"- {label}: Not supplied"
        )
    if province_context:
        province_name = str(province_context["province"])
        province_description = (
            f"{province_name}: {_int(province_context['records']):,} unweighted production records; "
            f"{_percent(province_context.get('stored_positive_share'))} positive stored-quantity share "
            f"among valid province records."
        )
    else:
        province_description = "No province selected."

    return f"""# AgriLoss crop follow-up report: {crop_name}

Generated: {generated_at}

## Challenge in focus
{track_title}

## Review signal
{signal}

## User and survey scope
- User role: {user_role}
- SAS 2024 survey season used for crop evidence: {survey_season}

## What the SAS 2024 sample shows
{why}

## Recommended next step to evaluate
{recommendation_text}

## Planning location
- Location or group entered: {planning_location}
- Planning period or season: {planning_period}
- Province survey context: {province_description}

The planning location is user-entered context. Crop evidence is not filtered to this location. Province values are a separate marginal summary and are not joined to this crop's values.

## Local conditions supplied for review
- Conditions selected: {condition_text}
- Notes: {local_notes or "None supplied"}

## Local quantities and market inputs
{chr(10).join(local_input_lines)}

These entries are user-supplied planning context and are not matched to SAS records. The current SAS release has no verified cost data, so AgriLoss does not estimate costs, margins, or profitability. Validate any quoted prices and costs locally.

## Local follow-up actions
{chr(10).join(f"- {action}" for action in condition_actions) or "No local conditions selected. Add relevant conditions before using this report to guide field work."}

## Survey data-quality checks
{chr(10).join(f"- {check}" for check in checks)}

## Sample snapshot (unweighted production records)
- Crop group: {crop_name}
- NST2 priority food crop: {priority}
- Production records: {_int(crop_row['records']):,}
- Stored quantity > 0 (`s2q36`, kg): {_int(crop_row['stored_positive_records']):,} · {_percent(crop_row['stored_positive_share'])} of valid answers · median when > 0: {_kg(crop_row['stored_median_positive_kg'])}
- Storage-stage loss > 0 (`s2q47`, kg): {_int(crop_row['storage_loss_positive_records']):,} · {_percent(crop_row['storage_loss_positive_share'])} of valid answers · negative values: {_int(crop_row['storage_loss_negative_records']):,}
- Transport-stage loss > 0 (`s2q46`, kg): {_int(crop_row.get('transport_loss_positive_records', 0)):,} · {_percent(crop_row.get('transport_loss_positive_share'))} of valid answers · negative values: {_int(crop_row.get('transport_loss_negative_records', 0)):,}
- Transformed quantity > 0 (`s2q25`, kg): {_int(crop_row['transformed_positive_records']):,} · {_percent(crop_row['transformed_positive_share'])} of valid answers · median when > 0: {_kg(crop_row['transformed_median_positive_kg'])}
- Quantity sold > 0 (`s2q26`, kg): {_int(crop_row['sold_positive_records']):,} · {_percent(crop_row['sold_positive_share'])} of valid answers · median when > 0: {_kg(crop_row['sold_median_positive_kg'])}
- Median harvest (`s2q21`, kg): {_kg(crop_row['median_reported_harvest_kg'])}
- Positive total reported-loss answers (`s2q39`, unit unconfirmed): {_int(crop_row['positive_reported_loss_records']):,} · {_percent(crop_row['positive_reported_loss_share'])} of valid answers
- Review lens: {review_lens}

## Decision gate
Complete the local follow-up actions and evidence checks above. Confirm seasonal supply, buyer/processor interest, current terms, product quality, yields, and costs before selecting a process, facility, or investment.

## What this brief is not
This is not a national estimate, a farmer ranking, a cause of loss, or an investment recommendation. Candidate process routes are evaluation ideas only; crop-by-season summaries are available, while province values remain separate from crop evidence.

Source: NISR Rwanda Seasonal Agricultural Survey 2024 production data, [NISR Microdata Portal](https://microdata.statistics.gov.rw/index.php/catalog/113).
Public dashboard status: {release_note}
"""


def _render_crop_review(
    review_queue: pd.DataFrame,
    season_crops: pd.DataFrame,
    review_lens: str,
    release_note: str,
    track: str,
    survey_season: str,
    provinces: pd.DataFrame,
    peer_crops: pd.DataFrame,
    market_rows: list[dict[str, Any]],
) -> None:
    st.markdown("#### 1. Choose a crop to review")
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
    _render_crop_season_comparison(season_crops, selected_crop, track)
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
        condition_options = STORAGE_LOCAL_CONDITIONS
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
        condition_options = PROCESSING_LOCAL_CONDITIONS

    st.markdown("#### 2. Add the planning context")
    province_options = ["Not specified"]
    if "province" in provinces:
        province_options.extend(
            sorted(provinces["province"].dropna().astype(str).unique().tolist())
        )
    with st.form(key=f"crop_follow_up_form_{track}"):
        user_role = st.selectbox(
            "Your role",
            options=USER_ROLE_OPTIONS,
        )
        location_column, period_column = st.columns(2)
        planning_location = location_column.text_input(
            "Planning location (district, cooperative, or market)",
            max_chars=120,
            help="Enter the area or group this plan concerns. This does not filter the survey results.",
        )
        planning_period = period_column.text_input(
            "Planning season or period (optional)",
            max_chars=80,
            help="For example, the upcoming season or a planned assessment period.",
        )
        selected_province = st.selectbox(
            "Province survey context (optional)",
            options=province_options,
            help="Province figures are a separate sample summary and are not joined to the selected crop.",
        )
        local_conditions = st.multiselect(
            "Conditions to investigate locally",
            options=condition_options,
            help="Select the constraints reported by local partners. These answers guide the checklist; they are not SAS survey observations.",
        )
        st.markdown("**Optional local quantities and market details**")
        st.caption("Enter current planning values if known. These values are not checked against or joined to SAS records; leave 0 if unknown.")
        if track == "storage":
            supply_column, storage_column = st.columns(2)
            available_supply_kg = supply_column.number_input(
                "Expected crop supply for this period (kg)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )
            storage_capacity_kg = storage_column.number_input(
                "Usable storage capacity (kg)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )
            processing_capacity_kg = 0.0
            buyer_quote_rwf_per_kg = 0.0
            processing_cost_rwf_per_kg = 0.0
        else:
            supply_column, capacity_column = st.columns(2)
            available_supply_kg = supply_column.number_input(
                "Expected crop supply for this period (kg)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )
            processing_capacity_kg = capacity_column.number_input(
                "Available processing capacity for this period (kg)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
            )
            quote_column, cost_column = st.columns(2)
            buyer_quote_rwf_per_kg = quote_column.number_input(
                "Current buyer quote (RWF/kg)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                format="%.2f",
            )
            processing_cost_rwf_per_kg = cost_column.number_input(
                "Estimated variable processing cost (RWF/kg)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                format="%.2f",
                help="Enter a current local estimate. The survey has no cost data and this value is not validated.",
            )
            storage_capacity_kg = 0.0
        local_notes = st.text_area(
            "Local notes (optional; do not enter personal information)",
            max_chars=500,
        )
        submitted = st.form_submit_button(
            "Review recommendation and field actions",
            type="primary",
        )

    if not submitted:
        st.caption("Submit the planning context to review the crop recommendation and prepare a follow-up report.")
        return
    if not planning_location.strip():
        st.error("Enter the planning location or group before reviewing the recommendation.")
        return

    local_inputs: dict[str, float | None] = {
        "available_supply_kg": available_supply_kg or None,
    }
    if track == "storage":
        local_inputs["storage_capacity_kg"] = storage_capacity_kg or None
    else:
        local_inputs["processing_capacity_kg"] = processing_capacity_kg or None
        local_inputs["buyer_quote_rwf_per_kg"] = buyer_quote_rwf_per_kg or None
        local_inputs["processing_cost_rwf_per_kg"] = processing_cost_rwf_per_kg or None

    province_context = None
    if selected_province != "Not specified":
        province_rows = provinces.loc[
            provinces["province"].astype(str) == selected_province
        ]
        if not province_rows.empty:
            province_context = province_rows.iloc[0].to_dict()
            st.caption(
                f"{selected_province}: {_int(province_context['records']):,} unweighted records; "
                f"{_percent(province_context.get('stored_positive_share'))} with stored quantity > 0. "
                "Province results are separate from the selected crop."
            )

    recommendations = _actionable_recommendations(
        crop_row,
        peer_crops,
        track,
        market_rows,
    )
    checks = _follow_up_checks(crop_row, track)
    local_actions = _local_condition_checks(track, local_conditions)

    st.markdown("#### 3. Review the recommendation")
    st.caption(
        "The recommendation uses crop-level SAS evidence. Your entered location and conditions guide local follow-up; they do not change or geographically filter the survey evidence."
    )
    for item in recommendations:
        st.markdown(f"**{item['title']}**")
        st.markdown(f"- **Survey evidence:** {item['evidence']}")
        st.markdown(f"- **Next step:** {item['action']}")
        if item.get("source_url"):
            st.markdown(
                f"- Rwanda example: [{item['source_label']}]({item['source_url']}) "
                "(documented example only; it does not establish demand or feasibility)."
            )

    st.markdown("#### Local values you entered")
    entered_rows = [
        {
            "Planning input": LOCAL_INPUT_LABELS[key][0],
            "Entered value": f"{float(value):,.2f} {LOCAL_INPUT_LABELS[key][1]}",
        }
        for key, value in local_inputs.items()
        if value is not None
    ]
    if entered_rows:
        st.dataframe(pd.DataFrame(entered_rows), hide_index=True, width="stretch")
    else:
        st.caption("No local quantities or market values were entered.")
    st.caption(
        "The SAS 2024 aggregate contains no verified cost data. AgriLoss does not calculate cost, margin, or profitability estimates."
    )

    st.markdown("#### Local actions prompted by your conditions")
    if local_actions:
        for action in local_actions:
            st.markdown(f"- {action}")
    else:
        st.info("No local conditions were selected. Add relevant constraints before using the report to guide field work.")

    st.markdown("#### Survey data-quality checks")
    for check in checks:
        st.markdown(f"- {check}")

    brief = _follow_up_brief(
        crop_row,
        review_lens,
        release_note,
        track,
        review_signal=review_signal,
        province_context=province_context,
        local_condition=local_conditions,
        local_notes=local_notes,
        planning_location=planning_location,
        planning_period=planning_period,
        survey_season=survey_season,
        user_role=user_role,
        local_inputs=local_inputs,
        recommendations=recommendations,
    )
    file_stub = "storage" if track == "storage" else "value-addition"
    with st.expander("Preview the crop follow-up report"):
        st.markdown(brief)
    st.download_button(
        "Download crop follow-up report",
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
    extra = st.columns(5)
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
    extra[4].metric(
        "Transport-stage loss > 0",
        f"{_int(overall.get('transport_loss_positive_records')):,} · {_percent(overall.get('transport_loss_positive_share'))}",
    )
    st.caption("Unweighted sample summaries; not national estimates. Blank answers are excluded.")
    st.markdown("#### How to use AgriLoss")
    st.markdown(
        """
        1. Open **Start here** to review the data scope and intended users.
        2. Choose **post-harvest collection and storage** or **processing and value addition** in Crop workspace.
        3. Select a SAS 2024 season and crop; identify your role; enter the planning location and period; then add relevant local quantities, prices, costs, and conditions.
        4. AgriLoss uses grouped NISR data, checks provided numeric values are non-negative, and keeps local entries separate from survey statistics.
        5. Review the evidence-based follow-up recommendation and the local information still needed.
        6. Compare crop measures, sales, and historical market evidence where available. The current release has no validated cost or margin estimates.
        7. Preview and download the report with evidence, local context, actions, and limitations.
        8. Use the report to plan field checks and decide what to verify next; confirm local evidence before choosing an intervention.
        """
    )

    if facilities:
        st.markdown("##### Reported storage facility (`s2q37`)")
        facility_frame = pd.DataFrame(facilities).rename(
            columns={"facility": "Facility response", "records": "Production records"}
        )
        st.dataframe(facility_frame, hide_index=True, width="stretch")


def _render_workspace(
    crops: pd.DataFrame,
    season_crops: pd.DataFrame,
    provinces: pd.DataFrame,
    release_note: str,
    market_rows: list[dict[str, Any]],
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
    season_options = sorted(season_crops["season"].astype(str).unique().tolist())
    survey_season = st.selectbox(
        "SAS season for crop evidence",
        options=[ALL_SURVEY_SEASONS, *season_options],
    )
    if survey_season == ALL_SURVEY_SEASONS:
        workspace_crops = crops
        st.caption(
            "Crop summaries pool the published SAS 2024 seasons. Season C is a restricted sample."
        )
    else:
        workspace_crops = season_crops.loc[
            season_crops["season"].astype(str) == survey_season
        ].drop(columns="season")
        if survey_season == "C":
            st.caption(
                "Season C is a restricted sample. Its crop-level summaries are not representative of a full seasonal sample."
            )
        else:
            st.caption(
                f"Crop evidence uses SAS Season {survey_season} only; crop groups below the publication threshold are pooled."
            )
    peer_crops = _named_crops(workspace_crops)

    if track == "storage":
        st.markdown("#### Crops to investigate for storage or collection")
        st.caption(
            "Flags are crop groups at or above the 75th percentile for positive storage-stage or transport-stage loss share among named crop groups. "
            "They are relative investigation flags within the selected season basis, not acceptable-loss limits or investment rankings. Summaries are unweighted."
        )
        investigation_queue = _storage_investigation_queue(workspace_crops)
        if investigation_queue.empty:
            st.info("No crop group crosses the displayed relative investigation flags. Local evidence may still justify a review.")
        else:
            st.dataframe(investigation_queue, hide_index=True, width="stretch")
    else:
        st.markdown("#### Processing options worth evaluating")
        st.caption(
            "Options are tied to reported food, drink, or other transformation use. A named option appears only when at least 100 records report that use; this is a display rule, not a business-case threshold."
        )
        processing_queue = _processing_option_queue(workspace_crops, market_rows)
        if processing_queue.empty:
            st.info(
                "No crop-specific processing option meets the minimum evidence rule. "
                "First confirm product, supply, buyer requirements, and processor interest locally."
            )
        else:
            st.dataframe(processing_queue, hide_index=True, width="stretch")
        st.caption(
            "Market evidence comes from Season A 2024 reports. It does not establish current prices, demand, conversion yields, costs, or profitability."
        )
        if survey_season != "A":
            selected_basis = (
                "the pooled all-season crop evidence"
                if survey_season == ALL_SURVEY_SEASONS
                else f"the selected Season {survey_season} crop evidence"
            )
            st.caption(
                f"The displayed historical market prices are Season A only; they are not matched to {selected_basis}."
            )

    if track == "storage":
        review_lens = st.selectbox("Sort crops by", options=list(STORAGE_LENSES))
        sort_columns = {
            STORAGE_LENSES[0]: "stored_positive_share",
            STORAGE_LENSES[1]: "storage_loss_positive_share",
            STORAGE_LENSES[2]: "transport_loss_positive_share",
            STORAGE_LENSES[3]: "stored_positive_records",
            STORAGE_LENSES[4]: "stored_missing_share",
        }
    else:
        review_lens = st.selectbox("Sort crops by", options=list(VALUE_LENSES))
        sort_columns = {
            VALUE_LENSES[0]: "transformed_positive_share",
            VALUE_LENSES[1]: "sold_positive_share",
            VALUE_LENSES[2]: "median_reported_harvest_kg",
        }

    review_queue = _rank_crop_review(
        peer_crops,
        sort_columns[review_lens],
    )
    if review_queue.empty:
        st.info("No named crop groups have a published value for this sort.")
        return
    _render_crop_review(
        review_queue,
        season_crops,
        review_lens,
        release_note,
        track,
        survey_season,
        provinces,
        peer_crops,
        market_rows,
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
            "transport_loss_positive_records",
            "transport_loss_positive_share",
            "transport_loss_negative_records",
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
        - Median kilograms for stored, transformed, sold, storage-stage loss, and transport-stage loss are medians **among positive values**, so zeros do not pull them to zero.
        - Median harvest uses all valid `s2q21` values, including zeros if any.
        - `s2q36`, `s2q38`, `s2q25`, `s2q26`, `s2q46`, and `s2q47` are labelled in kilograms. `s2q39` is not.
        - Negative `s2q46` and `s2q47` values are counted and not clipped.
        - Transport-stage loss is a collection/transport signal; the survey does not include routes, distances, costs, or collection volumes at facilities.
        - Facility codes 12, 13, and 14 are not mapped to a storage type.
        - The workspace supports crop summaries by SAS 2024 season. Province summaries remain separate and are not joined to crop or season results.
        - Season-by-crop groups with fewer than 100 records are pooled within season without their original names.
        - Seasonal summaries are independent survey samples, not repeated measurements of the same farms. Season C is restricted.
        - The release contains no verified costs; user-entered prices and costs are context only and are not used to estimate margins.
        - Survey weights are not applied.
        """
    )


def _render_linked_analysis(
    practice_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    crop_market_rows: list[dict[str, Any]],
    linkage: dict[str, Any],
) -> None:
    if not practice_rows and not market_rows and not crop_market_rows:
        st.info(
            "Linked practice and market summaries are not in this public aggregate release. "
            "They require a fresh aggregate build and disclosure review before publication."
        )
        return

    st.markdown("### Season A production links to farm practices and inputs")
    st.caption(
        "Production records are linked to the agricultural-practice and fertilizer/pesticide modules at plot level. "
        f"Season {linkage.get('season', 'A')} · unweighted crop-record comparisons · "
        f"{_int(linkage.get('matched_practice_plot_keys')):,} of "
        f"{_int(linkage.get('production_plot_keys')):,} production plot keys matched with exact keys and equal plot weights · "
        "observational associations, not causes or population estimates."
    )
    if practice_rows:
        practice = pd.DataFrame(practice_rows)
        practice_options = sorted(practice["practice"].astype(str).unique().tolist())
        selected_practice = st.selectbox(
            "Practice or input",
            options=practice_options,
        )
        practice_view = practice.loc[practice["practice"] == selected_practice]
        crop_options = sorted(practice_view["crop"].astype(str).unique().tolist())
        if crop_options:
            selected_crop = st.selectbox("Crop", options=crop_options)
            crop_view = practice_view.loc[practice_view["crop"] == selected_crop].copy()
            if not crop_view.empty:
                measure_labels = {
                    "Stored quantity > 0": "stored_positive_share",
                    "Storage-stage loss > 0": "storage_loss_positive_share",
                    "Transformed quantity > 0": "transformed_positive_share",
                    "Quantity sold > 0": "sold_positive_share",
                }
                selected_measure = st.selectbox(
                    "Compare outcome",
                    options=list(measure_labels),
                )
                chart_data = crop_view.loc[
                    :, ["status", "records", measure_labels[selected_measure]]
                ].rename(
                    columns={
                        "status": "Practice response",
                        "records": "Crop records",
                        measure_labels[selected_measure]: "share",
                    }
                )
                chart_data = chart_data.dropna(subset=["share"])
                if not chart_data.empty:
                    st.plotly_chart(
                        _bar_chart(
                            chart_data,
                            x="Practice response",
                            y="share",
                            title=f"{selected_crop} · {selected_measure}",
                            y_label="Share of valid crop records",
                            percent_axis=True,
                        ),
                        width="stretch",
                    )

                display = crop_view.loc[
                    :,
                    [
                        "status",
                        "records",
                        "stored_positive_records",
                        "stored_positive_share",
                        "storage_loss_positive_records",
                        "storage_loss_positive_share",
                        "transformed_positive_records",
                        "transformed_positive_share",
                        "sold_positive_records",
                        "sold_positive_share",
                    ],
                ].rename(
                    columns={
                        "status": "Practice response",
                        "records": "Crop records",
                        "stored_positive_records": "Stored > 0 records",
                        "stored_positive_share": "Stored > 0 share",
                        "storage_loss_positive_records": "Storage loss > 0 records",
                        "storage_loss_positive_share": "Storage loss > 0 share",
                        "transformed_positive_records": "Transformed > 0 records",
                        "transformed_positive_share": "Transformed > 0 share",
                        "sold_positive_records": "Sold > 0 records",
                        "sold_positive_share": "Sold > 0 share",
                    }
                )
                for column in display.columns:
                    if column.endswith("share"):
                        display[column] = display[column].map(_percent)
                st.dataframe(display, hide_index=True, width="stretch")
        else:
            st.info("No crop has both Yes and No groups meeting the release threshold for this practice.")
    if market_rows:
        st.markdown("### Reported sales channels and prices")
        market = pd.DataFrame(market_rows).rename(
            columns={
                "market_channel": "Reported market channel",
                "production_records": "Production records",
                "valid_sales_records": "Valid quantity-sold answers",
                "positive_sales_records": "Positive-sales records",
                "positive_sales_share": "Share of valid answers with sales",
                "median_positive_sales_kg": "Median positive quantity sold (kg)",
                "positive_price_records": "Positive-price records",
                "median_positive_price_rwf_per_kg": "Median reported price (RWF/kg)",
            }
        )
        if "Share of valid answers with sales" in market:
            market["Share of valid answers with sales"] = market[
                "Share of valid answers with sales"
            ].map(_percent)
        st.dataframe(market, hide_index=True, width="stretch")
        st.caption(
            "Market channel and price responses are historical SAS 2024 reports, not a current market feed. "
            "Rare channels are pooled; blank prices are not treated as zero."
        )
    if crop_market_rows:
        st.markdown("### Crop sales and reported price by market channel")
        crop_market = pd.DataFrame(crop_market_rows)
        crop_options = sorted(crop_market["crop"].astype(str).unique().tolist())
        selected_crop = st.selectbox("Crop for market comparison", options=crop_options)
        crop_view = crop_market.loc[crop_market["crop"].astype(str) == selected_crop].copy()
        chart_view = crop_view.dropna(subset=["median_positive_price_rwf_per_kg"])
        if not chart_view.empty:
            st.plotly_chart(
                _bar_chart(
                    chart_view,
                    x="market_channel",
                    y="median_positive_price_rwf_per_kg",
                    title=f"{selected_crop} · median reported price by channel",
                    y_label="Median positive reported price (RWF/kg)",
                    x_angle=-20,
                    color="#477c91",
                ),
                width="stretch",
            )
        display = crop_view.loc[
            :,
            [
                "market_channel",
                "production_records",
                "valid_sales_records",
                "positive_sales_records",
                "positive_sales_share",
                "median_positive_sales_kg",
                "positive_price_records",
                "median_positive_price_rwf_per_kg",
            ],
        ].rename(
            columns={
                "market_channel": "Reported market channel",
                "production_records": "Production records",
                "valid_sales_records": "Valid sales answers",
                "positive_sales_records": "Positive-sales records",
                "positive_sales_share": "Share of valid answers with sales",
                "median_positive_sales_kg": "Median positive quantity sold (kg)",
                "positive_price_records": "Positive-price records",
                "median_positive_price_rwf_per_kg": "Median reported price (RWF/kg)",
            }
        )
        display["Share of valid answers with sales"] = display[
            "Share of valid answers with sales"
        ].map(_percent)
        st.dataframe(display, hide_index=True, width="stretch")
        st.caption(
            "Only crop/channel groups with at least 100 production records are shown. Prices are historical SAS 2024 reports, "
            "not current quotes or a profitability estimate; confirm current buyer prices and terms locally."
        )


def render_public_dashboard(payload: dict[str, Any]) -> None:
    """Render storage and value-addition summaries from SAS 2024 aggregates only."""
    overall = payload["overall"]
    seasons = pd.DataFrame(payload["by_season"])
    season_crops = pd.DataFrame(payload["by_season_crop"])
    provinces = pd.DataFrame(payload["by_province"])
    crops = pd.DataFrame(payload["by_crop"])
    facilities = payload.get("by_storage_facility") or []
    practice_rows = payload.get("by_crop_practice") or []
    market_rows = payload.get("by_market_channel") or []
    crop_market_rows = payload.get("by_crop_market_channel") or []
    linkage = payload.get("module_linkage") or {}

    season_options = sorted(seasons["season"].astype(str).unique().tolist())
    province_options = sorted(provinces["province"].astype(str).unique().tolist())
    with st.sidebar:
        st.markdown("### AgriLoss Rwanda")
        st.divider()
        selected_seasons = st.multiselect(
            "Explore seasons",
            options=season_options,
            default=season_options,
        )
        selected_provinces = st.multiselect(
            "Explore provinces",
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

    start_tab, workspace_tab, explore_tab, linked_tab, methods_tab = st.tabs(
        [
            "Start here",
            "Crop workspace",
            "Explore the sample",
            "SAS module links",
            "Data and methods",
        ]
    )
    with start_tab:
        _render_start_tab(overall, facilities)
    with workspace_tab:
        _render_workspace(
            crops,
            season_crops,
            provinces,
            release_note,
            crop_market_rows,
        )
    with explore_tab:
        _render_explore_tab(
            seasons, provinces, crops, selected_seasons, selected_provinces
        )
    with linked_tab:
        _render_linked_analysis(practice_rows, market_rows, crop_market_rows, linkage)
    with methods_tab:
        _render_methods_tab(seasons, selected_seasons)

    st.caption(
        "AgriLoss Rwanda · NISR SAS 2024 production extracts · Track 1: post-harvest collection and storage, processing and value addition"
    )
