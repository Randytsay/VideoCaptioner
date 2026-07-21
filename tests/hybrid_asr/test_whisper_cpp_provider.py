from pathlib import Path

from app.core.asr.asr_data import ASRData, ASRDataSeg
from app.core.hybrid_asr.models import TranscriptionRequest
from app.core.hybrid_asr.providers import WhisperCppConfig, WhisperCppTranscriber


class FakeWhisperCppASR:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def run(self) -> ASRData:
        return ASRData([ASRDataSeg("本機辨識", 500, 1_500)])


def test_adapter_reports_existing_whisper_cpp_prompt_limitations() -> None:
    created: list[FakeWhisperCppASR] = []

    def factory(**kwargs: object) -> FakeWhisperCppASR:
        asr = FakeWhisperCppASR(**kwargs)
        created.append(asr)
        return asr

    transcriber = WhisperCppTranscriber(
        WhisperCppConfig(model="large-v3", executable="whisper-cli"), asr_factory=factory
    )
    result = transcriber.transcribe(
        TranscriptionRequest(
            audio_path=Path("語音.wav"),
            language="zh",
            glossary=("彌勒佛",),
            previous_context="前段",
            word_timestamps=True,
        )
    )

    assert result.text == "本機辨識"
    assert result.segments[0].start_sec == 0.5
    assert len(result.warnings) == 2
    assert created[0].kwargs["whisper_cpp_path"] == "whisper-cli"
    assert created[0].kwargs["need_word_time_stamp"] is True
