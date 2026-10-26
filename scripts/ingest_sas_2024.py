"""Load the original SAS 2024 JSON rows into a local SQLite staging database.

This is a raw, provenance-preserving staging step. It does not normalize values,
join survey modules, or calculate indicators.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from scripts.audit_sas_2024 import AuditError, iter_json_array


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "dataset" / "nisrdataset"
DEFAULT_DATABASE = ROOT / "artifacts" / "agri_loss_sas_2024.sqlite"
SCHEMA_VERSION = 1
BATCH_SIZE = 1000


class IngestionError(ValueError):
    """Raised when source data or the staging database cannot be handled safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _initialize_database(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version not in (0, SCHEMA_VERSION):
        raise IngestionError(
            f"Unsupported SQLite schema version {version}; expected {SCHEMA_VERSION}"
        )

    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_files (
            source_file TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            record_count INTEGER NOT NULL CHECK (record_count >= 0),
            ingested_at_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS raw_records (
            source_file TEXT NOT NULL,
            row_number INTEGER NOT NULL CHECK (row_number > 0),
            json_payload TEXT NOT NULL,
            PRIMARY KEY (source_file, row_number),
            FOREIGN KEY (source_file) REFERENCES source_files(source_file)
                ON DELETE CASCADE
        );
        """
    )
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _serialized_rows(path: Path) -> Iterator[tuple[int, str]]:
    expected_columns: list[str] | None = None
    try:
        for row_number, row in enumerate(iter_json_array(path), start=1):
            if not isinstance(row, dict):
                raise IngestionError(f"{path}: record {row_number} is not a JSON object")

            columns = list(row)
            if expected_columns is None:
                expected_columns = columns
            elif columns != expected_columns:
                raise IngestionError(
                    f"{path}: schema differs at record {row_number}; "
                    "object keys or their order do not match the first record"
                )

            payload = json.dumps(
                row, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            )
            yield row_number, payload
    except AuditError as error:
        raise IngestionError(str(error)) from error
    except IngestionError:
        raise
    except (TypeError, ValueError) as error:
        raise IngestionError(
            f"{path}: data cannot be serialized as strict JSON: {error}"
        ) from error


def ingest_directory(
    data_dir: Path,
    database_path: Path,
    *,
    expected_file_count: int | None = 12,
) -> dict[str, Any]:
    """Ingest all top-level JSON files atomically and idempotently."""
    data_dir = data_dir.resolve()
    database_path = database_path.resolve()
    if not data_dir.is_dir():
        raise IngestionError(f"Source directory does not exist: {data_dir}")
    if database_path == data_dir or data_dir in database_path.parents:
        raise IngestionError("The SQLite database must be outside the source directory")

    source_paths = sorted(path for path in data_dir.glob("*.json") if path.is_file())
    if expected_file_count is not None and len(source_paths) != expected_file_count:
        raise IngestionError(
            f"Expected {expected_file_count} JSON files in {data_dir}, found {len(source_paths)}"
        )
    if not source_paths:
        raise IngestionError(f"No JSON source files found in {data_dir}")

    sources = [
        {
            "path": path,
            "source_file": path.relative_to(data_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in source_paths
    ]

    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    imported: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    try:
        _initialize_database(connection)
        with connection:
            current_files = {
                row[0] for row in connection.execute("SELECT source_file FROM source_files")
            }
            incoming_files = {item["source_file"] for item in sources}
            stale_files = sorted(current_files - incoming_files)
            if stale_files:
                names = ", ".join(stale_files)
                raise IngestionError(
                    "The database contains source files absent from this input directory: "
                    f"{names}. Use a new database to ingest a different source set."
                )

            for source in sources:
                source_name = source["source_file"]
                existing = connection.execute(
                    "SELECT sha256, size_bytes, record_count "
                    "FROM source_files WHERE source_file = ?",
                    (source_name,),
                ).fetchone()
                actual_count = connection.execute(
                    "SELECT COUNT(*) FROM raw_records WHERE source_file = ?",
                    (source_name,),
                ).fetchone()[0]

                if (
                    existing is not None
                    and existing[0] == source["sha256"]
                    and existing[1] == source["size_bytes"]
                    and existing[2] == actual_count
                ):
                    skipped.append({"file": source_name, "rows": actual_count})
                    continue

                connection.execute(
                    "INSERT INTO source_files "
                    "(source_file, sha256, size_bytes, record_count, ingested_at_utc) "
                    "VALUES (?, ?, ?, 0, ?) "
                    "ON CONFLICT(source_file) DO UPDATE SET "
                    "sha256 = excluded.sha256, size_bytes = excluded.size_bytes, "
                    "record_count = 0, ingested_at_utc = excluded.ingested_at_utc",
                    (source_name, source["sha256"], source["size_bytes"], _utc_now()),
                )
                connection.execute(
                    "DELETE FROM raw_records WHERE source_file = ?", (source_name,)
                )

                count = 0
                batch: list[tuple[str, int, str]] = []
                for row_number, payload in _serialized_rows(source["path"]):
                    count += 1
                    batch.append((source_name, row_number, payload))
                    if len(batch) >= BATCH_SIZE:
                        connection.executemany(
                            "INSERT INTO raw_records "
                            "(source_file, row_number, json_payload) VALUES (?, ?, ?)",
                            batch,
                        )
                        batch.clear()
                if count == 0:
                    raise IngestionError(
                        f"{source['path']}: source array contains no records"
                    )
                if batch:
                    connection.executemany(
                        "INSERT INTO raw_records "
                        "(source_file, row_number, json_payload) VALUES (?, ?, ?)",
                        batch,
                    )

                connection.execute(
                    "UPDATE source_files SET record_count = ? WHERE source_file = ?",
                    (count, source_name),
                )
                imported.append({"file": source_name, "rows": count})

            # Detect a source edited while it was being read before committing any rows.
            for source in sources:
                if (
                    source["path"].stat().st_size != source["size_bytes"]
                    or _sha256(source["path"]) != source["sha256"]
                ):
                    raise IngestionError(
                        f"Source changed during ingestion; no changes were committed: "
                        f"{source['source_file']}"
                    )
    except (sqlite3.Error, OSError) as error:
        raise IngestionError(f"SQLite ingestion failed: {error}") from error
    finally:
        connection.close()

    return {
        "database": str(database_path),
        "imported": imported,
        "skipped": skipped,
        "imported_rows": sum(item["rows"] for item in imported),
        "skipped_rows": sum(item["rows"] for item in skipped),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument(
        "--expected-files",
        type=int,
        default=12,
        help="Expected number of JSON source files (default: 12; use 0 to disable)",
    )
    args = parser.parse_args(argv)
    expected_count = None if args.expected_files == 0 else args.expected_files

    try:
        result = ingest_directory(
            args.data_dir, args.database, expected_file_count=expected_count
        )
    except (IngestionError, sqlite3.Error, OSError) as error:
        print(f"Ingestion failed: {error}", file=sys.stderr)
        return 1

    for source in result["imported"]:
        print(f"Imported {source['rows']:,} rows from {source['file']}.")
    for source in result["skipped"]:
        print(f"Unchanged: {source['file']} ({source['rows']:,} rows).")
    print(
        f"SQLite staging complete: {result['imported_rows']:,} rows imported, "
        f"{result['skipped_rows']:,} unchanged rows; {result['database']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
