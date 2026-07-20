from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .models import AudioSegment


@dataclass(frozen=True, slots=True)
class SilenceInterval:
    start_sec: float
    end_sec: float

    @property
    def midpoint_sec(self) -> float:
        return (self.start_sec + self.end_sec) / 2


_SILENCE_START = re.compile(r"silence_start:\s*([0-9.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*([0-9.]+)")


def require_binary(binary: str) -> str:
    resolved = shutil.which(binary)
    if resolved is None:
        raise RuntimeError(f"{binary} was not found in PATH")
    return resolved


def require_ffmpeg(binary: str = "ffmpeg") -> str:
    return require_binary(binary)


def probe_duration(source_path: Path, *, ffprobe_binary: str = "ffprobe") -> float:
    binary = require_binary(ffprobe_binary)
    command = [
        binary,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(source_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {completed.stderr.strip()}")
    try:
        duration = float(completed.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("ffprobe returned an invalid duration") from exc
    if duration <= 0:
        raise RuntimeError("ffprobe returned a non-positive duration")
    return duration


def normalize_audio(
    source_path: Path,
    output_path: Path,
    *,
    sample_rate: int = 16_000,
    channels: int = 1,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    binary = require_ffmpeg(ffmpeg_binary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg audio normalization failed: {completed.stderr.strip()}")


def detect_silences(
    audio_path: Path,
    *,
    threshold_db: float = -35.0,
    minimum_duration_sec: float = 0.5,
    ffmpeg_binary: str = "ffmpeg",
) -> list[SilenceInterval]:
    if minimum_duration_sec <= 0:
        raise ValueError("minimum_duration_sec must be positive")
    binary = require_ffmpeg(ffmpeg_binary)
    command = [
        binary,
        "-hide_banner",
        "-nostats",
        "-i",
        str(audio_path),
        "-af",
        f"silencedetect=noise={threshold_db}dB:d={minimum_duration_sec}",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg silence detection failed: {completed.stderr.strip()}")
    return parse_silencedetect(completed.stderr)


def parse_silencedetect(stderr: str) -> list[SilenceInterval]:
    intervals: list[SilenceInterval] = []
    pending_start: float | None = None
    for line in stderr.splitlines():
        start_match = _SILENCE_START.search(line)
        if start_match:
            pending_start = float(start_match.group(1))
            continue
        end_match = _SILENCE_END.search(line)
        if end_match and pending_start is not None:
            end = float(end_match.group(1))
            if end >= pending_start:
                intervals.append(SilenceInterval(pending_start, end))
            pending_start = None
    return intervals


def choose_split_points(
    duration_sec: float,
    silences: Sequence[SilenceInterval],
    *,
    target_sec: float = 900.0,
    search_window_sec: float = 60.0,
    minimum_segment_sec: float = 30.0,
) -> list[float]:
    if duration_sec <= 0:
        raise ValueError("duration_sec must be positive")
    if target_sec <= 0:
        raise ValueError("target_sec must be positive")

    points = [0.0]
    target = target_sec
    while target < duration_sec:
        lower = max(points[-1] + minimum_segment_sec, target - search_window_sec)
        upper = min(duration_sec - minimum_segment_sec, target + search_window_sec)
        candidates = [
            silence.midpoint_sec
            for silence in silences
            if lower <= silence.midpoint_sec <= upper
        ]
        chosen = min(candidates, key=lambda point: abs(point - target)) if candidates else target
        if chosen <= points[-1]:
            break
        points.append(chosen)
        target = chosen + target_sec
    points.append(duration_sec)
    return points


def build_segment_plan(
    source_audio: Path,
    duration_sec: float,
    silences: Sequence[SilenceInterval],
    *,
    target_sec: float = 900.0,
    search_window_sec: float = 60.0,
    overlap_sec: float = 3.0,
) -> list[AudioSegment]:
    if overlap_sec < 0:
        raise ValueError("overlap_sec must be non-negative")
    points = choose_split_points(
        duration_sec,
        silences,
        target_sec=target_sec,
        search_window_sec=search_window_sec,
    )
    segments: list[AudioSegment] = []
    for index, (raw_start, raw_end) in enumerate(zip(points, points[1:]), start=1):
        start = max(0.0, raw_start - (overlap_sec if index > 1 else 0.0))
        end = min(
            duration_sec,
            raw_end + (overlap_sec if raw_end < duration_sec else 0.0),
        )
        segments.append(
            AudioSegment(
                segment_id=f"segment_{index:04d}",
                audio_path=source_audio,
                start_offset_sec=start,
                end_offset_sec=end,
                overlap_sec=overlap_sec if index > 1 else 0.0,
            )
        )
    return segments


def extract_segment(
    source_audio: Path,
    output_path: Path,
    *,
    start_sec: float,
    end_sec: float,
    sample_rate: int = 16_000,
    channels: int = 1,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    if start_sec < 0 or end_sec <= start_sec:
        raise ValueError("invalid segment time range")
    binary = require_ffmpeg(ffmpeg_binary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start_sec:.6f}",
        "-i",
        str(source_audio),
        "-t",
        f"{end_sec - start_sec:.6f}",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg segment extraction failed: {completed.stderr.strip()}")


def materialize_segment_plan(
    plan: Sequence[AudioSegment],
    output_directory: Path,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> list[AudioSegment]:
    output_directory.mkdir(parents=True, exist_ok=True)
    materialized: list[AudioSegment] = []
    created_paths: list[Path] = []
    try:
        for segment in plan:
            output_path = output_directory / f"{segment.segment_id}.wav"
            extract_segment(
                segment.audio_path,
                output_path,
                start_sec=segment.start_offset_sec,
                end_sec=segment.end_offset_sec,
                ffmpeg_binary=ffmpeg_binary,
            )
            created_paths.append(output_path)
            materialized.append(
                AudioSegment(
                    segment_id=segment.segment_id,
                    audio_path=output_path,
                    start_offset_sec=segment.start_offset_sec,
                    end_offset_sec=segment.end_offset_sec,
                    overlap_sec=segment.overlap_sec,
                )
            )
    except Exception:
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise
    return materialized
