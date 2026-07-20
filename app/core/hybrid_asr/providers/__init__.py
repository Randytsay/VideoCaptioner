"""Optional adapters that bridge existing and external ASR implementations."""

from .faster_whisper import FasterWhisperConfig, FasterWhisperTranscriber
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
    "QwenASRConfig",
    "QwenForcedAligner",
    "QwenForcedAlignerConfig",
    "QwenTranscriber",
    "WhisperCppConfig",
    "WhisperCppTranscriber",
]
