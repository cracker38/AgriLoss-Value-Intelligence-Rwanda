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
            "grouping": "Independent one-dimensional season, province, and crop summaries; no respondent rows or cross-tabulations.",
            "notes": [
                "Groups below the minimum size are pooled without their original labels.",
                "The group-size rule is a coarse suppression measure, not NISR disclosure approval.",
                "Obtain the required data-use and disclosure review before placing this file in a public repository.",
                "Stored, transformed, sold, and storage-stage loss quantities use NISR kilogram labels. Total reported loss (s2q39) still has no confirmed unit.",
                "Blank responses remain missing. Negative storage-stage loss values are counted, not clipped.",
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
