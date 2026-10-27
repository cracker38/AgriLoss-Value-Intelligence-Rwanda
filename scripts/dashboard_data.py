from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dataset" / "nisrdataset"
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
