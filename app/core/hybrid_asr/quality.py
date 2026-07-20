"""Deterministic, no-cost checks used before escalation to another provider."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import AlignmentResult, SRTCue


@dataclass(frozen=True)
class QualityReport:
    warnings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.warnings


def check_alignment(result: AlignmentResult, warning_below: float = 0.90) -> QualityReport:
    warnings = []
    if result.coverage < warning_below:
        warnings.append(f"alignment coverage is {result.coverage:.1%}, below {warning_below:.1%}")
    if result.unmatched_text:
        warnings.append("alignment returned unmatched text")
    return QualityReport(tuple(warnings))


def check_transcript_density(text: str, duration_sec: float, min_chars_per_minute: float = 8, max_chars_per_minute: float = 800) -> QualityReport:
    if duration_sec <= 0:
        return QualityReport(("audio duration must be positive",))
    density = len(re.sub(r"\s+", "", text)) / (duration_sec / 60)
    if density < min_chars_per_minute or density > max_chars_per_minute:
        return QualityReport((f"transcript density {density:.1f} chars/min is outside expected range",))
    return QualityReport(())


def check_cues(cues: list[SRTCue], duration_sec: float) -> QualityReport:
    warnings: list[str] = []
    prior_end = 0.0
    for cue in cues:
        if cue.start_sec < prior_end:
            warnings.append("cue timestamps overlap or move backwards")
            break
        prior_end = cue.end_sec
    if cues and cues[-1].end_sec > duration_sec:
        warnings.append("last cue exceeds audio duration")
    return QualityReport(tuple(warnings))
