from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .models import AlignmentResult, TranscriptSegment


@dataclass(frozen=True, slots=True)
class QualityThresholds:
    minimum_alignment_coverage: float = 0.90
    failure_alignment_coverage: float = 0.75
    minimum_chars_per_minute: float = 8.0
    maximum_chars_per_second: float = 18.0
    maximum_repeated_ngram_ratio: float = 0.35


@dataclass(frozen=True, slots=True)
class QualityIssue:
    code: str
    message: str
    severity: str = "warning"


def repeated_ngram_ratio(text: str, n: int = 3) -> float:
    compact = "".join(text.split())
    if len(compact) < n * 2:
        return 0.0
    grams = [compact[index : index + n] for index in range(len(compact) - n + 1)]
    return 1.0 - len(set(grams)) / len(grams)


def inspect_transcript(
    text: str,
    duration_sec: float,
    *,
    alignment: AlignmentResult | None = None,
    segments: Sequence[TranscriptSegment] = (),
    thresholds: QualityThresholds = QualityThresholds(),
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    compact = "".join(text.split())

    if duration_sec <= 0:
        return [QualityIssue("invalid_duration", "Audio duration must be positive", "error")]

    chars_per_minute = len(compact) / duration_sec * 60
    chars_per_second = len(compact) / duration_sec
    if chars_per_minute < thresholds.minimum_chars_per_minute:
        issues.append(QualityIssue("low_text_density", "Transcript may be incomplete"))
    if chars_per_second > thresholds.maximum_chars_per_second:
        issues.append(QualityIssue("high_text_density", "Transcript may contain hallucinated text"))

    ratio = repeated_ngram_ratio(compact)
    if ratio > thresholds.maximum_repeated_ngram_ratio:
        issues.append(QualityIssue("excessive_repetition", f"Repeated n-gram ratio is {ratio:.2f}"))

    if alignment is not None:
        if alignment.coverage < thresholds.failure_alignment_coverage:
            issues.append(QualityIssue("alignment_failed", f"Alignment coverage is {alignment.coverage:.1%}", "error"))
        elif alignment.coverage < thresholds.minimum_alignment_coverage:
            issues.append(QualityIssue("alignment_low", f"Alignment coverage is {alignment.coverage:.1%}"))

    previous_end = 0.0
    for segment in segments:
        if segment.start_sec is None or segment.end_sec is None:
            continue
        if segment.start_sec < previous_end:
            issues.append(QualityIssue("timestamp_overlap", "Transcript timestamps overlap or move backwards", "error"))
            break
        previous_end = segment.end_sec

    return issues
