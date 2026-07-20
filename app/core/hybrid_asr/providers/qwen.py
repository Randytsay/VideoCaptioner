"""Optional local adapters for the official ``qwen-asr`` package.

Imports are deliberately lazy so the desktop application does not acquire Qwen
or PyTorch dependencies unless the user selects this provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from ..models import (
    AlignedToken,
    AlignmentRequest,
    AlignmentResult,
    TranscriptionRequest,
    TranscriptionResult,
    TranscriptSegment,
)

_LANGUAGE_NAMES = {
    "zh": "Chinese",
    "en": "English",
    "yue": "Cantonese",
    "ja": "Japanese",
    "ko": "Korean",
}


def qwen_language(language: str | None) -> str | None:
    if language is None or not language.strip():
        return None
    return _LANGUAGE_NAMES.get(language.lower(), language)


@dataclass(frozen=True, slots=True)
class QwenASRConfig:
    model_path: Path
    load_kwargs: dict[str, Any] = field(default_factory=dict)
    max_new_tokens: int = 512


@dataclass(frozen=True, slots=True)
class QwenForcedAlignerConfig:
    model_path: Path
    load_kwargs: dict[str, Any] = field(default_factory=dict)


class QwenTranscriber:
    """Lazy, single-instance wrapper around ``Qwen3ASRModel``."""

    provider_name = "qwen_asr"

    def __init__(
        self,
        config: QwenASRConfig,
        loader: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config
        self._loader = loader or self._default_loader
        self._model: Any | None = None

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        model = self._load_model()
        context = self._build_context(request)
        results = model.transcribe(
            audio=str(request.audio_path),
            context=context,
            language=qwen_language(request.language),
            return_time_stamps=request.word_timestamps,
        )
        if not results:
            raise RuntimeError("Qwen ASR returned no transcription result")
        result = results[0]
        text = str(getattr(result, "text", ""))
        timestamps = getattr(result, "time_stamps", None) or ()
        segments = tuple(self._to_transcript_segment(item) for item in timestamps)
        if not segments and text:
            segments = (TranscriptSegment(text),)
        return TranscriptionResult(
            text=text,
            segments=segments,
            provider=self.provider_name,
            model=str(self.config.model_path),
            language=str(getattr(result, "language", "")) or qwen_language(request.language),
            raw_metadata={"context_used": bool(context), "timestamps_returned": bool(timestamps)},
        )

    def _load_model(self) -> Any:
        if self._model is None:
            self._model = self._loader(
                str(self.config.model_path),
                max_new_tokens=self.config.max_new_tokens,
                **self.config.load_kwargs,
            )
        return self._model

    @staticmethod
    def _default_loader(model_path: str, **kwargs: Any) -> Any:
        try:
            from qwen_asr import Qwen3ASRModel  # type: ignore[reportMissingImports]
        except ImportError as exc:
            raise RuntimeError(
                "Qwen ASR is not installed. Install it in the isolated Qwen environment."
            ) from exc
        return Qwen3ASRModel.from_pretrained(model_path, **kwargs)

    @staticmethod
    def _build_context(request: TranscriptionRequest) -> str:
        parts = []
        if request.glossary:
            parts.append("專有名詞：" + "、".join(request.glossary))
        if request.previous_context:
            parts.append("前段脈絡（僅供理解，不可重複輸出）：" + request.previous_context)
        return "\n".join(parts)

    @staticmethod
    def _to_transcript_segment(item: Any) -> TranscriptSegment:
        return TranscriptSegment(
            text=str(getattr(item, "text", "")),
            start_sec=float(getattr(item, "start_time", 0.0)),
            end_sec=float(getattr(item, "end_time", 0.0)),
        )


class QwenForcedAligner:
    """Lazy Qwen aligner that returns only timing for the supplied transcript."""

    provider_name = "qwen_forced_aligner"

    def __init__(
        self,
        config: QwenForcedAlignerConfig,
        loader: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config
        self._loader = loader or self._default_loader
        self._model: Any | None = None

    def align(self, request: AlignmentRequest) -> AlignmentResult:
        model = self._load_model()
        results = model.align(
            audio=str(request.audio_path),
            text=request.transcript,
            language=qwen_language(request.language) or "Chinese",
        )
        if not results:
            raise RuntimeError("Qwen Forced Aligner returned no alignment result")
        items: Sequence[Any] = getattr(results[0], "items", results[0])
        tokens = tuple(
            AlignedToken(
                text=str(getattr(item, "text", "")),
                start_sec=float(getattr(item, "start_time", 0.0)),
                end_sec=float(getattr(item, "end_time", 0.0)),
            )
            for item in items
        )
        matched_length = sum(len(token.text.replace(" ", "")) for token in tokens)
        source_length = len("".join(request.transcript.split()))
        coverage = min(1.0, matched_length / source_length) if source_length else 1.0
        return AlignmentResult(
            tokens=tokens,
            coverage=coverage,
            provider=self.provider_name,
            model=str(self.config.model_path),
            unmatched_text="" if coverage == 1.0 else request.transcript,
        )

    def _load_model(self) -> Any:
        if self._model is None:
            self._model = self._loader(str(self.config.model_path), **self.config.load_kwargs)
        return self._model

    @staticmethod
    def _default_loader(model_path: str, **kwargs: Any) -> Any:
        try:
            from qwen_asr import Qwen3ForcedAligner  # type: ignore[reportMissingImports]
        except ImportError as exc:
            raise RuntimeError(
                "Qwen ASR is not installed. Install it in the isolated Qwen environment."
            ) from exc
        return Qwen3ForcedAligner.from_pretrained(model_path, **kwargs)
