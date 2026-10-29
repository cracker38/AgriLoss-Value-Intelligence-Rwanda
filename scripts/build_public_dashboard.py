from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.dashboard_data import PUBLIC_DASHBOARD_PATH, ROOT, load_production_data


DEFAULT_OUTPUT = ROOT / "artifacts" / "dashboard_release_candidate.json"
MIN_GROUP_RECORDS = 100
LINKED_ANALYSIS_SEASON = "A"
PLOT_KEY_COLUMNS = ("Segment_ID", "s2q1")
PRACTICE_FIELDS = {
    "s4q3": "Anti-erosion activity",
    "s4q15": "Plot irrigated",
}
INPUT_FIELDS = {
    "s3q3": "Organic fertilizer used",
    "s3q9": "Inorganic fertilizer used",
    "s3q19": "Pesticide or fungicide used",
}
LINKED_BINARY_FIELDS = {**PRACTICE_FIELDS, **INPUT_FIELDS}
MARKET_CHANNELS = {
    "Market",
    "Farm/Home",
    "Not reported",
    "Cooperative or other reported channel (pooled)",
}
FACILITY_LABELS = {
    "Own storage": "Own storage",
    "Public storage": "Public storage",
    "Storage owned by Cooperatives/private companies": "Cooperative or private storage",
    "Other storage(specify)": "Other storage",
}
UNMAPPED_FACILITY_CODES = {"12", "13", "14"}


def _number_or_none(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def _quantity_summary(frame: pd.DataFrame, column: str, *, keep_negatives: bool = False) -> dict[str, Any]:
    values = pd.to_numeric(frame[column], errors="coerce") if column in frame else pd.Series(dtype="float64")
    valid = values.dropna()
    summary: dict[str, Any] = {
        "reported_records": int(valid.size),
        "missing_records": int(len(frame) - valid.size),
        "positive_records": int((valid > 0).sum()),
        "zero_records": int((valid == 0).sum()),
    }
    if keep_negatives:
        summary["negative_records"] = int((valid < 0).sum())
    if valid.size >= MIN_GROUP_RECORDS:
        summary["positive_share"] = round(float((valid > 0).mean()), 4)
        positive = valid[valid > 0]
        summary["median_positive"] = _number_or_none(positive.median()) if not positive.empty else None
    else:
        summary["positive_share"] = None
        summary["median_positive"] = None
    return summary


def _attach(summary: dict[str, Any], prefix: str, measure: dict[str, Any], *, kg: bool) -> None:
    summary[f"{prefix}_reported_records"] = measure["reported_records"]
    summary[f"{prefix}_missing_records"] = measure["missing_records"]
    summary[f"{prefix}_positive_records"] = measure["positive_records"]
    summary[f"{prefix}_positive_share"] = measure["positive_share"]
    median_key = f"{prefix}_median_positive_kg" if kg else f"{prefix}_median_positive_value"
    summary[median_key] = measure["median_positive"]
    if "negative_records" in measure:
        summary[f"{prefix}_negative_records"] = measure["negative_records"]


def _price_quality(frame: pd.DataFrame) -> dict[str, Any]:
    sold = pd.to_numeric(frame["s2q26"], errors="coerce") if "s2q26" in frame else pd.Series(dtype="float64")
    price = pd.to_numeric(frame["s2q28"], errors="coerce") if "s2q28" in frame else pd.Series(dtype="float64")
    sold_positive = sold > 0
    return {
        "sold_with_positive_price_records": int((sold_positive & (price > 0)).sum()),
        "sold_with_zero_price_records": int((sold_positive & (price == 0)).sum()),
        "sold_with_missing_price_records": int((sold_positive & price.isna()).sum()),
    }


def _measure_summary(frame: pd.DataFrame) -> dict[str, Any]:
    harvest = _quantity_summary(frame, "s2q21")
    loss = pd.to_numeric(frame["s2q39"], errors="coerce") if "s2q39" in frame else pd.Series(dtype="float64")
    loss_valid = loss.dropna()
    summary: dict[str, Any] = {
        "records": int(len(frame)),
        "loss_reported_records": int(loss_valid.size),
        "loss_missing_records": int(len(frame) - loss_valid.size),
        "positive_reported_loss_records": int((loss_valid > 0).sum()),
        "harvest_reported_records": harvest["reported_records"],
    }
    if loss_valid.size >= MIN_GROUP_RECORDS:
        summary["positive_reported_loss_share"] = round(float((loss_valid > 0).mean()), 4)
        summary["median_reported_loss_value"] = _number_or_none(loss_valid.median())
    else:
        summary["positive_reported_loss_share"] = None
        summary["median_reported_loss_value"] = None
    if harvest["reported_records"] >= MIN_GROUP_RECORDS:
        harvest_values = pd.to_numeric(frame["s2q21"], errors="coerce").dropna()
        summary["median_reported_harvest_kg"] = _number_or_none(harvest_values.median())
    else:
        summary["median_reported_harvest_kg"] = None

    _attach(summary, "stored", _quantity_summary(frame, "s2q36"), kg=True)
    _attach(summary, "public_stored", _quantity_summary(frame, "s2q38"), kg=True)
    _attach(
        summary,
        "storage_loss",
        _quantity_summary(frame, "s2q47", keep_negatives=True),
        kg=True,
    )
    _attach(summary, "transformed", _quantity_summary(frame, "s2q25"), kg=True)
    _attach(summary, "sold", _quantity_summary(frame, "s2q26"), kg=True)
    summary.update(_price_quality(frame))
    return summary


def _facility_summary(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if "s2q37" not in frame:
        return []
    labels = frame["s2q37"].astype("string")
    mapped = labels.map(lambda value: FACILITY_LABELS.get(str(value)) if pd.notna(value) else None)
    unmapped = labels.notna() & ~labels.isin(FACILITY_LABELS) & labels.isin(UNMAPPED_FACILITY_CODES)
    other_unexpected = labels.notna() & mapped.isna() & ~unmapped
    rows: list[dict[str, Any]] = []
    for label, count in mapped.dropna().value_counts().sort_index().items():
        rows.append({"facility": str(label), "records": int(count)})
    if int(unmapped.sum()):
        rows.append({"facility": "Unmapped facility code", "records": int(unmapped.sum())})
    if int(other_unexpected.sum()):
        rows.append({"facility": "Other unlabelled facility response", "records": int(other_unexpected.sum())})
    rows.append({"facility": "Not reported", "records": int(labels.isna().sum())})
    return rows


def _read_module_frame(season: str, module: str, fields: tuple[str, ...]) -> pd.DataFrame:
    source_path = ROOT / "dataset" / "nisrdataset" / f"sas_2024_season{season}_{module}.json"
    if not source_path.is_file():
        raise FileNotFoundError(f"Required linked SAS module is missing: {source_path}")
    with source_path.open("r", encoding="utf-8") as source:
        rows = json.load(source)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{source_path} must contain a JSON array of records")
    frame = pd.DataFrame.from_records(rows)
    required = {*PLOT_KEY_COLUMNS, "plot_weight", *fields}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{source_path} is missing linked fields: {sorted(missing)}")
    frame = frame.loc[:, [*PLOT_KEY_COLUMNS, "plot_weight", *fields]].copy()
    for column in frame.columns:
        frame[column] = frame[column].astype("string").str.strip().replace("", pd.NA)
    return frame


def _one_plot_value(values: pd.Series) -> Any:
    observed = values.dropna().unique()
    has_missing = bool(values.isna().any())
    if len(observed) > 1 or (has_missing and len(observed) == 1):
        raise ValueError("A repeated plot key has conflicting linked-module values")
    return observed[0] if len(observed) else pd.NA


def _plot_level_module(frame: pd.DataFrame, fields: tuple[str, ...]) -> pd.DataFrame:
    missing_keys = frame.loc[:, list(PLOT_KEY_COLUMNS)].isna().any(axis=1)
    if missing_keys.any():
        raise ValueError("Linked module has rows without complete plot join keys")

    grouped = frame.groupby(list(PLOT_KEY_COLUMNS), sort=False, dropna=False)
    plot_level = grouped.agg(
        {column: _one_plot_value for column in ("plot_weight", *fields)}
    ).reset_index()
    for column in fields:
        values = set(plot_level[column].dropna().astype(str).unique())
        unexpected = values.difference({"Yes", "No"})
        if unexpected:
            raise ValueError(
                f"Linked binary field {column} has unexpected responses: {sorted(unexpected)}"
            )
    return plot_level


def _join_plot_modules(
    production: pd.DataFrame,
    practice: pd.DataFrame,
    inputs: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    practice_plot = _plot_level_module(practice, tuple(PRACTICE_FIELDS))
    inputs_plot = _plot_level_module(inputs, tuple(INPUT_FIELDS))
    joined_modules = practice_plot.merge(
        inputs_plot,
        on=list(PLOT_KEY_COLUMNS),
        how="outer",
        suffixes=("_practice", "_inputs"),
        validate="one_to_one",
        indicator=True,
    )
    if not joined_modules["_merge"].eq("both").all():
        raise ValueError("Practice and fertilizer/pesticide plot keys do not match exactly")
    if not joined_modules["plot_weight_practice"].eq(
        joined_modules["plot_weight_inputs"]
    ).all():
        raise ValueError("Practice and fertilizer/pesticide plot weights do not match")
    joined_modules = joined_modules.drop(
        columns=["plot_weight_inputs", "_merge"]
    ).rename(columns={"plot_weight_practice": "module_plot_weight"})

    production_rows = production.copy()
    for column in PLOT_KEY_COLUMNS:
        production_rows[column] = (
            production_rows[column].astype("string").str.strip().replace("", pd.NA)
        )
    if production_rows.loc[:, list(PLOT_KEY_COLUMNS)].isna().any(axis=None):
        raise ValueError("Production rows are missing plot join keys")
    production_plot_weights = (
        production_rows.groupby(list(PLOT_KEY_COLUMNS), dropna=False)["plot_weight"]
        .nunique(dropna=False)
    )
    if production_plot_weights.gt(1).any():
        raise ValueError("Production plot records have inconsistent plot weights")

    linked = production_rows.merge(
        joined_modules,
        on=list(PLOT_KEY_COLUMNS),
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    if not linked["_merge"].eq("both").all():
        raise ValueError("A production plot does not have matching practice/input records")
    if not linked["plot_weight"].astype("string").eq(
        linked["module_plot_weight"].astype("string")
    ).all():
        raise ValueError("Production and linked-module plot weights do not match")
    linked = linked.drop(columns=["_merge", "module_plot_weight"])
    return linked, {
        "production_records": int(len(production_rows)),
        "production_plot_keys": int(production_rows.loc[:, list(PLOT_KEY_COLUMNS)].drop_duplicates().shape[0]),
        "matched_practice_plot_keys": int(len(practice_plot)),
        "fertilizer_pesticide_source_rows": int(len(inputs)),
        "fertilizer_pesticide_plot_keys": int(len(inputs_plot)),
    }


def _crop_practice_associations(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field, label in LINKED_BINARY_FIELDS.items():
        valid = frame.loc[frame[field].isin(["Yes", "No"])]
        for crop, crop_frame in valid.groupby("s2q4", sort=True, dropna=True):
            statuses = {
                status: group
                for status, group in crop_frame.groupby(field, sort=True)
            }
            if any(
                status not in statuses or len(statuses[status]) < MIN_GROUP_RECORDS
                for status in ("Yes", "No")
            ):
                continue
            for status in ("Yes", "No"):
                group = statuses[status]
                measure = _measure_summary(group)
                rows.append(
                    {
                        "crop": str(crop),
                        "practice_field": field,
                        "practice": label,
                        "status": status,
                        **measure,
                    }
                )
    return rows


def _market_channel_summaries(frame: pd.DataFrame) -> list[dict[str, Any]]:
    working = frame.copy()
    channels = working["s2q27"].astype("string").str.strip().replace("", pd.NA)
    channels = channels.fillna("Not reported")
    channels = channels.replace(
        {
            "Cooperative/company/Association": "Cooperative or other reported channel (pooled)",
            "Other selling place": "Cooperative or other reported channel (pooled)",
        }
    )
    working["_market_channel"] = channels
    available_channels = set(channels.unique())
    if not available_channels.issubset(MARKET_CHANNELS):
        unexpected = sorted(available_channels.difference(MARKET_CHANNELS))
        raise ValueError(f"Unexpected reported market channels: {unexpected}")

    rows: list[dict[str, Any]] = []
    for channel, group in working.groupby("_market_channel", sort=True):
        if len(group) < MIN_GROUP_RECORDS:
            continue
        sold = pd.to_numeric(group["s2q26"], errors="coerce")
        price = pd.to_numeric(group["s2q28"], errors="coerce")
        positive_sales = sold.gt(0)
        valid_sales = sold.notna()
        positive_prices = positive_sales & price.gt(0)
        positive_price_values = price.loc[positive_prices]
        rows.append(
            {
                "market_channel": str(channel),
                "production_records": int(len(group)),
                "valid_sales_records": int(valid_sales.sum()),
                "positive_sales_records": int(positive_sales.sum()),
                "positive_sales_share": (
                    round(float(positive_sales.sum() / valid_sales.sum()), 4)
                    if valid_sales.sum() >= MIN_GROUP_RECORDS
                    else None
                ),
                "median_positive_sales_kg": (
                    _number_or_none(sold.loc[positive_sales].median())
                    if positive_sales.sum() >= MIN_GROUP_RECORDS
                    else None
                ),
                "positive_price_records": (
                    int(positive_prices.sum())
                    if positive_prices.sum() >= MIN_GROUP_RECORDS
                    else None
                ),
                "median_positive_price_rwf_per_kg": (
                    _number_or_none(positive_price_values.median())
                    if positive_prices.sum() >= MIN_GROUP_RECORDS
                    else None
                ),
            }
        )
    return rows


def _build_linked_analysis() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    production = load_production_data(seasons=(LINKED_ANALYSIS_SEASON,))
    practice = _read_module_frame(
        LINKED_ANALYSIS_SEASON,
        "agricultural_practice",
        tuple(PRACTICE_FIELDS),
    )
    inputs = _read_module_frame(
        LINKED_ANALYSIS_SEASON,
        "fertilizer_pesticide",
        tuple(INPUT_FIELDS),
    )
    linked, linkage = _join_plot_modules(production, practice, inputs)
    return (
        _crop_practice_associations(linked),
        _market_channel_summaries(production),
        {
            "season": LINKED_ANALYSIS_SEASON,
            "join_key": list(PLOT_KEY_COLUMNS),
            **linkage,
            "practice_source": "NISR SAS 2024 Season A agricultural-practice module",
            "input_source": "NISR SAS 2024 Season A fertilizer/pesticide module",
            "weight_match": True,
            "interpretation": "Unweighted observational crop-record associations; not causal or population estimates.",
        },
    )


def _marginal_summaries(
    frame: pd.DataFrame,
    column: str,
    *,
    label_column: str,
    pooled_label: str,
    include_measures: bool,
) -> list[dict[str, Any]]:
    labels = frame[column].astype("string").fillna("Not reported")
    working = frame.assign(_release_label=labels)
    counts = working.groupby("_release_label", dropna=False).size()
    publish_labels = set(counts[counts >= MIN_GROUP_RECORDS].index.astype(str))
    common = working[working["_release_label"].astype(str).isin(publish_labels)]
    small = working[~working["_release_label"].astype(str).isin(publish_labels)]

    rows: list[dict[str, Any]] = []
    for value, group in common.groupby("_release_label", sort=True, dropna=False):
        row = {label_column: str(value), "records": int(len(group))}
        if include_measures:
            row.update(_measure_summary(group))
            row[label_column] = str(value)
        rows.append(row)

    if not small.empty:
        row = {label_column: pooled_label, "records": int(len(small))}
        if include_measures:
            row.update(_measure_summary(small))
            row[label_column] = pooled_label
        rows.append(row)
    return rows


def build_public_dashboard_candidate() -> dict[str, Any]:
    """Build coarse marginal summaries for disclosure review; never copy source rows."""
    data = load_production_data()
    crop_practice_rows, market_channel_rows, linkage = _build_linked_analysis()
    overall = _measure_summary(data)
    overall["distinct_crop_values"] = int(data["s2q4"].nunique(dropna=True))

    season_rows: list[dict[str, Any]] = []
    for season, frame in data.groupby("season", sort=True):
        row = _measure_summary(frame)
        row["season"] = str(season)
        row["distinct_crop_values"] = int(frame["s2q4"].nunique(dropna=True))
        season_rows.append(row)

    province_rows = _marginal_summaries(
        data,
        "s1q1",
        label_column="province",
        pooled_label="Other or unreported provinces (pooled)",
        include_measures=True,
    )
    crop_rows = _marginal_summaries(
        data,
        "s2q4",
        label_column="crop",
        pooled_label="Other or unreported crops (pooled)",
        include_measures=True,
    )

    return {
        "schema_version": 1,
        "release_status": "review_required",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "NISR SAS 2024 production extracts",
        "review": {
            "status": "required",
            "reviewed_by": None,
            "reviewed_on": None,
            "reference": None,
        },
        "aggregation": {
            "minimum_group_records": MIN_GROUP_RECORDS,
            "grouping": (
                "Independent season, province, and crop summaries, plus Season A crop-by-one-practice "
                "associations and Season A market-channel summaries; no respondent rows or geographic cross-tabulations."
            ),
            "notes": [
                "Groups below the minimum size are pooled without their original labels.",
                "The group-size rule is a coarse suppression measure, not NISR disclosure approval.",
                "Obtain the required data-use and disclosure review before placing this file in a public repository.",
                "Stored, transformed, sold, and storage-stage loss quantities use NISR kilogram labels. Total reported loss (s2q39) still has no confirmed unit.",
                "Blank responses remain missing. Negative storage-stage loss values are counted, not clipped.",
                "Crop-by-practice tables include a crop/response cell only when both Yes and No groups have at least 100 crop records.",
                "Season A practice/input links use Segment_ID + s2q1 after one-row-per-plot reduction, response consistency checks, complete key matching, and plot-weight equality checks.",
                "Season B practice data are excluded because their provenance is not confirmed. Season C is excluded because its sample is restricted.",
                "Market channel categories below 100 records are pooled. Market and price values are historical SAS 2024 reports, not a current market feed.",
                "Practice/input associations are unweighted and observational; they are not causal or population estimates.",
            ],
        },
        "interpretation": {
            "population_estimates": False,
            "survey_weights_applied": False,
            "s2q39_unit_confirmed": False,
            "s2q39_note": "Reported values are shown without a unit; the unit is unconfirmed.",
            "kilogram_fields": ["s2q21", "s2q25", "s2q26", "s2q36", "s2q38", "s2q47"],
        },
        "overall": overall,
        "by_season": season_rows,
        "by_province": province_rows,
        "by_crop": crop_rows,
        "by_storage_facility": _facility_summary(data),
        "by_crop_practice": crop_practice_rows,
        "by_market_channel": market_channel_rows,
        "module_linkage": linkage,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a coarse aggregate dashboard candidate for disclosure review."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--publish-provisional",
        action="store_true",
        help="Write the candidate to public_data/dashboard_aggregates.json, keeping the existing owner-authorization record.",
    )
    args = parser.parse_args(argv)

    payload = build_public_dashboard_candidate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote aggregate review candidate to {args.output}.")

    if args.publish_provisional:
        if not PUBLIC_DASHBOARD_PATH.is_file():
            raise FileNotFoundError(
                "Cannot publish provisionally without an existing authorized public file."
            )
        existing = json.loads(PUBLIC_DASHBOARD_PATH.read_text(encoding="utf-8"))
        payload["release_status"] = existing.get("release_status")
        payload["review"] = existing.get("review")
        payload["publication_authorization"] = existing.get("publication_authorization")
        if payload["release_status"] != "owner_authorized_unreviewed":
            raise ValueError("Refusing to overwrite a non-provisional public release automatically.")
        PUBLIC_DASHBOARD_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Updated provisional public aggregates at {PUBLIC_DASHBOARD_PATH}.")
    else:
        print("It is not approved for public release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
