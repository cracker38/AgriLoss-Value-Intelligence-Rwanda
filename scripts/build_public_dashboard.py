from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.dashboard_data import ROOT, load_production_data


DEFAULT_OUTPUT = ROOT / "artifacts" / "dashboard_release_candidate.json"
MIN_GROUP_RECORDS = 100


def _number_or_none(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 2)


def _measure_summary(frame: pd.DataFrame, label: str | None = None) -> dict[str, Any]:
    loss = pd.to_numeric(frame["s2q39"], errors="coerce").dropna()
    harvest = pd.to_numeric(frame["s2q21"], errors="coerce").dropna()
    summary: dict[str, Any] = {
        "records": int(len(frame)),
        "loss_reported_records": int(loss.size),
        "loss_missing_records": int(len(frame) - loss.size),
        "positive_reported_loss_records": int(loss.gt(0).sum()),
        "harvest_reported_records": int(harvest.size),
    }
    if loss.size >= MIN_GROUP_RECORDS:
        summary["positive_reported_loss_share"] = round(float(loss.gt(0).mean()), 4)
        summary["median_reported_loss_value"] = _number_or_none(loss.median())
    else:
        summary["positive_reported_loss_share"] = None
        summary["median_reported_loss_value"] = None
    if harvest.size >= MIN_GROUP_RECORDS:
        summary["median_reported_harvest_kg"] = _number_or_none(harvest.median())
    else:
        summary["median_reported_harvest_kg"] = None
    if label is not None:
        summary["label"] = label
    return summary


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
        include_measures=False,
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
            ],
        },
        "interpretation": {
            "population_estimates": False,
            "survey_weights_applied": False,
            "s2q39_unit_confirmed": False,
            "s2q39_note": "Reported values are shown without a unit; the unit is unconfirmed.",
        },
        "overall": overall,
        "by_season": season_rows,
        "by_province": province_rows,
        "by_crop": crop_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a coarse aggregate dashboard candidate for disclosure review."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    payload = build_public_dashboard_candidate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Wrote aggregate review candidate to {args.output}. "
        "It is not approved for public release."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
