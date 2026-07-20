# Codex handoff: Hybrid ASR remaining work

## Current branch

`agent/hybrid-asr-core`

The branch contains a model-agnostic foundation only. Existing VideoCaptioner GUI and production ASR paths have not been changed.

## Implemented foundation

- Development rules in `AGENTS.md`.
- Shared transcription, alignment, audio-segment, and subtitle data models.
- `Transcriber` and `ForcedAligner` protocols.
- FFmpeg audio normalization helper and deterministic smart split planning.
- Deterministic transcript quality checks.
- SRT rendering, validation, and atomic output.
- SQLite job, segment, usage, and review schema with basic resume operations.
- Unit tests for SRT, quality, audio planning, fingerprinting, and resume behavior.

## Mandatory first task: validate the foundation

Run from the repository root:

```bash
uv sync
uv run pytest tests/hybrid_asr -v
uv run ruff check app/core/hybrid_asr tests/hybrid_asr
uv run pyright app/core/hybrid_asr
```

Fix any compatibility, formatting, typing, or import failures. Do not weaken tests merely to make them pass. Record exact command output in `docs/hybrid-asr-validation.md`.

## Task 1: complete FFmpeg segmentation

Implement actual segment extraction and silence detection in `app/core/hybrid_asr/audio.py` or dedicated modules.

Acceptance criteria:

- Probe media duration reliably.
- Run `silencedetect` and parse Windows/macOS/Linux output.
- Extract each planned segment as 16 kHz mono PCM WAV.
- Use Unicode-safe subprocess arguments.
- Clean temporary files on success and failure.
- Add integration tests marked `slow` that skip clearly when FFmpeg is unavailable.

## Task 2: adapt existing Qwen and Whisper implementations

Inspect the existing repository and reuse current model loading and transcription code. Do not create a second independent implementation if working code already exists.

Create providers implementing `Transcriber`:

- `QwenTranscriber`
- `WhisperTranscriber`

Acceptance criteria:

- Support language, prompt/glossary, previous context, and optional word timestamps.
- Return `TranscriptionResult` consistently.
- Separate model loading from each request.
- Provide mock unit tests and real local integration tests.
- Record installed package versions, device, model path/name, media duration, elapsed time, and output sample.

## Task 3: integrate Qwen forced alignment

Create a provider implementing `ForcedAligner` using the installed Qwen forced-aligner model/API.

Critical rule: the aligner may assign timestamps only. It must not replace, paraphrase, or correct transcript text.

Acceptance criteria:

- Support Traditional Chinese and mixed English.
- Create a reversible mapping between display text and alignment text.
- Normalize punctuation, spaces, numbers, and English case for alignment while preserving display text.
- Return token/character times, confidence when available, coverage, and unmatched text.
- Test with a real Chinese audio clip and report coverage.
- Explicitly document unsupported characters, sutra/mantra behavior, and package-version constraints.

## Task 4: add glossary management

Implement:

- default glossary plus folder-specific glossary selection;
- CSV columns `wrong_term,correct_term,note,match_mode,enabled`;
- modes `prompt_only`, `exact`, `contains`, `regex`, and `review_only`;
- deterministic version hash;
- safe correction rules that avoid blind substring replacement.

Reuse the repository's current custom dictionary and prompt-file functionality where possible.

## Task 5: build the orchestrator and CLI

Create a model-independent pipeline that coordinates:

1. file scan and stability check;
2. fingerprint and resume decision;
3. normalization and smart segmentation;
4. transcription;
5. glossary normalization;
6. forced alignment;
7. quality checks;
8. retry/fallback decision;
9. cue segmentation;
10. atomic SRT output;
11. SQLite updates.

CLI requirements:

```bash
python -m app.core.hybrid_asr.cli --single-file path/to/video.mp4 --mode qwen_local
python -m app.core.hybrid_asr.cli --root path/to/folder --mode hybrid_smart --resume
```

Add `--dry-run`, `--retry-failed`, and `--review-needed`.

## Task 6: integrate Vertex AI Gemini

Use the current official Google Gen AI SDK in Vertex AI mode, not an AI Studio API key workflow.

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
