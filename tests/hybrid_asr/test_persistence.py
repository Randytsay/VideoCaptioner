from pathlib import Path

from app.core.hybrid_asr.persistence import SCHEMA_VERSION, JobRepository, fingerprint_file


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


def test_repository_records_attempt_alignment_usage_and_review(tmp_path: Path) -> None:
    source = tmp_path / "課程.wav"
    source.write_bytes(b"audio")
    repository = JobRepository(tmp_path / "jobs.db")
    assert repository.schema_version() == SCHEMA_VERSION

    media_id = repository.upsert_media_file(source, fingerprint_file(source))
    segment_id = repository.upsert_segment(media_id, "segment_0001", 0.0, 10.0)
    attempt_id = repository.create_transcription_attempt(segment_id, "qwen", "test-model")
    repository.finish_transcription_attempt(
        attempt_id,
        status="done",
        transcript_text="逐字稿",
    )
    assert repository.record_alignment(
        segment_id,
        provider="qwen-aligner",
        model="test-aligner",
        coverage=0.95,
    ) > 0
    assert repository.record_usage(
        media_file_id=media_id,
        segment_id=segment_id,
        provider="gemini",
        model="test-model",
        estimated_cost_usd=0.01,
        pricing_version="test",
    ) > 0
    review_id = repository.add_review_item(
        media_id,
        "glossary_review",
        segment_id=segment_id,
    )
    repository.resolve_review_item(review_id)


def test_processing_segment_can_be_recovered_as_interrupted(tmp_path: Path) -> None:
    source = tmp_path / "課程.wav"
    source.write_bytes(b"audio")
    repository = JobRepository(tmp_path / "jobs.db")
    media_id = repository.upsert_media_file(source, fingerprint_file(source))
    segment_id = repository.upsert_segment(media_id, "segment_0001", 0.0, 10.0)
    repository.start_segment(segment_id)

    assert repository.recover_interrupted("9999-12-31T23:59:59+00:00") == 1
    pending = repository.pending_segments(media_id)
    assert pending[0]["status"] == "interrupted"
