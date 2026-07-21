"""Adapter for VideoCaptioner's existing whisper.cpp implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.core.asr.whisper_cpp import WhisperCppASR

from ..models import TranscriptionRequest, TranscriptionResult, TranscriptSegment


@dataclass(frozen=True, slots=True)
class WhisperCppConfig:
    model: str
    executable: str | None = None
    language: str = ""
    use_cache: bool = True


class WhisperCppTranscriber:
    """Bridge ``WhisperCppASR`` without introducing a parallel whisper.cpp API."""

    provider_name = "whisper_cpp"

    def __init__(
        self,
        config: WhisperCppConfig,
        asr_factory: Callable[..., WhisperCppASR] = WhisperCppASR,
    ) -> None:
        self.config = config
        self._asr_factory = asr_factory

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        language = request.language if request.language is not None else self.config.language
        asr = self._asr_factory(
            audio_input=str(request.audio_path),
            language=language,
            whisper_cpp_path=self.config.executable,
            whisper_model=self.config.model,
            use_cache=self.config.use_cache,
            need_word_time_stamp=request.word_timestamps,
        )
        data = asr.run()
        segments = tuple(
            TranscriptSegment(
                text=segment.text,
                start_sec=segment.start_time / 1000,
                end_sec=segment.end_time / 1000,
            )
            for segment in data.segments
        )
        warnings = []
        if request.glossary:
            warnings.append("Existing WhisperCppASR does not accept a custom glossary prompt")
        if request.previous_context:
            warnings.append("Existing WhisperCppASR does not accept previous-context text")
        return TranscriptionResult(
            text="".join(segment.text for segment in segments),
            segments=segments,
            provider=self.provider_name,
            model=self.config.model,
            language=language or None,
            warnings=tuple(warnings),
            raw_metadata={
                "word_timestamps_requested": request.word_timestamps,
                "executable": self.config.executable,
            },
        )
