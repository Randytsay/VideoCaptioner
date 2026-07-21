from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .glossary import Glossary, GlossaryApplyResult
from .interfaces import ForcedAligner, Transcriber
from .models import (
    AlignedToken,
    AlignmentRequest,
    AlignmentResult,
    AudioSegment,
    SubtitleCue,
    TranscriptionRequest,
    TranscriptionResult,
)
from .quality import QualityIssue, QualityThresholds, inspect_transcript
from .segmenter import SubtitleSegmentationConfig, build_subtitle_cues


@dataclass(frozen=True, slots=True)
class SegmentPipelineResult:
    transcription: TranscriptionResult
    glossary_result: GlossaryApplyResult
    alignment: AlignmentResult | None
    cues: Sequence[SubtitleCue]
    quality_issues: Sequence[QualityIssue]


class SegmentPipeline:
    """Runs one prepared audio segment through injected model providers."""

    def __init__(
        self,
        transcriber: Transcriber,
        aligner: ForcedAligner | None = None,
        glossary: Glossary | None = None,
        subtitle_config: SubtitleSegmentationConfig = SubtitleSegmentationConfig(),
        quality_thresholds: QualityThresholds = QualityThresholds(),
    ) -> None:
        self.transcriber = transcriber
        self.aligner = aligner
        self.glossary = glossary or Glossary()
        self.subtitle_config = subtitle_config
        self.quality_thresholds = quality_thresholds

    def process(
        self,
        segment: AudioSegment,
        *,
        language: str | None = None,
        previous_context: str | None = None,
    ) -> SegmentPipelineResult:
        transcription = self.transcriber.transcribe(
            TranscriptionRequest(
                audio_path=segment.audio_path,
                language=language,
                glossary=self.glossary.prompt_terms(),
                previous_context=previous_context,
                word_timestamps=self.aligner is None,
            )
        )
        glossary_result = self.glossary.apply(transcription.text)

        alignment: AlignmentResult | None = None
        if self.aligner is not None:
            relative = self.aligner.align(
                AlignmentRequest(
                    audio_path=segment.audio_path,
                    transcript=glossary_result.text,
                    language=language,
                    rough_start_sec=0.0,
                    rough_end_sec=segment.duration_sec,
                )
            )
            shifted_tokens = tuple(
                AlignedToken(
                    text=token.text,
                    start_sec=token.start_sec + segment.start_offset_sec,
                    end_sec=token.end_sec + segment.start_offset_sec,
                    confidence=token.confidence,
                    source_start=token.source_start,
                    source_end=token.source_end,
                )
                for token in relative.tokens
            )
            alignment = AlignmentResult(
                tokens=shifted_tokens,
                coverage=relative.coverage,
                provider=relative.provider,
                model=relative.model,
                unmatched_text=relative.unmatched_text,
                warnings=relative.warnings,
                raw_metadata=relative.raw_metadata,
            )
            tokens = shifted_tokens
        else:
            tokens = self._tokens_from_transcription(
                transcription,
                glossary_result.text,
                segment,
            )

        cues = build_subtitle_cues(
            tokens,
            self.subtitle_config,
            media_duration_sec=segment.end_offset_sec,
        )
        issues = inspect_transcript(
            glossary_result.text,
            segment.duration_sec,
            alignment=alignment,
            segments=transcription.segments,
            thresholds=self.quality_thresholds,
        )
        if glossary_result.review_hits:
            issues = list(issues) + [
                QualityIssue(
                    "glossary_review",
                    f"Review glossary terms: {', '.join(glossary_result.review_hits)}",
                )
            ]

        return SegmentPipelineResult(
            transcription=transcription,
            glossary_result=glossary_result,
            alignment=alignment,
            cues=cues,
            quality_issues=tuple(issues),
        )

    @staticmethod
    def _tokens_from_transcription(
        transcription: TranscriptionResult,
        text: str,
        segment: AudioSegment,
    ) -> tuple[AlignedToken, ...]:
        timed_segments = [
            transcript_segment
            for transcript_segment in transcription.segments
            if transcript_segment.start_sec is not None
            and transcript_segment.end_sec is not None
            and transcript_segment.text.strip()
        ]
        if timed_segments and text == transcription.text:
            return tuple(
                AlignedToken(
                    text=transcript_segment.text,
                    start_sec=transcript_segment.start_sec + segment.start_offset_sec,
                    end_sec=transcript_segment.end_sec + segment.start_offset_sec,
                    confidence=transcript_segment.confidence,
                )
                for transcript_segment in timed_segments
                if transcript_segment.start_sec is not None
                and transcript_segment.end_sec is not None
            )
        if not text.strip():
            return ()
        return (
            AlignedToken(
                text=text,
                start_sec=segment.start_offset_sec,
                end_sec=segment.end_offset_sec,
            ),
        )
