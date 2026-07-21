from pathlib import Path
from types import SimpleNamespace

from app.core.hybrid_asr.models import AlignmentRequest, TranscriptionRequest
from app.core.hybrid_asr.providers import (
    QwenASRConfig,
    QwenForcedAligner,
    QwenForcedAlignerConfig,
    QwenTranscriber,
)


class FakeASRModel:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def transcribe(self, **kwargs: object) -> list[SimpleNamespace]:
        self.calls.append(kwargs)
        return [
            SimpleNamespace(
                text="彌勒佛說法",
                language="Chinese",
                time_stamps=[
                    SimpleNamespace(text="彌勒佛", start_time=0.2, end_time=0.9),
                    SimpleNamespace(text="說法", start_time=1.0, end_time=1.4),
                ],
            )
        ]


class FakeAlignerModel:
    def align(self, **kwargs: object) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                items=[SimpleNamespace(text="彌勒佛", start_time=0.2, end_time=0.9)]
            )
        ]


def test_qwen_transcriber_loads_once_and_passes_context() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    fake = FakeASRModel()

    def loader(path: str, **kwargs: object) -> FakeASRModel:
        calls.append((path, kwargs))
        return fake

    transcriber = QwenTranscriber(QwenASRConfig(Path("model")), loader=loader)
    request = TranscriptionRequest(
        audio_path=Path("語音.wav"),
        language="zh",
        glossary=("彌勒佛",),
        previous_context="前段內容",
        word_timestamps=True,
    )
    first = transcriber.transcribe(request)
    second = transcriber.transcribe(request)

    assert len(calls) == 1
    assert first.text == "彌勒佛說法"
    assert second.segments[0].start_sec == 0.2
    assert fake.calls[0]["language"] == "Chinese"
    assert "不可重複輸出" in str(fake.calls[0]["context"])


def test_qwen_aligner_preserves_transcript_text() -> None:
    aligner = QwenForcedAligner(
        QwenForcedAlignerConfig(Path("aligner")), loader=lambda *_args, **_kwargs: FakeAlignerModel()
    )
    request = AlignmentRequest(audio_path=Path("語音.wav"), transcript="彌勒佛", language="zh")

    result = aligner.align(request)

    assert result.tokens[0].text == request.transcript
    assert result.coverage == 1.0
