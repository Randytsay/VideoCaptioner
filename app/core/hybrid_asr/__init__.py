"""Model-agnostic core building blocks for hybrid transcription workflows."""

from .glossary import Glossary, GlossaryApplyResult, GlossaryEntry, GlossaryReplacement
from .interfaces import ForcedAligner, Transcriber
from .models import (
    AlignedToken,
    AlignmentRequest,
    AlignmentResult,
    AudioSegment,
    SubtitleCue,
    TranscriptionRequest,
    TranscriptionResult,
    TranscriptSegment,
)
from .pipeline import SegmentPipeline, SegmentPipelineResult
from .providers import FasterWhisperConfig, FasterWhisperTranscriber
from .scanner import FileSnapshot, MediaScanConfig, is_file_stable, scan_media_files
from .segmenter import SubtitleSegmentationConfig, build_subtitle_cues

__all__ = [
    "AlignedToken",
    "AlignmentRequest",
    "AlignmentResult",
    "AudioSegment",
    "FileSnapshot",
    "FasterWhisperConfig",
    "FasterWhisperTranscriber",
    "ForcedAligner",
    "Glossary",
    "GlossaryApplyResult",
    "GlossaryEntry",
    "GlossaryReplacement",
    "MediaScanConfig",
    "SegmentPipeline",
    "SegmentPipelineResult",
    "SubtitleCue",
    "SubtitleSegmentationConfig",
    "TranscriptSegment",
    "Transcriber",
    "TranscriptionRequest",
    "TranscriptionResult",
    "build_subtitle_cues",
    "is_file_stable",
    "scan_media_files",
]
