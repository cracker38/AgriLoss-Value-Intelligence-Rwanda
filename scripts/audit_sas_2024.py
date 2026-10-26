"""Audit the local NISR SAS 2024 extracts without changing source data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator, TextIO


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "dataset" / "nisrdataset"
DEFAULT_MIRROR = ROOT / "dataset" / "publicdataset" / "sas_2024_seasonB_production.csv"
DEFAULT_SCHEMA_OUTPUT = ROOT / "docs" / "schema-inventory.json"
DEFAULT_QUALITY_OUTPUT = ROOT / "docs" / "field-quality-summary.csv"
DEFAULT_CHECKS_OUTPUT = ROOT / "docs" / "data-quality-checks.json"
CSV_FIELDS = (
    "file",
    "record_count",
    "field",
    "empty_string_count",
    "empty_string_percent",
    "json_null_count",
    "nonempty_count",
    "numeric_parse_count",
    "nonnumeric_nonempty_count",
    "numeric_parse_min",
    "numeric_parse_max",
    "distinct_nonempty_values",
)


class AuditError(ValueError):
    """Raised when a source file cannot be audited safely."""


def _read_more(
    buffer: str, position: int, source: TextIO, chunk_size: int
) -> tuple[str, int, bool]:
    """Discard consumed text and read another chunk from a JSON source."""
    remaining = buffer[position:]
    chunk = source.read(chunk_size)
    return remaining + chunk, 0, not chunk


def iter_json_array(path: Path, chunk_size: int = 64 * 1024) -> Iterator[Any]:
    """Yield values from a top-level JSON array while keeping memory bounded."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        buffer = ""
        position = 0
        eof = False

        def skip_whitespace() -> bool:
            nonlocal buffer, position, eof
            while True:
                while position < len(buffer) and buffer[position].isspace():
                    position += 1
                if position < len(buffer):
                    return True
                if eof:
                    return False
                buffer, position, eof = _read_more(buffer, position, source, chunk_size)

        if not skip_whitespace() or buffer[position] != "[":
            raise AuditError(f"{path}: expected a top-level JSON array")
        position += 1
        expecting_value = True
        has_value = False

        while True:
            if not skip_whitespace():
                raise AuditError(f"{path}: JSON array is missing its closing bracket")

            marker = buffer[position]
            if marker == "]":
                if expecting_value and has_value:
                    raise AuditError(f"{path}: trailing comma before the closing bracket")
                position += 1
                if skip_whitespace():
                    raise AuditError(f"{path}: unexpected data after the JSON array")
                return

            if marker == ",":
                if expecting_value:
                    raise AuditError(f"{path}: unexpected comma in JSON array")
                position += 1
                expecting_value = True
                continue

            if not expecting_value:
                raise AuditError(f"{path}: expected a comma between array items")

            while True:
                try:
                    value, end = decoder.raw_decode(buffer, position)
                    break
                except json.JSONDecodeError as error:
                    if eof:
                        raise AuditError(
                            f"{path}: invalid JSON near character {position}: {error.msg}"
                        ) from error
                    buffer, position, eof = _read_more(buffer, position, source, chunk_size)

            yield value
            position = end
            expecting_value = False
            has_value = True


def _empty_field_stats() -> dict[str, Any]:
    return {
        "empty": 0,
        "null": 0,
        "nonempty": 0,
        "numeric": 0,
        "minimum": None,
        "maximum": None,
        "distinct": set(),
    }


def _numeric_value(value: str) -> Decimal | None:
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() else None


def _decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_dataset_file(path: Path, relative_name: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Summarize one flat-object JSON extract and validate its basic structure."""
    fields: dict[str, dict[str, Any]] = {}
    column_order: list[str] | None = None
    row_count = 0
    null_value_count = 0
    non_string_value_count = 0
    duplicate_id_count = 0
    duplicate_rows_ignoring_id = 0
    duplicate_production_keys = 0
    seen_ids: set[str] = set()
    seen_rows: set[str] = set()
    seen_production_keys: set[tuple[str, str, str]] = set()

    for row_number, row in enumerate(iter_json_array(path), start=1):
        if not isinstance(row, dict):
            raise AuditError(f"{path}: record {row_number} is not a JSON object")

        row_columns = list(row)
        if column_order is None:
            column_order = row_columns
            fields = {name: _empty_field_stats() for name in column_order}
        elif row_columns != column_order:
            raise AuditError(
                f"{path}: schema differs at record {row_number}; "
                "object keys or their order do not match the first record"
            )

        row_count += 1
        for name, raw_value in row.items():
            summary = fields[name]
            if raw_value is None:
                summary["null"] += 1
                null_value_count += 1
                continue

            if not isinstance(raw_value, str):
                non_string_value_count += 1
            value = raw_value if isinstance(raw_value, str) else str(raw_value)
            if value == "":
                summary["empty"] += 1
                continue

            summary["nonempty"] += 1
            summary["distinct"].add(value)
            numeric = _numeric_value(value)
            if numeric is not None:
                summary["numeric"] += 1
                if summary["minimum"] is None or numeric < summary["minimum"]:
                    summary["minimum"] = numeric
                if summary["maximum"] is None or numeric > summary["maximum"]:
                    summary["maximum"] = numeric

        if "id" in row:
            identifier = str(row["id"])
            if identifier in seen_ids:
                duplicate_id_count += 1
            seen_ids.add(identifier)

        signature_values = [(key, row[key]) for key in row_columns if key != "id"]
        signature = json.dumps(signature_values, ensure_ascii=False, separators=(",", ":"))
        row_digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()
        if row_digest in seen_rows:
            duplicate_rows_ignoring_id += 1
        seen_rows.add(row_digest)

        production_key_fields = ("Segment_ID", "s2q1", "s2q4")
        if all(name in row for name in production_key_fields) and "production" in path.name:
            production_key = tuple(str(row[name]) for name in production_key_fields)
            if production_key in seen_production_keys:
                duplicate_production_keys += 1
            seen_production_keys.add(production_key)

    if column_order is None:
        raise AuditError(f"{path}: JSON array is empty; no schema can be inferred")

    quality_rows: list[dict[str, Any]] = []
    for name in column_order:
        summary = fields[name]
        quality_rows.append(
            {
                "file": Path(relative_name).name,
                "record_count": row_count,
                "field": name,
                "empty_string_count": summary["empty"],
                "empty_string_percent": f"{summary['empty'] / row_count * 100:.4f}",
                "json_null_count": summary["null"],
                "nonempty_count": summary["nonempty"],
                "numeric_parse_count": summary["numeric"],
                "nonnumeric_nonempty_count": summary["nonempty"] - summary["numeric"],
                "numeric_parse_min": _decimal_text(summary["minimum"]),
                "numeric_parse_max": _decimal_text(summary["maximum"]),
                "distinct_nonempty_values": len(summary["distinct"]),
            }
        )

    inventory = {
        "file": relative_name.replace("\\", "/"),
        "rows": row_count,
        "columns": len(column_order),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "ordered_columns": column_order,
    }
    checks = {
        "file": relative_name.replace("\\", "/"),
        "rows": row_count,
        "columns": len(column_order),
        "json_null_value_count": null_value_count,
        "non_string_value_count": non_string_value_count,
        "duplicate_id_count": duplicate_id_count,
        "duplicate_rows_ignoring_id_count": duplicate_rows_ignoring_id,
        "duplicate_production_key_count": duplicate_production_keys if "production" in path.name else None,
    }
    return inventory, quality_rows, checks


def _record_key(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[str, ...] | None:
    """Build a candidate key only when every component is populated."""
    raw_values = tuple(row.get(field, "") for field in fields)
    if any(value is None for value in raw_values):
        return None
    values = tuple(str(value) for value in raw_values)
    if any(not value.strip() for value in values):
        return None
    return values


def audit_production_screening_linkage(
    production_path: Path,
    screening_path: Path,
    season: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Report crop-area arithmetic and diagnostic production-screening key coverage."""
    normalized_season = season.upper()
    if normalized_season not in {"A", "B", "C"}:
        raise AuditError(f"Unsupported SAS season {season!r}; expected A, B, or C")

    area_field = "Crop_Area" if normalized_season == "C" else "crop_area"
    area_tolerance = Decimal("0.0005")
    area_input_count = 0
    area_mismatch_count = 0
    max_area_difference: Decimal | None = None
    screening_rows = 0
    screening_rows_with_plot_keys = 0
    screening_plot_keys: set[tuple[str, ...]] = set()
    screening_crop_key_weights: dict[tuple[str, ...], list[str]] = {}

    for row in iter_json_array(screening_path):
        if not isinstance(row, dict):
            raise AuditError(f"{screening_path}: screening record is not a JSON object")
        screening_rows += 1

        plot_size = _numeric_value(str(row.get("Plot_size_ha", "")))
        crop_share = _numeric_value(str(row.get("s3q2_1", "")))
        crop_area = _numeric_value(str(row.get(area_field, "")))
        if plot_size is not None and crop_share is not None and crop_area is not None:
            area_input_count += 1
            difference = abs(crop_area - (plot_size * crop_share / Decimal("100")))
            if max_area_difference is None or difference > max_area_difference:
                max_area_difference = difference
            if difference > area_tolerance:
                area_mismatch_count += 1

        plot_key = _record_key(row, ("Segment_ID", "s2q1"))
        if plot_key is not None:
            screening_rows_with_plot_keys += 1
            screening_plot_keys.add(plot_key)

        crop_key = _record_key(row, ("Segment_ID", "s2q1", "s3q1"))
        if crop_key is not None:
            screening_crop_key_weights.setdefault(crop_key, []).append(
                str(row.get("plot_weight", ""))
            )

    screening_duplicate_crop_key_rows = sum(
        len(weights) - 1 for weights in screening_crop_key_weights.values() if len(weights) > 1
    )
    production_plot_keys: set[tuple[str, ...]] = set()
    production_rows = 0
    candidate_crop_matches = 0
    matched_weight_mismatches = 0
    for row in iter_json_array(production_path):
        if not isinstance(row, dict):
            raise AuditError(f"{production_path}: production record is not a JSON object")
        production_rows += 1

        plot_key = _record_key(row, ("Segment_ID", "s2q1"))
        if plot_key is not None:
            production_plot_keys.add(plot_key)

        crop_key = _record_key(row, ("Segment_ID", "s2q1", "s2q4"))
        if crop_key is None:
            continue
        candidate_weights = screening_crop_key_weights.get(crop_key)
        if candidate_weights is None:
            continue
        candidate_crop_matches += 1
        production_weight = str(row.get("plot_weight", ""))
        if any(weight != production_weight for weight in candidate_weights):
            matched_weight_mismatches += 1

    plot_key_matches = len(production_plot_keys & screening_plot_keys)
    match_percent = (
        candidate_crop_matches / production_rows * 100 if production_rows else 0.0
    )
    return {
        "season": normalized_season,
        "production_file": _relative_name(production_path, root),
        "screening_file": _relative_name(screening_path, root),
        "candidate_join_fields": {
            "production": ["Segment_ID", "s2q1", "s2q4"],
            "screening": ["Segment_ID", "s2q1", "s3q1"],
        },
        "production_rows": production_rows,
        "production_unique_plot_keys": len(production_plot_keys),
        "production_plot_keys_matching_screening": plot_key_matches,
        "screening_rows": screening_rows,
        "screening_rows_with_plot_keys": screening_rows_with_plot_keys,
        "screening_unique_plot_keys": len(screening_plot_keys),
        "screening_duplicate_plot_key_rows": (
            screening_rows_with_plot_keys - len(screening_plot_keys)
        ),
        "candidate_crop_key_matched_rows": candidate_crop_matches,
        "candidate_crop_key_match_percent": f"{match_percent:.4f}",
        "screening_duplicate_candidate_crop_key_rows": screening_duplicate_crop_key_rows,
        "matched_rows_with_plot_weight_mismatch": matched_weight_mismatches,
        "crop_area_field": area_field,
        "crop_area_formula": "Plot_size_ha * s3q2_1 / 100",
        "crop_area_rows_with_all_inputs": area_input_count,
        "crop_area_formula_tolerance_ha": _decimal_text(area_tolerance),
        "crop_area_formula_mismatch_count": area_mismatch_count,
        "crop_area_formula_max_abs_difference_ha": _decimal_text(max_area_difference),
    }


def _relative_name(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def compare_json_csv(json_path: Path, csv_path: Path, root: Path = ROOT) -> dict[str, Any]:
    """Check whether a CSV mirror exactly represents its JSON source."""
    json_rows = iter_json_array(json_path)
    reader: Iterator[list[str]]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = iter(csv.reader(source))
        try:
            header = next(reader)
        except StopIteration:
            return {
                "file": _relative_name(csv_path, root),
                "json_source": _relative_name(json_path, root),
                "header_matches": False,
                "json_rows": 0,
                "csv_rows": 0,
                "compared_rows": 0,
                "cell_mismatches": 0,
                "matches": False,
            }

        expected_columns: list[str] | None = None
        first_row = next(json_rows, None)
        if first_row is not None:
            expected_columns = list(first_row)
        header_matches = header == expected_columns
        compared_rows = 0
        cell_mismatches = 0
        json_count = 0
        csv_count = 1

        def compare_row(row: Any, csv_row: list[str] | None) -> None:
            nonlocal compared_rows, cell_mismatches
            if csv_row is None:
                return
            compared_rows += 1
            if not isinstance(row, dict) or list(row) != expected_columns or csv_row != [str(row[key]) for key in expected_columns or []]:
                cell_mismatches += 1

        if first_row is not None:
            json_count = 1
            csv_row = next(reader, None)
            if csv_row is not None:
                csv_count += 1
            compare_row(first_row, csv_row)
        for row in json_rows:
            json_count += 1
            csv_row = next(reader, None)
            if csv_row is not None:
                csv_count += 1
            compare_row(row, csv_row)

        for _ in reader:
            csv_count += 1

        return {
            "file": _relative_name(csv_path, root),
            "json_source": _relative_name(json_path, root),
            "header_matches": header_matches,
            "json_rows": json_count,
            "csv_rows": csv_count - 1,
            "compared_rows": compared_rows,
            "cell_mismatches": cell_mismatches,
            "matches": header_matches and json_count == csv_count - 1 and cell_mismatches == 0,
        }


def audit_sources(data_dir: Path, mirror_csv: Path, root: Path = ROOT) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Audit all NISR JSON files and the duplicate Season B production CSV."""
    json_files = sorted(data_dir.glob("*.json"))
    if len(json_files) != 12:
        raise AuditError(f"Expected 12 NISR JSON files in {data_dir}, found {len(json_files)}")

    inventory_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    dataset_checks: list[dict[str, Any]] = []
    for path in json_files:
        relative_name = str(path.relative_to(root)) if path.is_relative_to(root) else path.name
        inventory, fields, checks = audit_dataset_file(path, relative_name)
        inventory_rows.append(inventory)
        quality_rows.extend(fields)
        dataset_checks.append(checks)

    mirror_source = data_dir / "sas_2024_seasonB_production.json"
    if not mirror_source.is_file() or not mirror_csv.is_file():
        raise AuditError(f"Expected JSON/CSV mirror pair: {mirror_source} and {mirror_csv}")
    mirror_check = compare_json_csv(mirror_source, mirror_csv, root)
    production_screening_linkage = [
        audit_production_screening_linkage(
            data_dir / f"sas_2024_season{season}_production.json",
            data_dir / f"sas_2024_season{season}_screening.json",
            season,
            root,
        )
        for season in ("A", "B", "C")
    ]
    checks_document = {
        "generated_from": "dataset/nisrdataset/*.json",
        "dataset_checks": dataset_checks,
        "season_b_production_csv_mirror": mirror_check,
        "production_screening_linkage_diagnostics": production_screening_linkage,
    }
    schema_document = {
        "generated_from": "dataset/nisrdataset/*.json",
        "datasets": inventory_rows,
    }
    return schema_document, quality_rows, checks_document


def write_outputs(
    schema_document: dict[str, Any],
    quality_rows: list[dict[str, Any]],
    checks_document: dict[str, Any],
    schema_path: Path,
    quality_path: Path,
    checks_path: Path,
) -> None:
    """Write audit products as UTF-8 after the full audit has succeeded."""
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(schema_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with quality_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(quality_rows)
    checks_path.write_text(json.dumps(checks_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--mirror-csv", type=Path, default=DEFAULT_MIRROR)
    parser.add_argument("--schema-output", type=Path, default=DEFAULT_SCHEMA_OUTPUT)
    parser.add_argument("--quality-output", type=Path, default=DEFAULT_QUALITY_OUTPUT)
    parser.add_argument("--checks-output", type=Path, default=DEFAULT_CHECKS_OUTPUT)
    args = parser.parse_args(argv)

    try:
        schema_document, quality_rows, checks_document = audit_sources(args.data_dir, args.mirror_csv)
        write_outputs(
            schema_document,
            quality_rows,
            checks_document,
            args.schema_output,
            args.quality_output,
            args.checks_output,
        )
    except (AuditError, OSError, csv.Error) as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        return 1

    rows = sum(item["rows"] for item in schema_document["datasets"])
    mirror = checks_document["season_b_production_csv_mirror"]
    print(f"Audited {len(schema_document['datasets'])} JSON files and {rows:,} rows.")
    print(f"Generated: {args.schema_output}, {args.quality_output}, {args.checks_output}")
    print(f"Season B JSON/CSV mirror matches: {mirror['matches']} ({mirror['compared_rows']:,} rows).")
    for linkage in checks_document["production_screening_linkage_diagnostics"]:
        print(
            f"Season {linkage['season']}: crop-area formula mismatches "
            f"{linkage['crop_area_formula_mismatch_count']}/"
            f"{linkage['crop_area_rows_with_all_inputs']}; candidate crop-key coverage "
            f"{linkage['candidate_crop_key_match_percent']}%; plot-weight mismatches "
            f"{linkage['matched_rows_with_plot_weight_mismatch']}."
        )
    return 0 if mirror["matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
