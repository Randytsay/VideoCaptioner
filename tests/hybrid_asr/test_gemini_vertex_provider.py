from pathlib import Path
from types import SimpleNamespace

from app.core.hybrid_asr.models import TranscriptionRequest
from app.core.hybrid_asr.providers import GeminiVertexConfig, GeminiVertexTranscriber


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            text="彌勒佛說法",
            usage_metadata=SimpleNamespace(
                prompt_token_count=2_000,
                candidates_token_count=100,
                thoughts_token_count=10,
                cached_content_token_count=500,
            ),
        )


def test_gemini_vertex_uses_injected_client_and_reports_usage() -> None:
    models = FakeModels()
    factory_calls: list[GeminiVertexConfig] = []

    def client_factory(config: GeminiVertexConfig) -> SimpleNamespace:
        factory_calls.append(config)
        return SimpleNamespace(models=models)

    transcriber = GeminiVertexTranscriber(
        GeminiVertexConfig(project="caption-project"),
        client_factory=client_factory,
        part_factory=lambda path: {"audio_path": str(path)},
    )
    request = TranscriptionRequest(
        audio_path=Path("講課.wav"),
        language="zh",
        glossary=("彌勒佛",),
        previous_context="上一段內容",
    )

    first = transcriber.transcribe(request)
    second = transcriber.transcribe(request)

    assert len(factory_calls) == 1
    assert first.text == "彌勒佛說法"
    assert first.usage is not None
    assert first.usage.input_tokens == 2_000
    assert first.usage.output_tokens == 100
    assert first.usage.reasoning_tokens == 10
    assert first.raw_metadata["estimated_cost_usd"] == 0.002275
    assert second.model == "gemini-2.5-flash"
    prompt = str(models.calls[0]["contents"])
    assert "不可重複輸出" in prompt
    assert "彌勒佛" in prompt
    assert models.calls[0]["config"] == {"temperature": 0}
