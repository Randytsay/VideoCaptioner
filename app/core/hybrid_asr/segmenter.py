from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .models import AlignedToken, SubtitleCue


@dataclass(frozen=True, slots=True)
class SubtitleSegmentationConfig:
    max_chars_per_line: int = 18
    max_lines: int = 2
    min_duration_sec: float = 1.0
    max_duration_sec: float = 6.0
    max_chars_per_second: float = 8.0
    split_pause_above_sec: float = 0.55

    def __post_init__(self) -> None:
        if self.max_chars_per_line < 1 or self.max_lines < 1:
            raise ValueError("line limits must be positive")
        if self.min_duration_sec <= 0:
            raise ValueError("min_duration_sec must be positive")
        if self.max_duration_sec < self.min_duration_sec:
            raise ValueError("max_duration_sec must not be below min_duration_sec")
        if self.max_chars_per_second <= 0:
            raise ValueError("max_chars_per_second must be positive")
        if self.split_pause_above_sec < 0:
            raise ValueError("split_pause_above_sec must be non-negative")

    @property
    def max_chars_per_cue(self) -> int:
        return self.max_chars_per_line * self.max_lines


_TERMINAL_PUNCTUATION = set("。！？!?；;")
_SOFT_PUNCTUATION = set("，、,:：")


def _compact_length(text: str) -> int:
    return len("".join(text.split()))


def _join_tokens(tokens: Sequence[AlignedToken]) -> str:
    return "".join(token.text for token in tokens).strip()


def _wrap_text(text: str, width: int, max_lines: int) -> str:
    """Wrap without ever discarding transcript text.

    A provider can occasionally return a phrase-level token longer than the configured
    cue capacity. In that case the final line is allowed to exceed the preferred width
    instead of silently truncating spoken content.
    """

    if len(text) <= width:
        return text
    lines = [text[index : index + width] for index in range(0, len(text), width)]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    retained = lines[: max_lines - 1]
    retained.append("".join(lines[max_lines - 1 :]))
    return "\n".join(retained)


def build_subtitle_cues(
    tokens: Sequence[AlignedToken],
    config: SubtitleSegmentationConfig = SubtitleSegmentationConfig(),
    *,
    media_duration_sec: float | None = None,
) -> list[SubtitleCue]:
    if not tokens:
        return []

    ordered = sorted(tokens, key=lambda token: (token.start_sec, token.end_sec))
    groups: list[list[AlignedToken]] = []
    current: list[AlignedToken] = []

    for token in ordered:
        if current:
            gap = max(0.0, token.start_sec - current[-1].end_sec)
            if gap >= config.split_pause_above_sec:
                groups.append(current)
                current = []

        current.append(token)
        text = _join_tokens(current)
        duration = max(0.001, current[-1].end_sec - current[0].start_sec)
        compact_length = _compact_length(text)
        reading_speed = compact_length / duration
        too_long = (
            compact_length >= config.max_chars_per_cue
            or duration >= config.max_duration_sec
            or reading_speed >= config.max_chars_per_second
        )
        terminal = bool(text and text[-1] in _TERMINAL_PUNCTUATION)
        soft_boundary = bool(
            text
            and text[-1] in _SOFT_PUNCTUATION
            and compact_length >= config.max_chars_per_line
        )
        if too_long or terminal or soft_boundary:
            groups.append(current)
            current = []

    if current:
        groups.append(current)

    cues: list[SubtitleCue] = []
    for index, group in enumerate(groups, start=1):
        start = group[0].start_sec
        raw_end = group[-1].end_sec
        next_start = groups[index][0].start_sec if index < len(groups) else media_duration_sec
        desired_end = max(raw_end, start + config.min_duration_sec)
        if next_start is not None:
            desired_end = min(desired_end, next_start)
        if media_duration_sec is not None:
            desired_end = min(desired_end, media_duration_sec)
        if desired_end <= start:
            desired_end = max(raw_end, start + 0.05)

        text = _wrap_text(
            _join_tokens(group),
            config.max_chars_per_line,
            config.max_lines,
        )
        cues.append(SubtitleCue(index, start, desired_end, text))

    return cues
