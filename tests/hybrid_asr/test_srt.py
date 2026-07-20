from pathlib import Path

import pytest

from app.core.hybrid_asr.models import SubtitleCue
from app.core.hybrid_asr.srt import format_srt_timestamp, render_srt, validate_cues, write_srt_atomic


def test_format_srt_timestamp_rounds_milliseconds() -> None:
    assert format_srt_timestamp(3661.2346) == "01:01:01,235"


def test_render_srt() -> None:
    cues = [SubtitleCue(1, 0.5, 2.0, "大家好"), SubtitleCue(2, 2.1, 4.0, "歡迎回來")]
    text = render_srt(cues)
    assert "00:00:00,500 --> 00:00:02,000" in text
    assert "歡迎回來" in text


def test_validate_rejects_overlap() -> None:
    cues = [SubtitleCue(1, 0.0, 2.0, "一"), SubtitleCue(2, 1.9, 3.0, "二")]
    with pytest.raises(ValueError, match="overlaps"):
        validate_cues(cues)


def test_atomic_writer_leaves_no_partial_file(tmp_path: Path) -> None:
    output = tmp_path / "中文檔名.srt"
    write_srt_atomic(output, [SubtitleCue(1, 0.0, 1.0, "測試")], media_duration_sec=1.0)
    assert output.exists()
    assert not output.with_suffix(".srt.partial").exists()
    assert "測試" in output.read_text(encoding="utf-8-sig")
