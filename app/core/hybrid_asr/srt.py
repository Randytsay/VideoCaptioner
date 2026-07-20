"""Validated and atomic SRT output."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from .models import SRTCue


def _timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def validate_cues(cues: Iterable[SRTCue], media_duration_sec: float | None = None) -> list[SRTCue]:
    ordered = list(cues)
    previous_end = 0.0
    for cue in ordered:
        if cue.start_sec < previous_end:
            raise ValueError("SRT cue timestamps overlap or move backwards")
        if media_duration_sec is not None and cue.end_sec > media_duration_sec + 0.001:
            raise ValueError("SRT cue exceeds media duration")
        previous_end = cue.end_sec
    return ordered


def render_srt(cues: Iterable[SRTCue], media_duration_sec: float | None = None) -> str:
    ordered = validate_cues(cues, media_duration_sec)
    return "\n\n".join(
        f"{index}\n{_timestamp(cue.start_sec)} --> {_timestamp(cue.end_sec)}\n{cue.text.strip()}"
        for index, cue in enumerate(ordered, start=1)
    ) + ("\n" if ordered else "")


def write_srt_atomic(destination: Path, cues: Iterable[SRTCue], media_duration_sec: float | None = None) -> Path:
    content = render_srt(cues, media_duration_sec)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.write_text(content, encoding="utf-8", newline="\n")
    os.replace(partial, destination)
    return destination
