"""Small SQLite repository for resumable, segment-level batch work."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import AudioSegment

SCHEMA_VERSION = 1


def file_fingerprint(path: Path, chunk_size: int = 65_536) -> str:
    stat = path.stat()
    digest = hashlib.sha256()
    digest.update(str(stat.st_size).encode())
    digest.update(str(stat.st_mtime_ns).encode())
    with path.open("rb") as handle:
        digest.update(handle.read(chunk_size))
        if stat.st_size > chunk_size:
            handle.seek(max(0, stat.st_size - chunk_size))
            digest.update(handle.read(chunk_size))
    return digest.hexdigest()


class JobRepository:
    def __init__(self, database_path: Path):
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY, path TEXT NOT NULL UNIQUE, fingerprint TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY, media_file_id INTEGER NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
                segment_key TEXT NOT NULL, start_sec REAL NOT NULL, end_sec REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', error TEXT, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(media_file_id, segment_key)
            );
            CREATE TABLE IF NOT EXISTS transcription_attempts (
                id INTEGER PRIMARY KEY, segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
                provider TEXT NOT NULL, model TEXT, status TEXT NOT NULL, error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS alignment_results (
                id INTEGER PRIMARY KEY, segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
                provider TEXT NOT NULL, coverage REAL, unmatched_text TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY, media_file_id INTEGER NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
                provider TEXT NOT NULL, model TEXT, estimated_cost_usd REAL, pricing_version TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS review_items (
                id INTEGER PRIMARY KEY, segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
                reason TEXT NOT NULL, resolved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.connection.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)", (SCHEMA_VERSION,))
        self.connection.commit()

    def register_media(self, path: Path, fingerprint: str, segments: Iterable[AudioSegment]) -> int:
        row = self.connection.execute("SELECT id, fingerprint FROM media_files WHERE path = ?", (str(path),)).fetchone()
        if row and row["fingerprint"] != fingerprint:
            self.connection.execute("DELETE FROM media_files WHERE id = ?", (row["id"],))
            row = None
        if row is None:
            cursor = self.connection.execute("INSERT INTO media_files(path, fingerprint) VALUES (?, ?)", (str(path), fingerprint))
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return a media file ID")
            media_id = int(cursor.lastrowid)
        else:
            media_id = int(row["id"])
        self.connection.executemany(
            "INSERT OR IGNORE INTO segments(media_file_id, segment_key, start_sec, end_sec) VALUES (?, ?, ?, ?)",
            [(media_id, segment.segment_id, segment.start_offset_sec, segment.end_offset_sec) for segment in segments],
        )
        self.connection.commit()
        return media_id

    def pending_segments(self, media_id: int) -> list[sqlite3.Row]:
        return list(self.connection.execute("SELECT * FROM segments WHERE media_file_id = ? AND status IN ('pending', 'interrupted', 'failed') ORDER BY start_sec", (media_id,)))

    def set_segment_status(self, segment_id: int, status: str, error: str | None = None) -> None:
        if status not in {"pending", "processing", "done", "failed", "interrupted", "needs_review"}:
            raise ValueError(f"Unsupported segment status: {status}")
        self.connection.execute("UPDATE segments SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, error, segment_id))
        self.connection.commit()
