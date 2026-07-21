from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class UsageMetrics:
    """Provider-reported token usage for one transcription request.

    These figures are not an invoice. They are the usage values returned by the
    provider and can be used with a versioned price table for an estimate.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    cached_input_tokens: int | None = None

    def __post_init__(self) -> None:
        for name in (
            "input_tokens",
            "output_tokens",
            "reasoning_tokens",
            "cached_input_tokens",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class AudioSegment:
    segment_id: str
    audio_path: Path
    start_offset_sec: float
    end_offset_sec: float
    overlap_sec: float = 0.0

    def __post_init__(self) -> None:
        if self.start_offset_sec < 0:
            raise ValueError("start_offset_sec must be non-negative")
        if self.end_offset_sec <= self.start_offset_sec:
            raise ValueError("end_offset_sec must be greater than start_offset_sec")
        if self.overlap_sec < 0:
            raise ValueError("overlap_sec must be non-negative")

    @property
    def duration_sec(self) -> float:
        return self.end_offset_sec - self.start_offset_sec


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    text: str
    start_sec: float | None = None
    end_sec: float | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.start_sec is not None and self.start_sec < 0:
            raise ValueError("start_sec must be non-negative")
        if self.end_sec is not None and self.start_sec is not None and self.end_sec < self.start_sec:
            raise ValueError("end_sec must not precede start_sec")


@dataclass(frozen=True, slots=True)
class TranscriptionRequest:
    audio_path: Path
    language: str | None = None
    glossary: Sequence[str] = ()
    previous_context: str | None = None
    word_timestamps: bool = False
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    segments: Sequence[TranscriptSegment]
    provider: str
    model: str
    language: str | None = None
    warnings: Sequence[str] = ()
    usage: UsageMetrics | None = None
    raw_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AlignmentRequest:
    audio_path: Path
    transcript: str
    language: str | None = None
    rough_start_sec: float | None = None
    rough_end_sec: float | None = None
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AlignedToken:
    text: str
    start_sec: float
    end_sec: float
    confidence: float | None = None
    source_start: int | None = None
    source_end: int | None = None

    def __post_init__(self) -> None:
        if self.start_sec < 0:
            raise ValueError("start_sec must be non-negative")
        if self.end_sec < self.start_sec:
            raise ValueError("end_sec must not precede start_sec")


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    tokens: Sequence[AlignedToken]
    coverage: float
    provider: str
    model: str
    unmatched_text: str = ""
    warnings: Sequence[str] = ()
    raw_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("coverage must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class SubtitleCue:
    index: int
    start_sec: float
    end_sec: float
    text: str

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("index must start at 1")
        if self.start_sec < 0:
            raise ValueError("start_sec must be non-negative")
        if self.end_sec <= self.start_sec:
            raise ValueError("end_sec must be greater than start_sec")
        if not self.text.strip():
            raise ValueError("subtitle text must not be empty")
