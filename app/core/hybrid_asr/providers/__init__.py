"""Optional adapters that bridge existing and external ASR implementations."""

from .faster_whisper import FasterWhisperConfig, FasterWhisperTranscriber
from .whisper_cpp import WhisperCppConfig, WhisperCppTranscriber

__all__ = [
    "FasterWhisperConfig",
    "FasterWhisperTranscriber",
    "WhisperCppConfig",
    "WhisperCppTranscriber",
]
