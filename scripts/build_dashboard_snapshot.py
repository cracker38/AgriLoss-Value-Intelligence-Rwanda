from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dataset" / "nisrdataset"
OUTPUT_PATH = ROOT / "artifacts" / "dashboard_snapshot.json"


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        text = str(value).strip().replace(",", "")
        return float(text)
    except (TypeError, ValueError):
        return None


def season_file(season: str) -> Path:
    return DATA_DIR / f"sas_2024_season{season}_production.json"


def build_snapshot() -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    crop_counts: Counter[str] = Counter()
    province_counts: Counter[str] = Counter()
    loss_values: list[float] = []
    total_records = 0

    for season in ("A", "B", "C"):
        file_path = season_file(season)
        if not file_path.exists():
            continue

        with file_path.open("r", encoding="utf-8") as source:
            rows = json.load(source)

        if not rows:
            continue

        df = pd.DataFrame(rows)
        total_records += len(df)

        crop_column = df["s2q4"] if "s2q4" in df.columns else df["CropCategory"]
        crop_counts.update(
            (value if isinstance(value, str) and value.strip() else "Unknown")
            for value in crop_column.fillna("Unknown").tolist()
        )

        province_series = df["s1q1"] if "s1q1" in df.columns else pd.Series(["Unknown"] * len(df))
        province_counts.update(
            (value if isinstance(value, str) and value.strip() else "Unknown")
            for value in province_series.fillna("Unknown").tolist()
        )

        loss_series = df["s2q39"] if "s2q39" in df.columns else pd.Series([None] * len(df))
        for value in loss_series.tolist():
            numeric = to_float(value)
            if numeric is not None:
                loss_values.append(numeric)

        summaries.append(
            {
                "season": season,
                "records": int(len(df)),
                "crop_count": int(df["s2q4"].nunique()) if "s2q4" in df.columns else 0,
                "non_missing_loss": int(loss_series.notna().sum()) if hasattr(loss_series, "notna") else 0,
                "avg_loss_kg": round(float(pd.to_numeric(loss_series, errors="coerce").mean()), 2) if len(loss_series) else 0.0,
                "top_crop": df["s2q4"].fillna("Unknown").mode().iloc[0] if "s2q4" in df.columns and not df.empty else "Unknown",
            }
        )

    loss_average = round(sum(loss_values) / len(loss_values), 2) if loss_values else 0.0

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_records": total_records,
        "seasons_covered": [item["season"] for item in summaries],
        "season_summary": summaries,
        "top_crops": [
            {"crop": crop, "count": int(count)} for crop, count in crop_counts.most_common(10)
        ],
        "top_provinces": [
            {"province": province, "count": int(count)} for province, count in province_counts.most_common(8)
        ],
        "loss_summary": {
            "count": len(loss_values),
            "avg_kg": loss_average,
            "min_kg": round(min(loss_values), 2) if loss_values else 0.0,
            "max_kg": round(max(loss_values), 2) if loss_values else 0.0,
        },
        "quality_notes": [
            "Values are aggregated and public-safe.",
            "The dashboard does not expose raw respondent-level microdata.",
            "Loss values are shown as descriptive observations, not national estimates.",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    build_snapshot()
