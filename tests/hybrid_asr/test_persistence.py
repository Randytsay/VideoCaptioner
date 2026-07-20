from pathlib import Path

from app.core.hybrid_asr.persistence import JobRepository, fingerprint_file


def test_fingerprint_changes_when_content_changes(tmp_path: Path) -> None:
    source = tmp_path / "影片.wav"
    source.write_bytes(b"first")
    first = fingerprint_file(source)
    source.write_bytes(b"second")
    second = fingerprint_file(source)
    assert first.value != second.value


def test_repository_resumes_only_unfinished_segments(tmp_path: Path) -> None:
    source = tmp_path / "影片.wav"
    source.write_bytes(b"audio")
    repository = JobRepository(tmp_path / "jobs.db")
    media_id = repository.upsert_media_file(source, fingerprint_file(source), provider="qwen")
    first = repository.upsert_segment(media_id, "segment_0001", 0.0, 10.0)
    second = repository.upsert_segment(media_id, "segment_0002", 10.0, 20.0)
    repository.complete_segment(first, "完成", 0.98)
    repository.fail_segment(second, "temporary failure")

    pending = repository.pending_segments(media_id)
    assert [row["segment_key"] for row in pending] == ["segment_0002"]
