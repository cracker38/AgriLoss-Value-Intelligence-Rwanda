"""Tests for the local, raw SQLite staging import."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.ingest_sas_2024 import IngestionError, ingest_directory


def _source_dir(tmp_path: Path, rows: list[dict[str, object]]) -> tuple[Path, Path]:
    data_dir = tmp_path / "source"
    data_dir.mkdir()
    source = data_dir / "seasonA_production.json"
    source.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return data_dir, source


def _stored_rows(database: Path) -> list[tuple[int, dict[str, object]]]:
    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            "SELECT row_number, json_payload FROM raw_records ORDER BY row_number"
        ).fetchall()
    return [(row_number, json.loads(payload)) for row_number, payload in rows]


def test_import_preserves_raw_values_and_source_provenance(tmp_path: Path) -> None:
    rows = [
        {"id": "1", "quantity": "0", "blank": "", "crop": "beans, dried"},
        {"id": "2", "quantity": "", "blank": None, "crop": "maize"},
    ]
    data_dir, _ = _source_dir(tmp_path, rows)
    database = tmp_path / "artifacts" / "staging.sqlite"

    result = ingest_directory(data_dir, database, expected_file_count=1)

    assert result["imported_rows"] == 2
    assert result["skipped_rows"] == 0
    assert _stored_rows(database) == [(1, rows[0]), (2, rows[1])]
    with sqlite3.connect(database) as connection:
        metadata = connection.execute(
            "SELECT source_file, size_bytes, record_count, length(sha256) "
            "FROM source_files"
        ).fetchone()
    assert metadata == ("seasonA_production.json", len(json.dumps(rows).encode("utf-8")), 2, 64)


def test_unchanged_source_is_skipped_on_repeat_run(tmp_path: Path) -> None:
    data_dir, _ = _source_dir(tmp_path, [{"id": "1", "quantity": "0"}])
    database = tmp_path / "staging.sqlite"

    first = ingest_directory(data_dir, database, expected_file_count=1)
    second = ingest_directory(data_dir, database, expected_file_count=1)

    assert len(first["imported"]) == 1
    assert second["imported"] == []
    assert second["skipped"] == [{"file": "seasonA_production.json", "rows": 1}]
    assert _stored_rows(database) == [(1, {"id": "1", "quantity": "0"})]


def test_changed_source_replaces_its_rows(tmp_path: Path) -> None:
    data_dir, source = _source_dir(tmp_path, [{"id": "1", "quantity": "5"}])
    database = tmp_path / "staging.sqlite"
    ingest_directory(data_dir, database, expected_file_count=1)
    source.write_text(json.dumps([{"id": "1", "quantity": "7"}]), encoding="utf-8")

    result = ingest_directory(data_dir, database, expected_file_count=1)

    assert result["imported_rows"] == 1
    assert _stored_rows(database) == [(1, {"id": "1", "quantity": "7"})]


def test_invalid_replacement_rolls_back_and_preserves_previous_rows(tmp_path: Path) -> None:
    data_dir, source = _source_dir(tmp_path, [{"id": "1", "quantity": "5"}])
    database = tmp_path / "staging.sqlite"
    ingest_directory(data_dir, database, expected_file_count=1)
    source.write_text('[{"id":"2","quantity":"6"},]', encoding="utf-8")

    with pytest.raises(IngestionError, match="trailing comma"):
        ingest_directory(data_dir, database, expected_file_count=1)

    assert _stored_rows(database) == [(1, {"id": "1", "quantity": "5"})]


def test_rejects_schema_drift_without_committing_partial_rows(tmp_path: Path) -> None:
    data_dir, source = _source_dir(tmp_path, [{"id": "1", "quantity": "5"}])
    database = tmp_path / "staging.sqlite"
    ingest_directory(data_dir, database, expected_file_count=1)
    source.write_text(
        '[{"id":"2","quantity":"6"},{"id":"3","other":"7"}]',
        encoding="utf-8",
    )

    with pytest.raises(IngestionError, match="schema differs at record 2"):
        ingest_directory(data_dir, database, expected_file_count=1)

    assert _stored_rows(database) == [(1, {"id": "1", "quantity": "5"})]


def test_requires_expected_source_file_count(tmp_path: Path) -> None:
    data_dir, _ = _source_dir(tmp_path, [{"id": "1"}])

    with pytest.raises(IngestionError, match="Expected 12 JSON files"):
        ingest_directory(data_dir, tmp_path / "staging.sqlite")


def test_database_must_be_outside_source_directory(tmp_path: Path) -> None:
    data_dir, _ = _source_dir(tmp_path, [{"id": "1"}])

    with pytest.raises(IngestionError, match="outside the source directory"):
        ingest_directory(data_dir, data_dir / "staging.sqlite", expected_file_count=1)
