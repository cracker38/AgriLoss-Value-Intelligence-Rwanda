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
    for column in ("s2q39", "s2q21", "s2q2", "s1q9", "s2q25", "s2q26", "s2q28", "s2q36", "s2q38", "s2q47"):
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
    status = payload.get("release_status")
    review = payload.get("review")
    if status == "approved":
        if not isinstance(review, dict) or review.get("status") != "approved":
            raise ValueError("The aggregate release does not include an approval record")
        for field in ("reviewed_by", "reviewed_on", "reference"):
            if not isinstance(review.get(field), str) or not review[field].strip():
                raise ValueError(f"The aggregate release approval is missing {field}")
    elif status == "owner_authorized_unreviewed":
        authorization = payload.get("publication_authorization")
        if (
            not isinstance(authorization, dict)
            or authorization.get("authorized") is not True
            or authorization.get("review_status") != "not_recorded"
        ):
            raise ValueError("The owner-authorized release record is incomplete")
    else:
        raise ValueError("The aggregate release is not authorized for hosted display")

    for section in ("overall", "by_season", "by_province", "by_crop"):
        if section not in payload:
            raise ValueError(f"Public dashboard data is missing {section}")
    if "by_storage_facility" in payload and not isinstance(payload["by_storage_facility"], list):
        raise ValueError("Public dashboard section by_storage_facility must be a list")
    optional_list_sections = (
        "by_crop_practice",
        "by_market_channel",
        "by_province_district",
    )
    for section in optional_list_sections:
        if section in payload and not isinstance(payload[section], list):
            raise ValueError(f"Public dashboard section {section} must be a list")
    if "module_linkage" in payload and not isinstance(payload["module_linkage"], dict):
        raise ValueError("Public dashboard section module_linkage must be an object")
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
            "stored_positive_records",
            "stored_positive_share",
            "storage_loss_positive_records",
            "transformed_positive_records",
            "transformed_positive_share",
            "sold_positive_records",
            "sold_positive_share",
        },
        "by_season": {
            "season",
            "records",
            "distinct_crop_values",
            "loss_reported_records",
            "positive_reported_loss_records",
            "loss_missing_records",
            "stored_positive_records",
            "transformed_positive_records",
            "sold_positive_records",
        },
        "by_province": {"province", "records"},
        "by_crop": {
            "crop",
            "records",
            "loss_reported_records",
            "positive_reported_loss_share",
            "median_reported_harvest_kg",
            "median_reported_loss_value",
            "stored_positive_share",
            "storage_loss_positive_share",
            "transformed_positive_share",
            "sold_positive_share",
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
    optional_required_fields = {
        "by_crop_practice": {
            "crop",
            "practice_field",
            "practice",
            "status",
            "records",
            "stored_positive_share",
            "storage_loss_positive_share",
            "transformed_positive_share",
            "sold_positive_share",
        },
        "by_market_channel": {
            "market_channel",
            "production_records",
            "valid_sales_records",
            "positive_sales_records",
            "positive_sales_share",
            "median_positive_sales_kg",
            "positive_price_records",
            "median_positive_price_rwf_per_kg",
        },
        "by_province_district": {
            "province",
            "district",
            "records",
            "positive_reported_loss_share",
            "stored_positive_share",
            "transformed_positive_share",
            "sold_positive_share",
        },
    }
    for section, fields in optional_required_fields.items():
        for index, value in enumerate(payload.get(section, [])):
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
