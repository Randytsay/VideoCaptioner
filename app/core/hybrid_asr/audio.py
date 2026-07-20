"""FFmpeg-backed audio normalisation and silence-aware segment planning."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from .models import AudioSegment

_SILENCE_RE = re.compile(r"silence_(?:start|end):\s*([0-9.]+)")


class FFmpegUnavailableError(RuntimeError):
    pass


def require_ffmpeg() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise FFmpegUnavailableError(f"Missing required executable(s): {', '.join(missing)}")


def media_duration(path: Path) -> float:
    require_ffmpeg()
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return float(completed.stdout.strip())


def extract_normalized_audio(source: Path, destination: Path, audio_track_index: int = 0) -> Path:
    """Extract 16 kHz mono PCM WAV, preserving paths with non-ASCII characters."""
    require_ffmpeg()
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-i", str(source), "-map", f"0:a:{audio_track_index}",
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(destination)],
        check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if not destination.is_file():
        raise RuntimeError(f"FFmpeg did not produce expected file: {destination}")
    return destination


def materialize_segments(source_audio: Path, destination_dir: Path, segments: Iterable[AudioSegment]) -> list[AudioSegment]:
    """Create WAV files for an existing plan and return segments with their paths.

    The input is expected to be the already-normalised WAV. Keeping extraction
    here makes the planner reusable for source video and audio alike.
    """
    require_ffmpeg()
    destination_dir.mkdir(parents=True, exist_ok=True)
    materialized: list[AudioSegment] = []
    for segment in segments:
        output = destination_dir / f"segment-{segment.segment_id}.wav"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-ss", f"{segment.start_offset_sec:.3f}", "-i", str(source_audio),
             "-t", f"{segment.end_offset_sec - segment.start_offset_sec:.3f}", "-ac", "1", "-ar", "16000",
             "-c:a", "pcm_s16le", str(output)],
            check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if not output.is_file():
            raise RuntimeError(f"FFmpeg did not produce expected segment: {output}")
        materialized.append(AudioSegment(
            segment.segment_id, segment.start_offset_sec, segment.end_offset_sec, output,
            segment.overlap_before_sec, segment.overlap_after_sec,
        ))
    return materialized


def detect_silence(path: Path, noise_db: int = -35, minimum_duration: float = 0.45) -> list[float]:
    """Return silence boundary timestamps emitted by FFmpeg's silencedetect filter."""
    require_ffmpeg()
    completed = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", str(path), "-af", f"silencedetect=noise={noise_db}dB:d={minimum_duration}", "-f", "null", "-"],
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return [float(value) for value in _SILENCE_RE.findall(completed.stderr)]


def plan_segments(
    duration_sec: float,
    silence_boundaries: Iterable[float] = (),
    target_sec: float = 15 * 60,
    search_window_sec: float = 60,
    overlap_sec: float = 3,
) -> list[AudioSegment]:
    """Plan full-coverage segments, preferring a nearby silence boundary.

    Overlap is only added after a cut point has been selected, so the first and
    final boundaries remain exactly 0 and media duration.
    """
    if duration_sec <= 0 or target_sec <= 0 or overlap_sec < 0:
        raise ValueError("duration and target must be positive; overlap cannot be negative")
    silences = sorted({point for point in silence_boundaries if 0 < point < duration_sec})
    cuts = [0.0]
    cursor = target_sec
    while cursor < duration_sec:
        nearby = [point for point in silences if abs(point - cursor) <= search_window_sec and point > cuts[-1]]
        cuts.append(min(nearby, key=lambda point: abs(point - cursor)) if nearby else cursor)
        cursor = cuts[-1] + target_sec
    cuts.append(duration_sec)
    segments: list[AudioSegment] = []
    for index, (left, right) in enumerate(zip(cuts, cuts[1:]), start=1):
        start = max(0.0, left - (overlap_sec if index > 1 else 0.0))
        end = min(duration_sec, right + (overlap_sec if index < len(cuts) - 1 else 0.0))
        segments.append(AudioSegment(str(index), start, end, overlap_before_sec=left - start, overlap_after_sec=end - right))
    return segments
