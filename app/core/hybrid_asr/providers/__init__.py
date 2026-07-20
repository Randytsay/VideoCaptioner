"""Optional adapters that bridge existing and external ASR implementations."""

from .faster_whisper import FasterWhisperConfig, FasterWhisperTranscriber

__all__ = ["FasterWhisperConfig", "FasterWhisperTranscriber"]
