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
    UsageMetrics,
)
from .persistence import JobRepository, UsageSummary
from .pipeline import SegmentPipeline, SegmentPipelineResult
from .pricing import TokenPricing, UsageCostEstimate, estimate_token_cost
from .providers import (
    FasterWhisperConfig,
    FasterWhisperTranscriber,
    GeminiVertexConfig,
    GeminiVertexTranscriber,
    QwenASRConfig,
    QwenForcedAligner,
    QwenForcedAlignerConfig,
    QwenTranscriber,
    WhisperCppConfig,
    WhisperCppTranscriber,
)
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
    "GeminiVertexConfig",
    "GeminiVertexTranscriber",
    "ForcedAligner",
    "Glossary",
    "GlossaryApplyResult",
    "GlossaryEntry",
    "GlossaryReplacement",
    "JobRepository",
    "MediaScanConfig",
    "QwenASRConfig",
    "QwenForcedAligner",
    "QwenForcedAlignerConfig",
    "QwenTranscriber",
    "SegmentPipeline",
    "SegmentPipelineResult",
    "SubtitleCue",
    "SubtitleSegmentationConfig",
    "TokenPricing",
    "TranscriptSegment",
    "Transcriber",
    "TranscriptionRequest",
    "TranscriptionResult",
    "UsageCostEstimate",
    "UsageMetrics",
    "UsageSummary",
    "WhisperCppConfig",
    "WhisperCppTranscriber",
    "build_subtitle_cues",
    "estimate_token_cost",
    "is_file_stable",
    "scan_media_files",
]
