# Codex handoff: Hybrid ASR remaining work

## Current branch

`agent/hybrid-asr-core`

The branch now contains a model-agnostic hybrid-ASR foundation. Existing VideoCaptioner GUI and production ASR paths have not been changed.

## Completed in the branch

- Development rules in `AGENTS.md`.
- Shared transcription, alignment, audio-segment, and subtitle data models.
- `Transcriber` and `ForcedAligner` protocols.
- FFmpeg/ffprobe helpers for probing duration, normalization, silence detection, split planning, and segment extraction.
- Recursive media scanning and file-stability checks.
- Glossary CSV loading, merge, prompt terms, deterministic corrections, review-only terms, and version hashing.
- Deterministic subtitle segmentation with pause, punctuation, duration, line-length, and reading-speed rules.
- Deterministic transcript quality checks.
- SRT rendering, validation, and atomic output.
- SQLite schema for media, segments, transcription attempts, alignment results, usage, and review items.
- Segment-level status, retry, interruption recovery, attempt history, usage records, and review records.
- Injectable single-segment processing pipeline using fake providers in tests.
- Focused unit tests and validation notes.

## Known issue to verify or fix first

When an existing source path receives a different fingerprint, `media_files.status` is reset to `pending`, but existing segment rows may still need explicit invalidation/deletion. Add a regression test and ensure changed media can never reuse stale completed segment results.

## Mandatory first task: validate the complete repository

Run from the repository root:

```bash
uv sync
uv run pytest tests/hybrid_asr -v
uv run ruff check app/core/hybrid_asr tests/hybrid_asr
uv run pyright app/core/hybrid_asr
uv run pytest
```

Fix compatibility, formatting, typing, import, migration, and regression failures. Do not weaken tests merely to make them pass. Record exact command output in `docs/hybrid-asr-validation.md`.

## Task 1: inspect and reuse existing VideoCaptioner implementations

Locate and document the current repository implementations for:

- Qwen ASR;
- Whisper/faster-whisper/whisper.cpp;
- model loading and device selection;
- FFmpeg utilities;
- subtitle entities and writers;
- custom dictionaries and prompt files;
- batch task execution and GUI threads.

Do not create duplicate model-loading systems when existing code can be adapted.

## Task 2: finish real FFmpeg validation

Although core commands exist, validate them against installed FFmpeg/ffprobe and real media.

Acceptance criteria:

- Unicode Windows and macOS paths work.
- Silence detection output is parsed correctly on actual FFmpeg output.
- Extracted segments have the expected duration, sample rate, and channel count.
- Temporary files are cleaned on success and failure.
- Integration tests are marked `slow` and skip clearly when FFmpeg is unavailable.

## Task 3: adapt existing Qwen and Whisper implementations

Create providers implementing `Transcriber`:

- `QwenTranscriber`
- `WhisperTranscriber`

Acceptance criteria:

- Reuse current model loading and transcription logic.
- Support language, prompt/glossary, previous context, and optional word timestamps.
- Return `TranscriptionResult` consistently.
- Load each model once rather than once per segment.
- Provide mock unit tests and real local integration tests.
- Record installed package versions, device, model path/name, media duration, elapsed time, and output sample.

## Task 4: integrate Qwen forced alignment

Create a provider implementing `ForcedAligner` using the installed Qwen forced-aligner model/API.

Critical rule: the aligner assigns timestamps only. It must not replace, paraphrase, or correct transcript text.

Acceptance criteria:

- Support Traditional Chinese and mixed English.
- Create a reversible mapping between display text and alignment text.
- Normalize punctuation, spaces, numbers, English case, and symbols while preserving display text.
- Return token/character times, confidence when available, coverage, and unmatched text.
- Test with real Chinese speech, sutra reading, and the recurring mantra ending.
- Explicitly document unsupported characters and package-version constraints.

## Task 5: complete orchestration and CLI

Build the full model-independent pipeline around the existing core:

1. file scan and stability check;
2. fingerprint and resume decision;
3. normalization and smart segmentation;
4. transcription;
5. glossary processing;
6. forced alignment;
7. quality checks;
8. retry/fallback decision;
9. cue merge and cross-segment overlap removal;
10. atomic SRT output;
11. SQLite updates.

CLI requirements:

```bash
python -m app.core.hybrid_asr.cli --single-file path/to/video.mp4 --mode qwen_local
python -m app.core.hybrid_asr.cli --root path/to/folder --mode hybrid_smart --resume
```

Add `--dry-run`, `--retry-failed`, and `--review-needed`.

## Task 6: integrate Vertex AI Gemini

Use the current official Google Gen AI SDK in Vertex AI mode, not an AI Studio API-key workflow.

Acceptance criteria:

- Application Default Credentials first; optional `GOOGLE_APPLICATION_CREDENTIALS`.
- Faithful transcript prompt: no summarizing, rewriting, or invented content.
- Previous context is reference-only and must not be repeated.
- Gemini timestamps are rough metadata, not final SRT timing.
- Retry 429 and transient 5xx separately from quality retries.
- Record reported usage and estimated cost with a pricing-version field.
- Provide mock tests and one opt-in real integration test.

## Task 7: implement smart hybrid decisions

Default decision flow:

- Qwen local transcription first.
- Accept healthy segments after deterministic checks.
- Send only suspicious segments to Gemini.
- Re-align Gemini text locally.
- Use Whisper as fallback/second opinion, not as authority over accepted Gemini text.

All thresholds must be configurable. Log every provider decision and reason.

## Task 8: integrate with the existing GUI

Only after CLI end-to-end tests pass, add a Traditional Chinese “智慧批次字幕” page.

Requirements:

- Select root folder and processing mode.
- Show file/segment progress, provider, speed, estimated cost, and errors.
- Pause, resume, cancel, retry failed segments, and open output SRT.
- Model inference must never block the Qt UI thread.
- The GUI must call the shared orchestrator; do not duplicate pipeline logic.

## Required real-world validation

Use at least these samples:

1. 3–5 minute Mandarin speech.
2. Mandarin mixed with English terms.
3. A lecture containing domain glossary terms.
4. A sutra-reading excerpt.
5. The recurring 《得見彌勒根本大明神咒》 ending.
6. A video longer than 30 minutes to exercise segmentation and resume.

For every sample report:

- provider/model/device;
- audio duration and elapsed processing time;
- transcript length;
- alignment coverage;
- number of SRT cues;
- last cue end time;
- warnings and manual corrections needed.

## Completion report format

At the end, state:

1. files changed;
2. commands executed;
3. tests passed/failed/skipped;
4. whether real Qwen, Whisper, aligner, Gemini, and FFmpeg were exercised;
5. any remaining mocks;
6. known dependency conflicts;
7. end-to-end sample metrics;
8. regressions checked in existing VideoCaptioner features.
