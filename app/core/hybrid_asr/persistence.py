from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class FileFingerprint:
    size_bytes: int
    modified_ns: int
    partial_sha256: str

    @property
    def value(self) -> str:
        return f"{self.size_bytes}:{self.modified_ns}:{self.partial_sha256}"


def fingerprint_file(path: Path, sample_bytes: int = 1024 * 1024) -> FileFingerprint:
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        digest.update(handle.read(sample_bytes))
        if stat.st_size > sample_bytes:
            handle.seek(max(0, stat.st_size - sample_bytes))
            digest.update(handle.read(sample_bytes))
    return FileFingerprint(stat.st_size, stat.st_mtime_ns, digest.hexdigest())


class JobRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    version INTEGER NOT NULL
                );
                INSERT INTO schema_meta(version)
                SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_meta);

                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY,
                    source_path TEXT NOT NULL UNIQUE,
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    provider TEXT,
                    model TEXT,
                    glossary_version TEXT,
                    config_hash TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS segments (
                    id INTEGER PRIMARY KEY,
                    media_file_id INTEGER NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
                    segment_key TEXT NOT NULL,
                    start_offset_sec REAL NOT NULL,
                    end_offset_sec REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    retries INTEGER NOT NULL DEFAULT 0,
                    transcript_text TEXT,
                    alignment_coverage REAL,
                    error_message TEXT,
                    updated_at TEXT NOT NULL,
                    UNIQUE(media_file_id, segment_key)
                );

                CREATE TABLE IF NOT EXISTS usage_records (
                    id INTEGER PRIMARY KEY,
                    media_file_id INTEGER REFERENCES media_files(id) ON DELETE CASCADE,
                    segment_id INTEGER REFERENCES segments(id) ON DELETE CASCADE,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_units REAL,
                    output_units REAL,
                    estimated_cost_usd REAL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_items (
                    id INTEGER PRIMARY KEY,
                    media_file_id INTEGER NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
                    segment_id INTEGER REFERENCES segments(id) ON DELETE CASCADE,
                    reason_code TEXT NOT NULL,
                    details TEXT,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.now(UTC).isoformat()

    def upsert_media_file(
        self,
        source_path: Path,
        fingerprint: FileFingerprint,
        *,
        provider: str | None = None,
        model: str | None = None,
        glossary_version: str | None = None,
        config_hash: str | None = None,
    ) -> int:
        now = self.now()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO media_files(
                    source_path, fingerprint, provider, model, glossary_version,
                    config_hash, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_path) DO UPDATE SET
                    fingerprint=excluded.fingerprint,
                    provider=excluded.provider,
                    model=excluded.model,
                    glossary_version=excluded.glossary_version,
                    config_hash=excluded.config_hash,
                    updated_at=excluded.updated_at,
                    status=CASE
                        WHEN media_files.fingerprint != excluded.fingerprint THEN 'pending'
                        ELSE media_files.status
                    END
                """,
                (
                    str(source_path), fingerprint.value, provider, model,
                    glossary_version, config_hash, now, now,
                ),
            )
            row = connection.execute(
                "SELECT id FROM media_files WHERE source_path = ?", (str(source_path),)
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create media file record")
            return int(row["id"])

    def set_media_status(self, media_file_id: int, status: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE media_files SET status = ?, updated_at = ? WHERE id = ?",
                (status, self.now(), media_file_id),
            )

    def upsert_segment(
        self,
        media_file_id: int,
        segment_key: str,
        start_offset_sec: float,
        end_offset_sec: float,
    ) -> int:
        now = self.now()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO segments(
                    media_file_id, segment_key, start_offset_sec, end_offset_sec, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(media_file_id, segment_key) DO UPDATE SET
                    start_offset_sec=excluded.start_offset_sec,
                    end_offset_sec=excluded.end_offset_sec,
                    updated_at=excluded.updated_at
                """,
                (media_file_id, segment_key, start_offset_sec, end_offset_sec, now),
            )
            row = connection.execute(
                "SELECT id FROM segments WHERE media_file_id = ? AND segment_key = ?",
                (media_file_id, segment_key),
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create segment record")
            return int(row["id"])

    def complete_segment(
        self,
        segment_id: int,
        transcript_text: str,
        alignment_coverage: float | None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE segments SET status='done', transcript_text=?, alignment_coverage=?,
                    error_message=NULL, updated_at=? WHERE id=?
                """,
                (transcript_text, alignment_coverage, self.now(), segment_id),
            )

    def fail_segment(self, segment_id: int, error_message: str, needs_review: bool = False) -> None:
        status = "needs_review" if needs_review else "failed"
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE segments SET status=?, retries=retries+1, error_message=?, updated_at=?
                WHERE id=?
                """,
                (status, error_message, self.now(), segment_id),
            )

    def pending_segments(self, media_file_id: int) -> list[sqlite3.Row]:
        with self.connection() as connection:
            return list(
                connection.execute(
                    """
                    SELECT * FROM segments
                    WHERE media_file_id=? AND status IN ('pending', 'failed', 'interrupted')
                    ORDER BY start_offset_sec
                    """,
                    (media_file_id,),
                ).fetchall()
            )
