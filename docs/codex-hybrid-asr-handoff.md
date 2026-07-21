# Codex handoff: Hybrid ASR remaining work

## Read this first

Before making changes, read:

1. `AGENTS.md`
2. `docs/hybrid-asr-work-status.md`
3. `docs/hybrid-asr-architecture.md`
4. this document

`docs/hybrid-asr-work-status.md` is the authoritative record of completed work, reviewed repository areas, known limitations, and items that must not be unnecessarily rewritten.

## Current repository state

- Repository: `Randytsay/VideoCaptioner`
- Branch: `agent/hybrid-asr-core`
- Draft PR: `#1`
- Base: `master`
- Do not merge to `master` until complete local validation and real-model tests pass.

The branch contains a model-independent Hybrid ASR foundation. Existing VideoCaptioner production ASR, GUI, and batch workflows have not been switched to it.

## Important findings from the existing repository

- `app/core/asr/transcribe.py` currently supports JianYing, Bcut, whisper.cpp, Whisper API, and Faster Whisper.
- Qwen is not currently integrated into the repository ASR dispatcher, even though the user has a Qwen environment installed locally.
- Existing Whisper prompt-file handling is in `app/core/task_factory.py`.
- Existing Traditional Chinese conversion and custom dictionary application are in `app/thread/transcript_thread.py` and `app/core/asr/asr_data.py`.
- Existing PyQt batch execution and progress reporting are in `app/thread/batch_process_thread.py`.
- Reuse these implementations where practical. Do not create duplicate production systems without a documented technical reason.

## Mandatory first task: validate the full branch

Run from a complete local checkout:

```bash
uv sync
uv run pytest tests/hybrid_asr -v
uv run ruff check app/core/hybrid_asr tests/hybrid_asr
uv run pyright app/core/hybrid_asr
uv run pytest
```

Fix compatibility, formatting, typing, import, migration, and regression failures. Do not delete tests or weaken assertions merely to pass validation.

Record exact results in:

```text
docs/hybrid-asr-validation.md
```

Include Python, operating system, FFmpeg, PyTorch, Qwen, Whisper, CUDA/MPS/CPU, and relevant package versions.

## Immediate defect to fix

Add a regression test and fix stale SQLite reuse when a source file changes.

Current risk:

- media fingerprint changes;
- media status resets to `pending`;
- old completed segment rows may remain;
- old transcription/alignment results could be reused incorrectly.

Required behavior:

- detect fingerprint change inside the same transaction;
- invalidate or delete all related old segment rows and cascading attempt/alignment/review/usage rows;
- create fresh pending segments;
- prove the behavior with a test.

## Task 1: real FFmpeg validation

The core FFmpeg commands already exist. Validate and correct them using installed FFmpeg/ffprobe and real media.

Acceptance criteria:

- Unicode Windows and macOS paths work;
- duration probing is correct;
- silence detection is parsed from actual FFmpeg output;
- output segments are mono, 16 kHz, PCM WAV;
- segment duration and offsets match the plan;
- temporary files are cleaned on success and failure;
- integration tests are marked `slow` and skip clearly when FFmpeg is unavailable.

## Task 2: adapt existing Whisper implementations

Create one or more `Transcriber` adapters around the existing repository implementations rather than rebuilding Whisper.

Potential backends:

- Faster Whisper
- whisper.cpp
- Whisper API, where appropriate

Acceptance criteria:

- support language;
- support glossary/prompt terms;
- support previous context when the backend supports it;
- support optional word timestamps;
- return `TranscriptionResult` consistently;
- avoid reloading the model for every segment;
- provide mock unit tests and real local integration tests;
- document model, package version, device, media duration, elapsed time, transcript length, and output sample.

## Task 3: integrate local Qwen ASR

The user's Qwen installation is external to the current repository dispatcher. Inspect the actual local environment before selecting the adapter API.

Acceptance criteria:

- implement `QwenTranscriber`;
- load the model once;
- support language, glossary terms, and previous context where available;
- return the shared `TranscriptionResult`;
- provide clear errors for missing packages/models or unsupported versions;
- record exact package/model/device details;
- run a real Mandarin test and a domain-glossary test.

Do not claim completion based only on mocks.

## Task 4: integrate Qwen Forced Aligner

Implement `ForcedAligner` using the user's actual Qwen forced-aligner installation/API.

Critical rule:

> The aligner assigns timestamps only. It must not rewrite, paraphrase, correct, or replace the supplied transcript.

Acceptance criteria:

- support Traditional Chinese and mixed English;
- create reversible `display_text` ↔ `alignment_text` mapping;
- normalize punctuation, spaces, numbers, English case, abbreviations, and symbols for alignment;
- preserve original display text;
- return token/character times, confidence if available, coverage, unmatched text, and warnings;
- test normal Mandarin, mixed English, sutra reading, and 《得見彌勒根本大明神咒》;
- document unsupported characters and package/version constraints.

## Task 5: integrate folder-aware glossary selection

The glossary parser and correction foundation already exist. Do not rewrite it.

Add:

- default glossary selection;
- folder-name-to-glossary mapping;
- manual glossary override;
- merge with existing selected Whisper prompt files and existing custom mappings;
- configuration and version-hash persistence;
- domain sample glossaries for general terms, Market America, Buddhist scripture, and meditation courses.

Avoid blind substring replacement. Use the existing match modes and review records.

## Task 6: build the whole-file orchestrator and CLI

Build around the existing scanner, audio, glossary, pipeline, quality, SRT, and SQLite foundations.

Required flow:

1. scan files;
2. confirm file stability;
3. calculate fingerprint;
4. restore or create job state;
5. normalize audio;
6. detect silence and materialize segment plan;
7. transcribe each segment;
8. apply glossary processing;
9. force-align text;
10. inspect quality;
11. retry or fall back when needed;
12. remove cross-segment overlap/repeated text;
13. build and validate cues;
14. write SRT atomically;
15. commit SQLite state after each completed segment;
16. clean temporary audio.

CLI requirements:

```bash
python -m app.core.hybrid_asr.cli --single-file path/to/video.mp4 --mode qwen_local
python -m app.core.hybrid_asr.cli --root path/to/folder --mode hybrid_smart --resume
```

Required options:

- `--single-file`
- `--root`
- `--mode`
- `--resume`
- `--dry-run`
- `--retry-failed`
- `--review-needed`

CLI end-to-end tests must pass before GUI work starts.

## Task 7: integrate Vertex AI Gemini

Use the current official Google Gen AI SDK in Vertex AI mode. Do not substitute an AI Studio API-key workflow.

Authentication order:

1. Application Default Credentials;
2. `GOOGLE_APPLICATION_CREDENTIALS`;
3. explicitly configured external credential path.

Do not commit credentials.

Prompt requirements:

- faithful transcription;
- no summarization;
- no rewriting;
- no invented content;
- preserve spoken order;
- mark unclear speech;
- use glossary terms;
- previous context is reference-only and must not be repeated.

Gemini timestamps are rough metadata only. Final SRT timing must come from local forced alignment when available.

Implement separate handling for:

- 429 exponential backoff;
- transient 5xx retries;
- authentication failure;
- malformed structured output;
- quality retry.

Record reported usage, estimated cost, and pricing-version metadata. Never label estimated cost as the actual invoice amount.

## Task 8: implement smart hybrid decisions

Modes:

- `qwen_local`
- `whisper_local`
- `gemini_quality`
- `hybrid_smart`

Default `hybrid_smart` flow:

1. transcribe locally with Qwen;
2. align locally;
3. run deterministic quality checks;
4. accept healthy segments;
5. send only suspicious segments to Gemini;
6. align Gemini text locally again;
7. use Whisper only as fallback or second opinion.

Add configurable thresholds for:

- alignment coverage;
- unmatched-token ratio;
- text density;
- repeated n-grams;
- glossary warnings;
- timestamp overlap/backward movement;
- cross-segment repetition;
- transcript too short/long;
- gap between final cue and media end.

Log every provider decision and its reason.

## Task 9: real-world validation

At minimum test:

1. 3–5 minute Mandarin speech;
2. Mandarin mixed with English terms;
3. domain-glossary lecture;
4. Buddhist lecture;
5. scripture reading;
6. 《得見彌勒根本大明神咒》 ending;
7. video longer than 30 minutes;
8. Chinese filename and folder path;
9. forced interruption and resume;
10. Google Drive file still syncing.

For every sample record:

- provider/model/device;
- media duration;
- processing time and speed multiplier;
- transcript length;
- alignment coverage;
- unmatched text;
- cue count;
- final cue end time;
- warnings and manual corrections.

## Task 10: GUI integration

Only after the CLI is proven end to end, add a Traditional Chinese `智慧批次字幕` page.

Required features:

- select root folder;
- select processing mode;
- show files, stages, segment progress, provider/model, speed, estimated cost, and errors;
- start, pause, resume, cancel, and retry failed segments;
- open output SRT;
- review flagged items;
- never block the Qt UI thread;
- preserve SQLite state when the GUI closes;
- call the shared orchestrator instead of duplicating pipeline logic.

Regression-test existing transcription, subtitle optimization, translation, editing, synthesis, and batch functionality.

## Commit and reporting rules

Complete one logical phase at a time. Test before commit. Push all commits to `agent/hybrid-asr-core` so Draft PR #1 updates automatically.

For every phase report:

1. phase name;
2. files changed;
3. commands executed;
4. passed, failed, and skipped tests;
5. whether real models and real media were used;
6. remaining mocks;
7. package versions and device;
8. sample metrics;
9. known issues;
10. commit SHA and next phase.

Do not merge `master` without explicit user approval.
