from pathlib import Path

from app.core.asr.asr_data import ASRData, ASRDataSeg
from app.core.hybrid_asr.models import TranscriptionRequest
from app.core.hybrid_asr.providers import FasterWhisperConfig, FasterWhisperTranscriber


class FakeFasterWhisperASR:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def run(self) -> ASRData:
        return ASRData(
            [
                ASRDataSeg("第一句", 0, 1_200),
                ASRDataSeg("第二句", 1_200, 2_400),
            ]
        )


def test_adapter_reuses_existing_asr_contract_and_converts_timestamps() -> None:
    created: list[FakeFasterWhisperASR] = []

    def factory(**kwargs: object) -> FakeFasterWhisperASR:
        asr = FakeFasterWhisperASR(**kwargs)
        created.append(asr)
        return asr

    transcriber = FasterWhisperTranscriber(
        FasterWhisperConfig(model="large-v3", device="cpu"), asr_factory=factory
    )
    result = transcriber.transcribe(
        TranscriptionRequest(
            audio_path=Path("課程.wav"),
            language="zh",
            glossary=("舍利弗",),
            previous_context="前一段內容",
            word_timestamps=True,
        )
    )

    assert result.text == "第一句第二句"
    assert [(segment.start_sec, segment.end_sec) for segment in result.segments] == [
        (0.0, 1.2),
        (1.2, 2.4),
    ]
    assert created[0].kwargs["whisper_model"] == "large-v3"
    assert created[0].kwargs["need_word_time_stamp"] is True
    assert "舍利弗" in str(created[0].kwargs["prompt"])
    assert "不可重複輸出" in str(created[0].kwargs["prompt"])
