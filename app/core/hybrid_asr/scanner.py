from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import time_ns


@dataclass(frozen=True, slots=True)
class MediaScanConfig:
    extensions: tuple[str, ...] = (
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
    )
    recursive: bool = True
    skip_existing_srt: bool = True

    def normalized_extensions(self) -> tuple[str, ...]:
        return tuple(
            extension.lower() if extension.startswith(".") else f".{extension.lower()}"
            for extension in self.extensions
        )


@dataclass(frozen=True, slots=True)
class FileSnapshot:
    size_bytes: int
    modified_ns: int
    observed_ns: int


def scan_media_files(
    root: Path,
    config: MediaScanConfig = MediaScanConfig(),
) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise NotADirectoryError(root)

    iterator = root.rglob("*") if config.recursive else root.glob("*")
    extensions = set(config.normalized_extensions())
    results: list[Path] = []

    for path in iterator:
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if config.skip_existing_srt and path.with_suffix(".srt").exists():
            continue
        results.append(path)

    return sorted(results, key=lambda path: str(path).casefold())


def snapshot_file(path: Path, *, observed_ns: int | None = None) -> FileSnapshot:
    stat = path.stat()
    return FileSnapshot(
        size_bytes=stat.st_size,
        modified_ns=stat.st_mtime_ns,
        observed_ns=observed_ns if observed_ns is not None else time_ns(),
    )


def is_file_stable(
    previous: FileSnapshot,
    current: FileSnapshot,
    *,
    minimum_age_sec: float = 60.0,
) -> bool:
    if minimum_age_sec < 0:
        raise ValueError("minimum_age_sec must be non-negative")

    unchanged = (
        previous.size_bytes == current.size_bytes
        and previous.modified_ns == current.modified_ns
    )
    age_ns = current.observed_ns - current.modified_ns
    return unchanged and age_ns >= int(minimum_age_sec * 1_000_000_000)
