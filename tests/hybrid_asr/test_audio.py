from pathlib import Path

from app.core.hybrid_asr.audio import SilenceInterval, build_segment_plan, choose_split_points, parse_silencedetect


def test_parse_silencedetect() -> None:
    stderr = """
    [silencedetect] silence_start: 895.0
    [silencedetect] silence_end: 899.0 | silence_duration: 4.0
    """
    assert parse_silencedetect(stderr) == [SilenceInterval(895.0, 899.0)]


def test_choose_nearest_silence_to_target() -> None:
    points = choose_split_points(
        1800.0,
        [SilenceInterval(892.0, 896.0), SilenceInterval(920.0, 924.0)],
        target_sec=900.0,
        search_window_sec=30.0,
    )
    assert points == [0.0, 894.0, 1800.0]


def test_segment_plan_adds_overlap_without_exceeding_media() -> None:
    plan = build_segment_plan(
        Path("source.wav"),
        1800.0,
        [SilenceInterval(898.0, 902.0)],
        target_sec=900.0,
        overlap_sec=3.0,
    )
    assert len(plan) == 2
    assert plan[0].start_offset_sec == 0.0
    assert plan[0].end_offset_sec == 903.0
    assert plan[1].start_offset_sec == 897.0
    assert plan[1].end_offset_sec == 1800.0
