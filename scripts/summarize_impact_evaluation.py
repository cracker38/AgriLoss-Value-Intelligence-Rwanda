from __future__ import annotations

import argparse
import csv
import math
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "impact_evaluation_summary.md"
DIMENSION_FIELDS = (
    "evidence_use_0_2",
    "scope_uncertainty_0_2",
    "follow_up_action_0_2",
    "decision_gate_0_2",
    "local_plan_0_2",
)
ERROR_FIELDS = (
    "error_positive_share_as_loss_rate",
    "error_crop_province_join",
    "error_2024_price_as_current",
    "error_sample_as_national",
    "error_process_example_as_demand_proof",
)
ERROR_LABELS = {
    "error_positive_share_as_loss_rate": "Positive-response share treated as a loss rate",
    "error_crop_province_join": "Province summary joined to selected crop",
    "error_2024_price_as_current": "2024 price treated as current",
    "error_sample_as_national": "Sample described as a national estimate",
    "error_process_example_as_demand_proof": "Process example treated as proof of demand",
}
ROLE_GROUPS = {
    "district_planner",
    "national_planner",
    "cooperative_staff",
    "extension_staff",
    "analyst",
    "other",
}
ORGANIZATION_TYPES = {
    "government",
    "cooperative",
    "research",
    "ngo_development_partner",
    "processor_buyer",
    "other",
}
SEQUENCE_ASSIGNMENTS = {
    1: {("A", "usual_source", 1), ("B", "agriloss", 2)},
    2: {("B", "agriloss", 1), ("A", "usual_source", 2)},
    3: {("A", "agriloss", 1), ("B", "usual_source", 2)},
    4: {("B", "usual_source", 1), ("A", "agriloss", 2)},
}
REQUIRED_FIELDS = {
    "participant_code",
    "role_group",
    "organization_type",
    "session_date",
    "dashboard_version_or_commit",
    "scenario_id",
    "condition",
    "sequence_id",
    "order",
    "time_seconds",
    "task_completed",
    *DIMENSION_FIELDS,
    "decision_quality_total_0_10",
    "confidence_0_100",
    "report_usefulness_1_5",
    *ERROR_FIELDS,
}


def _number(
    row: dict[str, str], field: str, *, minimum: float, maximum: float, integer: bool = False
) -> float | None:
    raw = (row.get(field) or "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"{field} must be numeric; received {raw!r}") from error
    if not math.isfinite(value) or value < minimum or value > maximum or (integer and not value.is_integer()):
        kind = "an integer " if integer else ""
        raise ValueError(f"{field} must be {kind}between {minimum:g} and {maximum:g}")
    return value


def _flag(row: dict[str, str], field: str) -> int | None:
    raw = (row.get(field) or "").strip().lower()
    if not raw:
        return None
    if raw in {"1", "yes", "true"}:
        return 1
    if raw in {"0", "no", "false"}:
        return 0
    raise ValueError(f"{field} must be 0/1 or yes/no; received {raw!r}")


def _read_sessions(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_FIELDS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Results CSV is missing columns: {sorted(missing)}")
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        profiles: dict[str, tuple[str, str, int]] = {}
        for line_number, raw in enumerate(reader, start=2):
            if None in raw:
                raise ValueError(
                    f"Row {line_number}: extra CSV values found; quote commas inside notes"
                )
            if not any((value or "").strip() for value in raw.values()):
                continue
            participant = (raw.get("participant_code") or "").strip()
            condition = (raw.get("condition") or "").strip()
            if not participant:
                raise ValueError(f"Row {line_number}: participant_code is required")
            role_group = (raw.get("role_group") or "").strip()
            organization_type = (raw.get("organization_type") or "").strip()
            if role_group not in ROLE_GROUPS:
                raise ValueError(f"Row {line_number}: role_group must use a documented category")
            if organization_type not in ORGANIZATION_TYPES:
                raise ValueError(f"Row {line_number}: organization_type must use a documented category")
            if condition not in {"usual_source", "agriloss"}:
                raise ValueError(f"Row {line_number}: condition must be usual_source or agriloss")
            identity = (participant, condition)
            if identity in seen:
                raise ValueError(
                    f"Row {line_number}: only one task per participant and condition is expected"
                )
            seen.add(identity)

            session_date = (raw.get("session_date") or "").strip()
            try:
                date.fromisoformat(session_date)
            except ValueError as error:
                raise ValueError(
                    f"Row {line_number}: session_date must use YYYY-MM-DD"
                ) from error
            scenario = (raw.get("scenario_id") or "").strip()
            if not scenario:
                raise ValueError(f"Row {line_number}: scenario_id is required")
            sequence = _number(raw, "sequence_id", minimum=1, maximum=4, integer=True)
            order = _number(raw, "order", minimum=1, maximum=2, integer=True)
            if sequence is None or order is None:
                raise ValueError(f"Row {line_number}: sequence_id and order are required")
            if (scenario, condition, int(order)) not in SEQUENCE_ASSIGNMENTS[int(sequence)]:
                raise ValueError(
                    f"Row {line_number}: scenario, condition, and order do not match sequence {int(sequence)}"
                )
            profile = (role_group, organization_type, int(sequence))
            if participant in profiles and profiles[participant] != profile:
                raise ValueError(
                    f"Row {line_number}: role, organization, and sequence must match for a participant"
                )
            profiles[participant] = profile
            version = (raw.get("dashboard_version_or_commit") or "").strip()
            if not version:
                raise ValueError(f"Row {line_number}: dashboard_version_or_commit is required")
            total_values = [
                _number(raw, field, minimum=0, maximum=2, integer=True)
                for field in DIMENSION_FIELDS
            ]
            score_total = sum(total_values) if all(value is not None for value in total_values) else None
            recorded_total = _number(
                raw, "decision_quality_total_0_10", minimum=0, maximum=10, integer=True
            )
            if recorded_total is not None and score_total is not None and recorded_total != score_total:
                raise ValueError(
                    f"Row {line_number}: decision-quality total does not match the five rubric scores"
                )
            if _flag(raw, "task_completed") is None:
                raise ValueError(f"Row {line_number}: task_completed is required")

            row: dict[str, Any] = {
                "participant": participant,
                "condition": condition,
                "role_group": role_group,
                "organization_type": organization_type,
                "scenario": scenario,
                "sequence": int(sequence),
                "order": int(order),
                "date": session_date,
                "version": version,
                "score": score_total if score_total is not None else recorded_total,
                "completed": _flag(raw, "task_completed"),
                "time": _number(raw, "time_seconds", minimum=0, maximum=86400),
                "confidence": _number(raw, "confidence_0_100", minimum=0, maximum=100),
                "report_usefulness": _number(raw, "report_usefulness_1_5", minimum=1, maximum=5),
                "errors": {field: _flag(raw, field) for field in ERROR_FIELDS},
            }
            if row["report_usefulness"] is not None and condition != "agriloss":
                raise ValueError(
                    f"Row {line_number}: report_usefulness is only recorded for the AgriLoss condition"
                )
            rows.append(row)
    if not rows:
        raise ValueError("No session rows found. Keep completed results outside the repository and pass their CSV path.")
    return rows


def _median(values: list[float]) -> str:
    return f"{median(values):.1f}" if values else "Not available"


def _condition_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Condition | Tasks | Completed | Median score / 10 | Median time (seconds) | Median confidence | Median report usefulness |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in ("usual_source", "agriloss"):
        subset = [row for row in rows if row["condition"] == condition]
        if len(subset) < 3:
            lines.append(
                f"| {condition} | Suppressed (<3) | Suppressed | Suppressed | Suppressed | Suppressed | Suppressed |"
            )
            continue
        completed = [row["completed"] for row in subset]
        score = [row["score"] for row in subset if row["score"] is not None]
        time_values = [row["time"] for row in subset if row["time"] is not None]
        confidence = [row["confidence"] for row in subset if row["confidence"] is not None]
        usefulness = [
            row["report_usefulness"]
            for row in subset
            if row["report_usefulness"] is not None
        ]
        completed_text = (
            f"{sum(completed)}/{len(completed)}"
            if completed
            else "Not available"
        )
        lines.append(
            f"| {condition} | {len(subset)} | {completed_text} | {_median(score)} | "
            f"{_median(time_values)} | {_median(confidence)} | {_median(usefulness)} |"
        )
    return "\n".join(lines)


def _group_score_table(rows: list[dict[str, Any]], key: str, label: str) -> str:
    groups = sorted({row[key] for row in rows})
    lines = ["| Group | Condition | Tasks scored | Median score / 10 |", "|---|---|---:|---:|"]
    for group in groups:
        for condition in ("usual_source", "agriloss"):
            values = [
                row["score"]
                for row in rows
                if row[key] == group
                and row["condition"] == condition
                and row["score"] is not None
            ]
            if len(values) >= 3:
                lines.append(f"| {group} | {condition} | {len(values)} | {_median(values)} |")
            else:
                lines.append(f"| {group} | {condition} | Suppressed | Suppressed (<3) |")
    return f"### By {label}\n\n" + "\n".join(lines)


def summarize(rows: list[dict[str, Any]]) -> str:
    by_participant: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_participant.setdefault(row["participant"], {})[row["condition"]] = row
    differences = [
        pair["agriloss"]["score"] - pair["usual_source"]["score"]
        for pair in by_participant.values()
        if {"agriloss", "usual_source"}.issubset(pair)
        and pair["agriloss"]["score"] is not None
        and pair["usual_source"]["score"] is not None
    ]
    error_lines = [
        "| Critical interpretation error | Observed / scored tasks |",
        "|---|---:|",
    ]
    for field in ERROR_FIELDS:
        observed = [row["errors"][field] for row in rows if row["errors"][field] is not None]
        if len(observed) >= 3:
            summary = f"{sum(observed)}/{len(observed)}"
        elif observed:
            summary = "Suppressed (<3 scored tasks)"
        else:
            summary = "Not scored"
        error_lines.append(f"| {ERROR_LABELS[field]} | {summary} |")
    if len(differences) >= 3:
        primary = (
            f"Complete participant pairs: **{len(differences)}**. Median paired score difference "
            f"(AgriLoss minus source workflow): **{median(differences):+.1f}/10** "
            f"(range {min(differences):+.1f} to {max(differences):+.1f}); "
            f"higher with AgriLoss: **{sum(value > 0 for value in differences)}**, "
            f"same: **{sum(value == 0 for value in differences)}**, "
            f"lower: **{sum(value < 0 for value in differences)}**."
        )
    else:
        primary = (
            "Fewer than three complete participant pairs have scored results; numerical paired results are suppressed."
            if differences
            else "No complete participant pairs with scored results are available yet."
        )
    dates = sorted({row["date"] for row in rows})
    period = dates[0] if dates[0] == dates[-1] else f"{dates[0]} to {dates[-1]}"
    participants = {row["participant"]: row for row in rows}
    role_counts = {
        group: sum(row["role_group"] == group for row in participants.values())
        for group in sorted(ROLE_GROUPS)
        if any(row["role_group"] == group for row in participants.values())
    }
    organization_counts = {
        group: sum(row["organization_type"] == group for row in participants.values())
        for group in sorted(ORGANIZATION_TYPES)
        if any(row["organization_type"] == group for row in participants.values())
    }
    version_list = ", ".join(sorted({row["version"] for row in rows}))
    role_text = ", ".join(
        f"{role}: {count}" for role, count in role_counts.items() if count >= 3
    ) or "No category meets the minimum display size"
    if any(count < 3 for count in role_counts.values()):
        role_text += "; small categories suppressed"
    organization_text = ", ".join(
        f"{organization}: {count}"
        for organization, count in organization_counts.items()
        if count >= 3
    ) or "No category meets the minimum display size"
    if any(count < 3 for count in organization_counts.values()):
        organization_text += "; small categories suppressed"
    return f"""# AgriLoss decision-support evaluation summary

Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

## Study record

- Session dates recorded: {period}
- Participants with coded records: {len(by_participant)}
- Role groups: {role_text}
- Organization types: {organization_text}
- Task rows: {len(rows)}
- Dashboard versions/commits used: {version_list}

## Primary descriptive result

{primary}

## Task-level measures

{_condition_table(rows)}

## Critical interpretation errors

{chr(10).join(error_lines)}

{_group_score_table(rows, "scenario", "scenario")}

{_group_score_table(rows, "sequence", "counterbalanced sequence")}

## Interpretation limit

This is a descriptive summary of a small, purposive formative study. The paired tasks use different scenarios, so score differences do not isolate a causal tool effect. Do not interpret task scores, completion, time, confidence, or report usefulness as evidence of reduced crop losses, higher incomes, or improved farmer welfare. Report all results and limitations; do not publish session-level notes or identifying information.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize anonymized AgriLoss decision-support session results."
    )
    parser.add_argument("--input", required=True, type=Path, help="Private completed results CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    rows = _read_sessions(args.input)
    report = summarize(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote aggregate evaluation summary to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
