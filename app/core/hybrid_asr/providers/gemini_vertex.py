"""Optional Gemini transcription through Vertex AI.

This provider deliberately uses Application Default Credentials (ADC), rather
than a Gemini Developer API key, so usage is charged to the selected Google
Cloud billing project and its applicable credits.
"""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..models import TranscriptionRequest, TranscriptionResult, TranscriptSegment, UsageMetrics
from ..pricing import TokenPricing, estimate_token_cost


@dataclass(frozen=True, slots=True)
class GeminiVertexConfig:
    """Configuration for a full-cloud Gemini transcription mode.

    ``pricing`` is intentionally explicit. Check the Vertex AI pricing page and
    update it before a new processing run; Vertex Cloud Billing remains the
    authoritative source for charged and credit-offset amounts.
    """

    project: str | None = None
    location: str = "global"
    model: str = "gemini-2.5-flash"
    pricing: TokenPricing = field(
        default_factory=lambda: TokenPricing(
            input_usd_per_million=1.0,
            output_usd_per_million=2.5,
            pricing_version="vertex-gemini-2.5-flash-audio-2026-07-21",
        )
    )
    generation_config: dict[str, Any] = field(default_factory=dict)


class GeminiVertexTranscriber:
    """Lazy Vertex AI Gemini adapter with provider usage and cost metadata."""

    provider_name = "gemini_vertex"

    def __init__(
        self,
        config: GeminiVertexConfig = GeminiVertexConfig(),
        client_factory: Callable[[GeminiVertexConfig], Any] | None = None,
        part_factory: Callable[[Path], Any] | None = None,
    ) -> None:
        self.config = config
        self._client_factory = client_factory or self._default_client_factory
        self._part_factory = part_factory or self._default_part_factory
        self._client: Any | None = None

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        response = self._client_instance().models.generate_content(
            model=self.config.model,
            contents=[self._prompt(request), self._part_factory(request.audio_path)],
            config=self._generation_config(),
        )
        text = str(getattr(response, "text", "")).strip()
        if not text:
            raise RuntimeError("Vertex AI Gemini returned an empty transcription")

        usage = self._usage_metrics(getattr(response, "usage_metadata", None))
        estimate = estimate_token_cost(usage, self.config.pricing) if usage is not None else None
        raw_metadata: dict[str, Any] = {
            "usage_reported": usage is not None,
            "pricing_version": self.config.pricing.pricing_version,
        }
        if estimate is not None:
            raw_metadata.update(
                {
                    "estimated_cost_usd": estimate.estimated_cost_usd,
                    "input_tokens": estimate.input_tokens,
                    "output_tokens": estimate.output_tokens,
                    "cached_input_tokens": estimate.cached_input_tokens,
                }
            )
        return TranscriptionResult(
            text=text,
            segments=(TranscriptSegment(text),),
            provider=self.provider_name,
            model=self.config.model,
            language=request.language,
            usage=usage,
            raw_metadata=raw_metadata,
        )

    def _client_instance(self) -> Any:
        if self._client is None:
            self._client = self._client_factory(self.config)
        return self._client

    def _generation_config(self) -> dict[str, Any]:
        # Keep transcription deterministic; callers can add supported Gemini
        # options through configuration without coupling the core to SDK types.
        return {"temperature": 0, **self.config.generation_config}

    @staticmethod
    def _prompt(request: TranscriptionRequest) -> str:
        terms = "、".join(request.glossary)
        context = request.previous_context or ""
        prompt = [
            "請將音訊忠實轉錄為繁體中文文字。",
            "不得摘要、改寫、補充未說出的內容或調整語句順序。",
            "聽不清楚的內容請標記為 [聽不清]，不可猜測。",
        ]
        if terms:
            prompt.append(f"優先採用這些專有名詞：{terms}。")
        if context:
            prompt.append(
                "以下僅供理解前段脈絡，絕對不可重複輸出："
                f"\n<context>{context}</context>"
            )
        return "\n".join(prompt)

    @staticmethod
    def _usage_metrics(metadata: Any) -> UsageMetrics | None:
        if metadata is None:
            return None

        def number(name: str) -> int | None:
            value = getattr(metadata, name, None)
            return int(value) if value is not None else None

        return UsageMetrics(
            input_tokens=number("prompt_token_count"),
            output_tokens=number("candidates_token_count"),
            reasoning_tokens=number("thoughts_token_count"),
            cached_input_tokens=number("cached_content_token_count"),
        )

    @staticmethod
    def _default_client_factory(config: GeminiVertexConfig) -> Any:
        try:
            from google import genai  # type: ignore[reportMissingImports]
        except ImportError as exc:
            raise RuntimeError(
                "Vertex AI Gemini requires the optional dependency 'google-genai'."
            ) from exc
        return genai.Client(vertexai=True, project=config.project, location=config.location)

    @staticmethod
    def _default_part_factory(audio_path: Path) -> Any:
        try:
            from google.genai import types  # type: ignore[reportMissingImports]
        except ImportError as exc:
            raise RuntimeError(
                "Vertex AI Gemini requires the optional dependency 'google-genai'."
            ) from exc
        mime_type, _ = mimetypes.guess_type(audio_path.name)
        return types.Part.from_bytes(
            data=audio_path.read_bytes(),
            mime_type=mime_type or "audio/wav",
        )
