from app.core.hybrid_asr.models import AlignmentResult
from app.core.hybrid_asr.quality import inspect_transcript, repeated_ngram_ratio


def test_repetition_ratio_detects_looping_text() -> None:
    assert repeated_ngram_ratio("所以所以所以所以所以") > repeated_ngram_ratio("今天我們開始上課")


def test_low_alignment_coverage_is_error() -> None:
    alignment = AlignmentResult(tokens=(), coverage=0.5, provider="test", model="test")
    issues = inspect_transcript("這是一段正常長度的逐字稿", 10.0, alignment=alignment)
    assert any(issue.code == "alignment_failed" and issue.severity == "error" for issue in issues)


def test_empty_long_audio_is_flagged() -> None:
    issues = inspect_transcript("", 60.0)
    assert any(issue.code == "low_text_density" for issue in issues)
