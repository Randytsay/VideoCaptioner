from pathlib import Path

from app.core.hybrid_asr.glossary import Glossary, GlossaryEntry
from app.core.hybrid_asr.models import (
    AlignedToken,
    AlignmentResult,
    AudioSegment,
    TranscriptSegment,
    TranscriptionResult,
)
from app.core.hybrid_asr.pipeline import SegmentPipeline


class FakeTranscriber:
    provider_name = "fake"

    def transcribe(self, _request):
        return TranscriptionResult(
            text="見信成佛",
            segments=[TranscriptSegment("見信成佛", 0.0, 2.0)],
            provider="fake",
            model="fake",
        )


class FakeAligner:
    provider_name = "fake-aligner"

    def align(self, request):
        assert request.transcript == "見性成佛"
        return AlignmentResult(
            tokens=(AlignedToken("見性成佛", 0.2, 1.8),),
            coverage=1.0,
            provider="fake-aligner",
            model="fake",
        )


def test_pipeline_corrects_then_aligns_and_offsets() -> None:
    pipeline = SegmentPipeline(
        FakeTranscriber(),
        FakeAligner(),
        Glossary([GlossaryEntry("見信成佛", "見性成佛")]),
    )
    result = pipeline.process(
        AudioSegment("segment_0001", Path("segment.wav"), 10.0, 20.0)
    )
    assert result.glossary_result.text == "見性成佛"
    assert result.alignment is not None
    assert result.alignment.tokens[0].start_sec == 10.2
    assert result.cues[0].text == "見性成佛"
