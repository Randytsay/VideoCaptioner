import shutil
from pathlib import Path

import pytest

from app.core.hybrid_asr.audio import (
    extract_normalized_audio,
    materialize_segments,
    media_duration,
    plan_segments,
)


def test_plan_segments_prefers_nearby_silence_and_adds_overlap():
    segments = plan_segments(1_850, [880, 1_770], target_sec=900, search_window_sec=30, overlap_sec=3)

    assert [(segment.start_offset_sec, segment.end_offset_sec) for segment in segments] == [
        (0.0, 883), (877, 1_773), (1767, 1850),
    ]


def test_plan_segments_hard_cuts_when_no_silence_is_available():
    segments = plan_segments(1_000, target_sec=600, overlap_sec=2)

    assert [(segment.start_offset_sec, segment.end_offset_sec) for segment in segments] == [(0.0, 602), (598, 1000)]


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="FFmpeg unavailable")
def test_ffmpeg_normalizes_and_materializes_unicode_paths(tmp_path):
    source = tmp_path / "來源" / "測試音訊.mp3"
    source.parent.mkdir()
    fixture = Path(__file__).parents[1] / "fixtures" / "audio" / "zh.mp3"
    shutil.copy2(fixture, source)
    normalized = extract_normalized_audio(source, tmp_path / "輸出" / "正規.wav")
    duration = media_duration(normalized)
    outputs = materialize_segments(normalized, tmp_path / "切段", plan_segments(duration, target_sec=1, overlap_sec=0))

    assert duration > 0
    assert outputs
    assert all(segment.audio_path and segment.audio_path.is_file() for segment in outputs)
