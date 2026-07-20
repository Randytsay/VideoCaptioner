import pytest

from app.core.hybrid_asr.models import SRTCue
from app.core.hybrid_asr.srt import render_srt, write_srt_atomic


def test_write_srt_atomically_with_unicode_path(tmp_path):
    output = tmp_path / "字幕" / "測試.srt"
    write_srt_atomic(output, [SRTCue(0, 1.2, "你好")], media_duration_sec=2)

    assert output.read_text(encoding="utf-8") == "1\n00:00:00,000 --> 00:00:01,200\n你好\n"
    assert not output.with_suffix(".srt.partial").exists()


def test_render_rejects_overlapping_cues():
    with pytest.raises(ValueError, match="overlap"):
        render_srt([SRTCue(0, 2, "甲"), SRTCue(1, 3, "乙")])
