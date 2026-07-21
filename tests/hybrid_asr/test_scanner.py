from pathlib import Path

from app.core.hybrid_asr.scanner import (
    FileSnapshot,
    is_file_stable,
    scan_media_files,
)


def test_scan_skips_media_with_existing_srt(tmp_path: Path) -> None:
    (tmp_path / "a.mp4").write_bytes(b"a")
    (tmp_path / "a.srt").write_text("done", encoding="utf-8")
    (tmp_path / "b.wav").write_bytes(b"b")
    assert scan_media_files(tmp_path) == [tmp_path / "b.wav"]


def test_unchanged_old_file_is_stable() -> None:
    previous = FileSnapshot(100, 1_000_000_000, 70_000_000_000)
    current = FileSnapshot(100, 1_000_000_000, 80_000_000_000)
    assert is_file_stable(previous, current, minimum_age_sec=60.0)
