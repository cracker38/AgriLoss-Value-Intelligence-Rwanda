"""Pytest coverage for the standard-library SAS 2024 source audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.audit_sas_2024 import (
    AuditError,
    audit_dataset_file,
    audit_production_screening_linkage,
    compare_json_csv,
    iter_json_array,
)


def test_reads_json_array_across_small_chunks(tmp_path: Path) -> None:
    path = tmp_path / "rows.json"
    path.write_text('[ {"id":"1"}, {"id":"2"} ]', encoding="utf-8")

    assert list(iter_json_array(path, chunk_size=5)) == [{"id": "1"}, {"id": "2"}]


def test_rejects_non_array_root(tmp_path: Path) -> None:
    path = tmp_path / "rows.json"
    path.write_text('{"id":"1"}', encoding="utf-8")

    with pytest.raises(AuditError, match="top-level JSON array"):
        list(iter_json_array(path))


def test_rejects_trailing_comma(tmp_path: Path) -> None:
    path = tmp_path / "rows.json"
    path.write_text('[{"id":"1"},]', encoding="utf-8")

    with pytest.raises(AuditError, match="trailing comma"):
        list(iter_json_array(path))


def test_rejects_schema_drift_with_record_number(tmp_path: Path) -> None:
    path = tmp_path / "sas_production.json"
    path.write_text('[{"id":"1","value":"0"},{"id":"2","extra":"x"}]', encoding="utf-8")

    with pytest.raises(AuditError, match="record 2"):
        audit_dataset_file(path, path.name)


def test_counts_blank_zero_null_and_non_string_values_separately(tmp_path: Path) -> None:
    path = tmp_path / "sas_production.json"
    rows = [
        {"id": "1", "quantity": "0"},
        {"id": "2", "quantity": ""},
        {"id": "3", "quantity": None},
        {"id": "4", "quantity": 4},
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")

    inventory, quality, checks = audit_dataset_file(path, path.name)
    quantity = next(item for item in quality if item["field"] == "quantity")

    assert inventory["rows"] == 4
    assert quantity["empty_string_count"] == 1
    assert quantity["json_null_count"] == 1
    assert quantity["numeric_parse_count"] == 2
    assert quantity["numeric_parse_min"] == "0"
    assert quantity["numeric_parse_max"] == "4"
    assert checks["json_null_value_count"] == 1
    assert checks["non_string_value_count"] == 1


def test_identifies_duplicate_rows_without_treating_id_as_a_join_key(tmp_path: Path) -> None:
    path = tmp_path / "sas_screening.json"
    path.write_text('[{"id":"1","value":"a"},{"id":"2","value":"a"}]', encoding="utf-8")

    _, _, checks = audit_dataset_file(path, path.name)

    assert checks["duplicate_id_count"] == 0
    assert checks["duplicate_rows_ignoring_id_count"] == 1


def test_checks_csv_mirror_headers_rows_and_quoted_values(tmp_path: Path) -> None:
    json_path = tmp_path / "production.json"
    csv_path = tmp_path / "production.csv"
    rows = [
        {"id": "1", "crop": "bean, dried", "quantity": "0"},
        {"id": "2", "crop": 'maize "white"', "quantity": ""},
    ]
    json_path.write_text(json.dumps(rows), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(rows[0].keys())
        writer.writerows([[row[key] for key in rows[0]] for row in rows])

    result = compare_json_csv(json_path, csv_path, tmp_path)

    assert result["matches"] is True
    assert result["compared_rows"] == 2
    assert result["cell_mismatches"] == 0


def test_reports_csv_cell_mismatch(tmp_path: Path) -> None:
    json_path = tmp_path / "production.json"
    csv_path = tmp_path / "production.csv"
    json_path.write_text('[{"id":"1","quantity":"5"}]', encoding="utf-8")
    csv_path.write_text("id,quantity\n1,6\n", encoding="utf-8")

    result = compare_json_csv(json_path, csv_path, tmp_path)

    assert result["matches"] is False
    assert result["cell_mismatches"] == 1


def test_checks_production_record_grain(tmp_path: Path) -> None:
    path = tmp_path / "sas_production.json"
    rows = [
        {"id": "1", "Segment_ID": "S1", "s2q1": "P1", "s2q4": "Beans"},
        {"id": "2", "Segment_ID": "S1", "s2q1": "P1", "s2q4": "Beans"},
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")

    _, _, checks = audit_dataset_file(path, path.name)

    assert checks["duplicate_production_key_count"] == 1


def test_reports_crop_area_formula_and_candidate_linkage(tmp_path: Path) -> None:
    production_path = tmp_path / "production.json"
    screening_path = tmp_path / "screening.json"
    production_rows = [
        {"Segment_ID": "S1", "s2q1": "P1", "s2q4": "Maize", "plot_weight": "2"},
        {"Segment_ID": "S1", "s2q1": "P1", "s2q4": "Beans", "plot_weight": "3"},
        {"Segment_ID": "S1", "s2q1": "P2", "s2q4": "Rice", "plot_weight": "5"},
    ]
    screening_rows = [
        {
            "Segment_ID": "S1",
            "s2q1": "P1",
            "s3q1": "Maize",
            "plot_weight": "2",
            "Plot_size_ha": "1",
            "s3q2_1": "50",
            "crop_area": "0.5",
        },
        {
            "Segment_ID": "S1",
            "s2q1": "P1",
            "s3q1": "Maize",
            "plot_weight": "2",
            "Plot_size_ha": "1",
            "s3q2_1": "50",
            "crop_area": "0.5",
        },
        {
            "Segment_ID": "S1",
            "s2q1": "P1",
            "s3q1": "Beans",
            "plot_weight": "4",
            "Plot_size_ha": "1",
            "s3q2_1": "25",
            "crop_area": "0.25",
        },
        {
            "Segment_ID": "S1",
            "s2q1": "P2",
            "s3q1": "Rice",
            "plot_weight": "5",
            "Plot_size_ha": "2",
            "s3q2_1": "50",
            "crop_area": "1.001",
        },
        {
            "Segment_ID": "S1",
            "s2q1": "P3",
            "s3q1": "",
            "plot_weight": "",
            "Plot_size_ha": "",
            "s3q2_1": "",
            "crop_area": "",
        },
    ]
    production_path.write_text(json.dumps(production_rows), encoding="utf-8")
    screening_path.write_text(json.dumps(screening_rows), encoding="utf-8")

    result = audit_production_screening_linkage(
        production_path, screening_path, "A", root=tmp_path
    )

    assert result["production_rows"] == 3
    assert result["production_unique_plot_keys"] == 2
    assert result["production_plot_keys_matching_screening"] == 2
    assert result["screening_duplicate_plot_key_rows"] == 2
    assert result["candidate_crop_key_matched_rows"] == 2
    assert result["screening_duplicate_candidate_crop_key_rows"] == 1
    assert result["matched_rows_with_plot_weight_mismatch"] == 1
    assert result["crop_area_rows_with_all_inputs"] == 4
    assert result["crop_area_formula_mismatch_count"] == 1


def test_rejects_unsupported_linkage_season(tmp_path: Path) -> None:
    production_path = tmp_path / "production.json"
    screening_path = tmp_path / "screening.json"
    production_path.write_text("[]", encoding="utf-8")
    screening_path.write_text("[]", encoding="utf-8")

    with pytest.raises(AuditError, match="Unsupported SAS season"):
        audit_production_screening_linkage(production_path, screening_path, "D")


def test_uses_capitalized_crop_area_for_season_c(tmp_path: Path) -> None:
    production_path = tmp_path / "production.json"
    screening_path = tmp_path / "screening.json"
    production_path.write_text(
        '[{"Segment_ID":"S1","s2q1":"P1","s2q4":"Maize","plot_weight":"2"}]',
        encoding="utf-8",
    )
    screening_path.write_text(
        '[{"Segment_ID":"S1","s2q1":"P1","s3q1":"Maize","plot_weight":"2",'
        '"Plot_size_ha":"0.5","s3q2_1":"50","Crop_Area":"0.25"}]',
        encoding="utf-8",
    )

    result = audit_production_screening_linkage(
        production_path, screening_path, "C", root=tmp_path
    )

    assert result["crop_area_field"] == "Crop_Area"
    assert result["crop_area_rows_with_all_inputs"] == 1
    assert result["crop_area_formula_mismatch_count"] == 0
    assert result["candidate_crop_key_matched_rows"] == 1
