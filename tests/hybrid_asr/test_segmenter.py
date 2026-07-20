from app.core.hybrid_asr.models import AlignedToken
from app.core.hybrid_asr.segmenter import SubtitleSegmentationConfig, build_subtitle_cues


def test_long_pause_splits_cues() -> None:
    tokens = [
        AlignedToken("大家好", 0.0, 0.8),
        AlignedToken("今天上課", 1.5, 2.4),
    ]
    cues = build_subtitle_cues(tokens)
    assert len(cues) == 2
    assert cues[0].end_sec <= cues[1].start_sec


def test_text_wraps_to_configured_lines() -> None:
    tokens = [AlignedToken("一二三四五六七八", 0.0, 2.0)]
    cues = build_subtitle_cues(
        tokens,
        SubtitleSegmentationConfig(max_chars_per_line=4, max_lines=2),
    )
    assert cues[0].text == "一二三四\n五六七八"
