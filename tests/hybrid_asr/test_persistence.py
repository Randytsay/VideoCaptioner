from app.core.hybrid_asr.models import AudioSegment
from app.core.hybrid_asr.persistence import JobRepository, file_fingerprint


def test_repository_resets_segments_when_source_changes(tmp_path):
    source = tmp_path / "測試.wav"
    source.write_bytes(b"one")
    repository = JobRepository(tmp_path / "jobs.db")
    first = repository.register_media(source, file_fingerprint(source), [AudioSegment("1", 0, 10)])
    row = repository.pending_segments(first)[0]
    repository.set_segment_status(row["id"], "done")

    source.write_bytes(b"changed")
    second = repository.register_media(source, file_fingerprint(source), [AudioSegment("1", 0, 10)])

    assert len(repository.pending_segments(second)) == 1
    repository.close()
