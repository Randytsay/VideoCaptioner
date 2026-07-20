"""Provider-neutral data models used by the hybrid ASR pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class AudioSegment:
    segment_id: str
    start_offset_sec: float
    end_offset_sec: float
    audio_path: Optional[Path] = None
    overlap_before_sec: float = 0.0
    overlap_after_sec: float = 0.0

    def __post_init__(self) -> None:
        if self.start_offset_sec < 0 or self.end_offset_sec <= self.start_offset_sec:
            raise ValueError("Audio segment offsets must form a positive interval")


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    confidence: Optional[float] = None


@dataclass(frozen=True)
class TranscriptionRequest:
    audio_path: Path
    language: Optional[str] = None
    glossary_prompt: str = ""
    previous_context: str = ""
    need_word_timestamps: bool = False
    model: Optional[str] = None
    device: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TranscriptionResult:
    provider: str
    model: Optional[str]
    segments: tuple[TranscriptSegment, ...]
    raw_response: Optional[Mapping[str, Any]] = None
    warnings: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return "".join(segment.text for segment in self.segments)


@dataclass(frozen=True)
class AlignedToken:
    text: str
    start_sec: float
    end_sec: float
    confidence: Optional[float] = None
    source_start: Optional[int] = None
    source_end: Optional[int] = None


@dataclass(frozen=True)
class AlignmentResult:
    provider: str
    tokens: tuple[AlignedToken, ...]
    transcript: str
    unmatched_text: str = ""
    warnings: tuple[str, ...] = ()

    @property
    def coverage(self) -> float:
        meaningful = [char for char in self.transcript if not char.isspace()]
        if not meaningful:
            return 1.0
        matched = sum(len(token.text.replace(" ", "")) for token in self.tokens)
        return min(1.0, matched / len(meaningful))


@dataclass(frozen=True)
class SRTCue:
    start_sec: float
    end_sec: float
    text: str

    def __post_init__(self) -> None:
        if self.start_sec < 0 or self.end_sec <= self.start_sec:
            raise ValueError("SRT cue must have a positive timestamp range")
        if not self.text.strip():
            raise ValueError("SRT cue text must not be empty")
