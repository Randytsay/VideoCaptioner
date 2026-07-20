# Hybrid ASR work status and agent takeover guide

## Authoritative project state

This document is the authoritative summary of work completed on the Hybrid ASR initiative.

- Repository: `Randytsay/VideoCaptioner`
- Working branch: `agent/hybrid-asr-core`
- Draft pull request: `#1`
- Base branch: `master`
- Do not merge the draft PR until the complete repository test suite, real model tests, and regression checks pass.

The current branch intentionally isolates the new Hybrid ASR foundation from the existing production GUI and transcription paths. Existing VideoCaptioner behavior has not been switched over to the new pipeline.

## Repository areas reviewed

The following existing implementation areas were re-read before this handoff was prepared:

- `app/core/asr/transcribe.py`
  - Existing ASR dispatch supports JianYing, Bcut, whisper.cpp, Whisper API, and Faster Whisper.
  - There is no Qwen provider currently integrated into the repository ASR dispatcher.
- `app/core/asr/asr_data.py`
  - Existing subtitle data structure, word/character timestamp handling, Traditional Chinese conversion, custom mapping, and SRT export.
- `app/core/task_factory.py`
  - Existing Whisper prompt-file selection and prompt formatting.
  - Existing output-path rules and transcription configuration creation.
- `app/thread/transcript_thread.py`
  - Existing GUI transcription workflow, temporary audio conversion, Traditional Chinese conversion, custom dictionary application, and output export.
- `app/thread/batch_process_thread.py`
  - Existing PyQt batch queue, task progress, task duration, processing speed, and task chaining.
- `app/core/entities.py`
  - Existing transcription, subtitle, and task configuration models.
- `pyproject.toml`
  - Python 3.10–3.12, PyQt5, pytest, Ruff, and Pyright configuration.

These existing modules must be reused or adapted where practical. Do not build a second independent model-loading, prompt, dictionary, or batch system unless separation is necessary for dependency isolation.

## Completed Hybrid ASR foundation

### 1. Development and safety rules

File:

- `AGENTS.md`

Completed rules include:

- preserve existing user-facing behavior;
- do not commit credentials, model weights, private media, databases, logs, or temporary audio;
- keep ASR, forced alignment, subtitle segmentation, persistence, and GUI concerns separate;
- forced alignment must never rewrite transcript text;
- core modules must not import PyQt;
- use dependency injection for providers;
- require tests for new features;
- use atomic subtitle writes;
- retain Windows, macOS, Linux, Unicode-path, and Traditional Chinese compatibility.

### 2. Shared data models

File:

- `app/core/hybrid_asr/models.py`

Completed models:

- `AudioSegment`
- `TranscriptSegment`
- `TranscriptionRequest`
- `TranscriptionResult`
- `AlignmentRequest`
- `AlignedToken`
- `AlignmentResult`
- `SubtitleCue`

The models validate negative timestamps, invalid ranges, invalid cue indexes, empty subtitles, and alignment coverage outside 0–1.

### 3. Provider protocols

File:

- `app/core/hybrid_asr/interfaces.py`

Completed protocols:

- `Transcriber`
- `ForcedAligner`

The contract explicitly separates transcription from alignment. A forced aligner assigns timing only and must not change the supplied text.

### 4. FFmpeg and audio segmentation foundation

File:

- `app/core/hybrid_asr/audio.py`

Completed implementation:

- executable discovery for FFmpeg and ffprobe;
- media-duration probing;
- conversion to mono 16 kHz PCM WAV;
- FFmpeg `silencedetect` invocation;
- silence-output parsing;
- split-point selection near target boundaries;
- fallback hard splitting when no suitable silence exists;
- configurable overlap planning;
- real WAV segment extraction;
- materialization of a segment plan;
- cleanup of already-created segment files when materialization fails.

Still required: real installed-FFmpeg validation, integration tests, actual duration/sample-rate verification, and Windows/macOS Unicode-path testing.

### 5. Recursive media scanning and file stability

File:

- `app/core/hybrid_asr/scanner.py`

Completed implementation:

- recursive and non-recursive media discovery;
- configurable extensions;
- optional skip when an SRT already exists;
- deterministic path sorting;
- file snapshots containing size, modified time, and observation time;
- stable-file decision based on unchanged size/mtime and minimum file age.

This is intended to prevent processing Google Drive files that are still being synchronized.

### 6. Glossary foundation

File:

- `app/core/hybrid_asr/glossary.py`

Completed implementation:

- UTF-8/UTF-8-BOM CSV loading;
- required `wrong_term` and `correct_term` columns;
- optional `note`, `match_mode`, and `enabled` columns;
- supported modes:
  - `prompt_only`
  - `exact`
  - `contains`
  - `regex`
  - `review_only`
- glossary merging;
- deterministic version hash;
- provider prompt-term generation;
- deterministic correction results;
- replacement audit records;
- review-only hit reporting;
- regular-expression validation;
- replacement-count limits.

Important limitation: repository-level folder-to-glossary selection and integration with the existing prompt/custom-dictionary UI have not been completed.

### 7. Subtitle segmentation

File:

- `app/core/hybrid_asr/segmenter.py`

Completed implementation:

- pause-based splitting;
- terminal-punctuation splitting;
- soft-punctuation splitting;
- maximum characters per cue;
- maximum duration;
- minimum duration;
- maximum reading speed;
- configurable line width and line count;
- prevention of text loss when one token is longer than the visual cue limit;
- prevention of cue overlap with the next group;
- media-duration clamping.

### 8. SRT rendering and atomic output

File:

- `app/core/hybrid_asr/srt.py`

Completed implementation:

- SRT timestamp formatting;
- cue index validation;
- overlap/backward-time validation;
- media-duration validation;
- SRT rendering;
- UTF-8 BOM output by default;
- `.partial` temporary output followed by `os.replace` atomic promotion;
- cleanup of partial output after failure.

### 9. Deterministic quality checks

File:

- `app/core/hybrid_asr/quality.py`

Completed implementation:

- minimum text-density warning;
- excessive text-density/hallucination warning;
- repeated n-gram ratio detection;
- alignment warning and failure thresholds;
- timestamp overlap/backward-time detection;
- configurable quality thresholds.

Still required: unmatched-token ratio, cross-segment repetition, source-ending coverage, glossary-error signals, and decision policies for Qwen/Gemini/Whisper fallback.

### 10. SQLite resumable-job foundation

File:

- `app/core/hybrid_asr/persistence.py`

Completed schema and operations:

- WAL journal mode;
- schema version tracking;
- `media_files`;
- `segments`;
- `transcription_attempts`;
- `alignment_results`;
- `usage_records`;
- `review_items`;
- media fingerprinting using file size, modification time, and partial SHA-256;
- media upsert;
- segment upsert;
- segment start, completion, failure, retry count, and interruption recovery;
- pending-segment query;
- transcription attempt creation/completion;
- alignment result records;
- usage and estimated-cost records;
- review-item creation and resolution;
- basic incremental-column migration support.

Fingerprint invalidation is now covered by a regression test. When a source path
receives a different fingerprint, its existing segments are deleted before the
media record is updated; SQLite foreign-key cascading removes segment attempts,
alignment records, per-segment usage, and review items. Changed media therefore
cannot reuse old transcript or alignment results. Media-level usage remains as
historical billing audit data.

### 11. Injectable segment processing pipeline

File:

- `app/core/hybrid_asr/pipeline.py`

Completed implementation:

- injected `Transcriber`;
- optional injected `ForcedAligner`;
- provider prompt terms from the glossary;
- previous-context forwarding;
- glossary correction before alignment;
- relative-to-global timestamp offset conversion;
- subtitle-cue construction;
- deterministic quality checks;
- glossary review warnings;
- fallback to transcription-provided timestamps when no forced aligner exists.

Important limitation: this processes one prepared segment only. It is not yet the whole-file, multi-segment, resumable orchestrator.

### 12. Package exports

File:

- `app/core/hybrid_asr/__init__.py`

Exports the completed core models, protocols, glossary types, scanner types, segment pipeline, and subtitle segmenter.

### 13. Existing FasterWhisper adapter

File:

- `app/core/hybrid_asr/providers/faster_whisper.py`

Completed implementation:

- reuses the existing `app.core.asr.faster_whisper.FasterWhisperASR` contract;
- maps Hybrid ASR transcription requests, glossary terms, context, language,
  device, VAD, and word-timestamp settings into the existing adapter;
- converts existing millisecond timestamps into provider-neutral seconds;
- uses dependency injection for model-free tests.

Known limitation: the existing FasterWhisper standalone binary owns model
lifetime, so one prepared segment currently starts one binary process. This has
not been validated with a locally installed FasterWhisper model.

### 14. Tests added

Directory:

- `tests/hybrid_asr/`

Added tests cover:

- SRT rendering, overlap rejection, atomic output, and Chinese filenames;
- transcript quality and alignment thresholds;
- silence-output parsing and split planning;
- file fingerprinting and resumable-segment behavior;
- glossary correction, review-only entries, CSV loading, and deterministic hashes;
- file scanning and stability checks;
- subtitle splitting and long-token text preservation;
- injected fake transcriber/aligner pipeline behavior.

Some isolated tests were reconstructed and run outside a full repository checkout, including glossary, scanner, segmenter, and injected-pipeline tests. This is not equivalent to validating the complete branch.

## Validation that has not been completed

The following commands still need to be run on a complete local checkout:

```bash
uv sync
uv run pytest tests/hybrid_asr -v
uv run ruff check app/core/hybrid_asr tests/hybrid_asr
uv run pyright app/core/hybrid_asr
uv run pytest
```

The branch must not be considered production-ready until those commands pass or all failures are documented and resolved.

## Work explicitly not completed

The following are not implemented or not validated:

1. Qwen ASR provider.
2. Real Qwen model loading and device selection.
3. Real FasterWhisper model loading and device validation.
4. Qwen Forced Aligner provider.
5. Display-text/alignment-text reversible normalization.
6. Real Chinese, mixed-language, sutra, and mantra alignment tests.
7. Vertex AI Gemini transcription provider.
8. Application Default Credentials validation.
9. API retry and pricing logic.
10. Full multi-segment orchestrator.
11. Cross-segment overlap-text removal.
12. Previous-context carry between segments at whole-file level.
13. SQLite integration with the segment pipeline.
14. Folder batch CLI.
15. Smart Qwen → Gemini → Whisper fallback decisions.
16. Existing VideoCaptioner GUI integration.
17. Pause/resume/cancel UI.
18. Packaging and executable regression tests.
19. Long-video end-to-end validation.
20. Full existing-feature regression testing.

## Required agent takeover order

The next agent must proceed in this order:

1. Reconcile the legacy `ChunkedASR` test/API contract, then obtain a clean full-suite baseline.
2. Validate the FasterWhisper adapter with an installed local model.
3. Locate the user's installed Qwen environment and integrate Qwen without duplicating model loading.
4. Integrate and validate Qwen Forced Aligner.
5. Add reversible alignment-text normalization.
6. Build whole-file orchestration and CLI with SQLite resume support.
7. Add Vertex AI Gemini.
8. Implement smart fallback decisions.
9. Perform real-world validation.
10. Add the Traditional Chinese GUI only after CLI end-to-end tests pass.

## Do not redo or replace without evidence

Do not rewrite the following merely for stylistic preference:

- shared data models;
- provider protocols;
- FFmpeg split planning;
- scanner and file-stability logic;
- glossary CSV parser and audit model;
- deterministic subtitle segmenter;
- SRT atomic writer;
- quality-check foundation;
- SQLite schema and repository foundation;
- injected segment pipeline.

Changes are appropriate only to fix verified defects, satisfy integration requirements, or pass repository tests.

## Agent completion report

For every phase, report:

1. files changed;
2. commands executed;
3. tests passed, failed, and skipped;
4. whether real FFmpeg, Qwen, Whisper, aligner, Gemini, and real media were used;
5. any mocks still present;
6. package versions and device used;
7. processing duration, media duration, alignment coverage, cue count, and last cue end time;
8. known dependency conflicts;
9. existing VideoCaptioner features regression-tested;
10. commit SHA and whether Draft PR #1 is ready to merge.
