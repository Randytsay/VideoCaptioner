# Codex handoff: Hybrid ASR implementation

## Starting point

Work from branch `codex/hybrid-asr-core`. Read `AGENTS.md` and
`docs/hybrid-asr-architecture.md` first. Do not alter the existing GUI workflow
or merge into `master`.

The core foundation has passing deterministic tests but no model adapter is
implemented yet. This is intentional: the repository contains FasterWhisper,
WhisperCpp and cloud Whisper adapters, but no Qwen ASR or Forced Aligner code.
Do not state that Qwen or Gemini works until a real local/API test has run.

## Ordered tasks

1. **Validate baseline**: run `uv sync --all-groups`, `uv run pytest
   tests/hybrid_asr -v`, `uv run ruff check app/core/hybrid_asr
   tests/hybrid_asr`, and `uv run pyright app/core/hybrid_asr`.
2. **Complete FFmpeg execution**: build extracted-segment materialisation from
   `AudioSegment` plans, including temporary-directory cleanup and a real media
   integration test. Reuse `app/core/utils/video_utils.py` where possible.
3. **Add a FasterWhisper adapter**: wrap the existing `FasterWhisperASR` behind
   `Transcriber`; do not duplicate its command/model configuration. Use a mock
   test plus one local audio test.
4. **Add Qwen adapters only after discovery**: identify the installed package
   and its supported API. Implement separate `QwenTranscriber` and
   `QwenForcedAligner` optional adapters. The aligner must preserve its input
   transcript exactly and report unmatched text and coverage.
5. **Build a CLI pipeline**: scanner -> stable-file check -> fingerprint ->
   normalisation -> segments -> transcriber -> glossary -> alignment -> quality
   -> atomic SRT -> SQLite. Support `--single-file`, `--root`, `--resume`,
   `--dry-run`, and `--retry-failed` before any GUI work.
6. **Gemini Vertex provider**: use Google Gen AI SDK in Vertex AI mode and ADC;
   no API key or credential file in Git. Treat Gemini timestamps as rough only;
   route its text into the forced aligner.
7. **Hybrid policy and UI**: only after end-to-end CLI verification, add Qwen
   first / Gemini escalation / Whisper fallback and then a non-blocking PyQt
   batch page.

## Required evidence for each real model

Record package/model/version, device, audio duration, wall time, transcript
characters, aligned characters, coverage, unmatched text, SRT cue count and
last cue end time. Use a harmless Chinese sample; private course media and model
weights must remain outside Git.

## Acceptance rules

- Make one focused commit per completed phase.
- Keep `ForcedAligner.align(audio, transcript)` text-preserving.
- Do not turn `contains` glossary rules into global replacements; only `exact`
  and explicit `regex` rules can change text automatically.
- SRT files must use the atomic `.partial` then `os.replace` workflow.
- Report skipped real-model tests truthfully instead of substituting mocks.
