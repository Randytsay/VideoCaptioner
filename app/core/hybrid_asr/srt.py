from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence

from .models import SubtitleCue


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def validate_cues(cues: Sequence[SubtitleCue], media_duration_sec: float | None = None) -> None:
    previous_end = 0.0
    for expected_index, cue in enumerate(cues, start=1):
        if cue.index != expected_index:
            raise ValueError(f"cue index {cue.index} should be {expected_index}")
        if cue.start_sec < previous_end:
            raise ValueError(f"cue {cue.index} overlaps or moves backwards")
        if media_duration_sec is not None and cue.end_sec > media_duration_sec + 0.05:
            raise ValueError(f"cue {cue.index} exceeds media duration")
        previous_end = cue.end_sec


def render_srt(cues: Iterable[SubtitleCue]) -> str:
    blocks: list[str] = []
    for cue in cues:
        blocks.append(
            f"{cue.index}\n"
            f"{format_srt_timestamp(cue.start_sec)} --> {format_srt_timestamp(cue.end_sec)}\n"
            f"{cue.text.strip()}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def write_srt_atomic(
    output_path: Path,
    cues: Sequence[SubtitleCue],
    *,
    media_duration_sec: float | None = None,
    encoding: str = "utf-8-sig",
) -> None:
    validate_cues(cues, media_duration_sec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_suffix(output_path.suffix + ".partial")
    try:
        partial_path.write_text(render_srt(cues), encoding=encoding, newline="\n")
        os.replace(partial_path, output_path)
    finally:
        partial_path.unlink(missing_ok=True)
