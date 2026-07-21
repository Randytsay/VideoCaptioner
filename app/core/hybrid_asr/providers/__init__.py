"""Optional adapters that bridge existing and external ASR implementations."""

from .faster_whisper import FasterWhisperConfig, FasterWhisperTranscriber
from .gemini_vertex import GeminiVertexConfig, GeminiVertexTranscriber
from .qwen import (
    QwenASRConfig,
    QwenForcedAligner,
    QwenForcedAlignerConfig,
    QwenTranscriber,
)
from .whisper_cpp import WhisperCppConfig, WhisperCppTranscriber

__all__ = [
    "FasterWhisperConfig",
    "FasterWhisperTranscriber",
    "GeminiVertexConfig",
    "GeminiVertexTranscriber",
    "QwenASRConfig",
    "QwenForcedAligner",
    "QwenForcedAlignerConfig",
    "QwenTranscriber",
    "WhisperCppConfig",
    "WhisperCppTranscriber",
]
