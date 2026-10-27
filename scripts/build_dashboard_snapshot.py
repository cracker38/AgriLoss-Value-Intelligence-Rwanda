from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from scripts.dashboard_data import ROOT, load_production_data


OUTPUT_PATH = ROOT / "artifacts" / "dashboard_snapshot.json"


def build_snapshot() -> dict[str, Any]:
    data = load_production_data()
    loss = data["s2q39"]
    summaries: list[dict[str, Any]] = []

    for season, frame in data.groupby("season", sort=True):
        reported_loss = frame["s2q39"].dropna()
        summaries.append(
            {
                "season": season,
                "production_rows": int(len(frame)),
                "distinct_crops": int(frame["s2q4"].nunique()),
                "loss_reported_rows": int(reported_loss.size),
                "positive_reported_loss_rows": int(reported_loss.gt(0).sum()),
                "median_reported_loss_value": (
                    float(reported_loss.median()) if not reported_loss.empty else None
                ),
            }
        )

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "NISR SAS 2024 production JSON extracts",
        "unit_note": "The published s2q39 field has no confirmed unit; values are not labeled kg.",
        "total_production_rows": int(len(data)),
        "loss_reported_rows": int(loss.notna().sum()),
        "loss_missing_rows": int(loss.isna().sum()),
        "positive_reported_loss_rows": int(loss.gt(0).sum()),
        "season_summary": summaries,
        "quality_notes": [
            "Unweighted sample descriptions only; these are not national population estimates.",
            "Blank loss responses remain missing and are not treated as zero.",
            "Season C is included for descriptive display but excluded from model training.",
            "Respondent-level rows are not included in this snapshot.",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


if __name__ == "__main__":
    build_snapshot()
