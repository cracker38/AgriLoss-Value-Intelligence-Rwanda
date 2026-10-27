from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dataset" / "nisrdataset"
PUBLIC_DASHBOARD_PATH = ROOT / "public_data" / "dashboard_aggregates.json"
SEASONS = ("A", "B", "C")


def load_production_data(seasons: Iterable[str] = SEASONS) -> pd.DataFrame:
    """Load production extracts for dashboard aggregation, never returning them to users."""
    frames: list[pd.DataFrame] = []
    for season in seasons:
        if season not in SEASONS:
            raise ValueError(f"Unsupported season: {season}")
        source_path = DATA_DIR / f"sas_2024_season{season}_production.json"
        if not source_path.is_file():
            raise FileNotFoundError(f"Required production extract is missing: {source_path}")
        with source_path.open("r", encoding="utf-8") as source:
            rows = json.load(source)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"{source_path} must contain a JSON array of records")
        frame = pd.DataFrame.from_records(rows)
        frame["season"] = season
        frames.append(frame)

    if not frames:
        raise ValueError("Select at least one season")

    data = pd.concat(frames, ignore_index=True, sort=False)
    for column in data.select_dtypes(include="object").columns:
        data[column] = data[column].replace("", float("nan"))
    for column in ("s2q39", "s2q21", "s2q2", "s1q9"):
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def load_public_dashboard_data(path: Path = PUBLIC_DASHBOARD_PATH) -> dict:
    """Load an approved aggregate release without loading respondent-level rows."""
    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError("Public dashboard data must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported public dashboard data schema")
    if payload.get("release_status") != "approved":
        raise ValueError("The aggregate release has not been marked approved")

    review = payload.get("review")
    if not isinstance(review, dict) or review.get("status") != "approved":
        raise ValueError("The aggregate release does not include an approval record")
    for field in ("reviewed_by", "reviewed_on", "reference"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise ValueError(f"The aggregate release approval is missing {field}")

    for section in ("overall", "by_season", "by_province", "by_crop"):
        if section not in payload:
            raise ValueError(f"Public dashboard data is missing {section}")
    for section in ("by_season", "by_province", "by_crop"):
        if not isinstance(payload[section], list):
            raise ValueError(f"Public dashboard section {section} must be a list")
    if not isinstance(payload["overall"], dict):
        raise ValueError("Public dashboard section overall must be an object")

    required_fields = {
        "overall": {
            "records",
            "distinct_crop_values",
            "loss_reported_records",
            "positive_reported_loss_records",
            "positive_reported_loss_share",
            "median_reported_harvest_kg",
        },
        "by_season": {
            "season",
            "records",
            "distinct_crop_values",
            "loss_reported_records",
            "positive_reported_loss_records",
            "loss_missing_records",
        },
        "by_province": {"province", "records"},
        "by_crop": {
            "crop",
            "records",
            "loss_reported_records",
            "positive_reported_loss_share",
            "median_reported_harvest_kg",
            "median_reported_loss_value",
        },
    }
    for section, fields in required_fields.items():
        values = [payload[section]] if section == "overall" else payload[section]
        for index, value in enumerate(values):
            if not isinstance(value, dict):
                raise ValueError(f"Public dashboard {section} entry {index} must be an object")
            missing = fields.difference(value)
            if missing:
                raise ValueError(
                    f"Public dashboard {section} entry {index} is missing: {sorted(missing)}"
                )
    return payload


def filter_production_data(
    data: pd.DataFrame,
    *,
    seasons: Iterable[str] | None = None,
    provinces: Iterable[str] | None = None,
    crops: Iterable[str] | None = None,
) -> pd.DataFrame:
    filtered = data
    for column, selected in (
        ("season", seasons),
        ("s1q1", provinces),
        ("s2q4", crops),
    ):
        if selected is not None:
            filtered = filtered[filtered[column].isin(list(selected))]
    return filtered


def available_values(data: pd.DataFrame, column: str) -> list[str]:
    if column not in data:
        return []
    return sorted(data[column].dropna().astype(str).unique().tolist())
