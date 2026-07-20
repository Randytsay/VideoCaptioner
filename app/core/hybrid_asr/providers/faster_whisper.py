"""Adapter for VideoCaptioner's existing FasterWhisper command-line ASR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.core.asr.asr_data import ASRData
from app.core.asr.faster_whisper import FasterWhisperASR

from ..models import TranscriptionRequest, TranscriptionResult, TranscriptSegment


@dataclass(frozen=True, slots=True)
class FasterWhisperConfig:
    """Settings mapped directly to the existing ``FasterWhisperASR`` adapter."""

    program: str = ""
    model: str = "base"
    model_dir: str = ""
    language: str = ""
    device: str = "cpu"
    vad_filter: bool = True
    vad_threshold: float = 0.4
    vad_method: str = ""
    ff_mdx_kim2: bool = False
    use_cache: bool = True


class FasterWhisperTranscriber:
    """Expose existing FasterWhisper behaviour through the Hybrid ASR contract.

    This intentionally delegates model execution to ``FasterWhisperASR`` rather
    than introducing a second faster-whisper integration. The standalone binary
    currently owns model lifetime, so a process per prepared segment remains an
    existing-provider limitation to address separately if needed.
    """

    provider_name = "faster_whisper"

    def __init__(
        self,
        config: FasterWhisperConfig,
        asr_factory: Callable[..., FasterWhisperASR] = FasterWhisperASR,
    ) -> None:
        self.config = config
        self._asr_factory = asr_factory

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        prompt = self._build_prompt(request)
        language = request.language if request.language is not None else self.config.language
        asr = self._asr_factory(
            audio_input=str(request.audio_path),
            faster_whisper_program=self.config.program,
            whisper_model=self.config.model,
            model_dir=self.config.model_dir,
            language=language,
            device=self.config.device,
            use_cache=self.config.use_cache,
            need_word_time_stamp=request.word_timestamps,
            vad_filter=self.config.vad_filter,
            vad_threshold=self.config.vad_threshold,
            vad_method=self.config.vad_method,
            ff_mdx_kim2=self.config.ff_mdx_kim2,
            prompt=prompt or None,
        )
        data = asr.run()
        return self._to_result(data, language, prompt)

    def _build_prompt(self, request: TranscriptionRequest) -> str:
        parts: list[str] = []
        if request.glossary:
            parts.append("專有名詞：" + "、".join(request.glossary))
        if request.previous_context:
            parts.append(
                "以下是前段脈絡，僅供理解，不可重複輸出：" + request.previous_context
            )
        return "\n".join(parts)

    def _to_result(
        self, data: ASRData, language: str | None, prompt: str
    ) -> TranscriptionResult:
        segments = tuple(
            TranscriptSegment(
                text=segment.text,
                start_sec=segment.start_time / 1000,
                end_sec=segment.end_time / 1000,
            )
            for segment in data.segments
        )
        return TranscriptionResult(
            text="".join(segment.text for segment in segments),
            segments=segments,
            provider=self.provider_name,
            model=self.config.model,
            language=language or None,
            raw_metadata={
                "word_timestamps_requested": bool(segments),
                "prompt_used": bool(prompt),
                "device": self.config.device,
            },
        )
