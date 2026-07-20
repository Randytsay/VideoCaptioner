from app.core.hybrid_asr.models import AlignedToken, AlignmentResult, SRTCue
from app.core.hybrid_asr.quality import check_alignment, check_cues, check_transcript_density


def test_quality_flags_low_alignment_coverage_and_bad_cues():
    alignment = AlignmentResult("test", (AlignedToken("大家", 0, 1),), "大家好今天")
    assert not check_alignment(alignment).passed
    assert not check_cues([SRTCue(0, 2, "甲"), SRTCue(1, 3, "乙")], 5).passed
    assert not check_transcript_density("很短", 600).passed
