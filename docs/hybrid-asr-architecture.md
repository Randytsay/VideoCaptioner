# Hybrid ASR architecture

> Current implementation status and agent takeover instructions are maintained in:
>
> - `docs/hybrid-asr-work-status.md`
> - `docs/codex-hybrid-asr-handoff.md`

## Goal

Add a reliable batch transcription pipeline without coupling model runtimes to the PyQt user interface. The final system should support local Qwen/Whisper transcription, Vertex AI Gemini transcription, forced alignment, glossary-aware correction, resumable jobs, and deterministic SRT generation.

## Design principles

1. Transcription answers **what was said**.
2. Forced alignment answers **when the supplied text was said**.
3. Subtitle segmentation decides **how aligned text is displayed**.
4. Persistence records every file, segment, attempt, and decision.
5. The GUI is a client of the pipeline, not the pipeline itself.

## Target flow

```text
media file
  -> audio normalization
  -> silence/VAD segmentation
  -> Transcriber (Qwen, Whisper, Gemini)
  -> glossary/text normalization
  -> ForcedAligner (Qwen aligner preferred)
  -> deterministic quality checks
  -> subtitle segmentation
  -> atomic SRT output
  -> SQLite job state
```

## Smart hybrid mode

1. Run Qwen locally first.
2. Check transcript density, repetition, alignment coverage, unmatched tokens, and glossary warnings.
3. Accept healthy segments.
4. Send only suspicious segments to Gemini for a faithful re-transcription.
5. Re-align the Gemini text locally.
6. Use Whisper only as a fallback or second opinion, not as the authority over higher-quality Gemini text.

## Current module boundaries

```text
app/core/hybrid_asr/
  models.py       shared immutable data structures
  interfaces.py   Transcriber and ForcedAligner protocols
  audio.py        ffmpeg extraction and smart segmentation
  scanner.py      recursive discovery and file-stability checks
  glossary.py     glossary parsing, merging, corrections, and audit data
  segmenter.py    deterministic subtitle segmentation
  quality.py      deterministic quality checks
  srt.py          cue validation, rendering, and atomic output
  persistence.py  SQLite schema and resumable job repository
  pipeline.py     injected single-segment processing pipeline
```

Future modules:

```text
  orchestrator.py whole-file/multi-segment coordination
  normalization.py reversible display/alignment text mapping
  providers/
    qwen.py
    whisper.py
    gemini_vertex.py
  alignment/
    qwen.py
  cli.py
```

## Existing VideoCaptioner integration points

The agent must adapt, not blindly duplicate, these existing areas:

- `app/core/asr/transcribe.py`: current Whisper and other ASR dispatch.
- `app/core/asr/asr_data.py`: subtitle timing data, Traditional Chinese conversion, mappings, and export.
- `app/core/task_factory.py`: prompt-file selection and task configuration.
- `app/thread/transcript_thread.py`: production transcription workflow and custom dictionaries.
- `app/thread/batch_process_thread.py`: PyQt batch queue and progress reporting.
- `app/core/entities.py`: current configuration and task entities.

The repository currently has no Qwen provider in its ASR dispatcher. The user's Qwen environment must be inspected locally before integration.

## Compatibility strategy

The new core remains isolated from existing VideoCaptioner production paths until CLI and real-model integration tests pass. Existing GUI and ASR paths remain untouched in the foundation phase. Providers should adapt existing model-loading code where available rather than duplicate it.

If PyQt, Qwen, Whisper, PyTorch, transformers, or vLLM dependencies conflict, model providers may be moved into a separate local worker process while retaining the same core protocols.

## Known integration risks

- Qwen, Whisper, PyTorch, transformers, vLLM, and PyQt may require incompatible dependency versions.
- Gemini timestamps are rough guidance only; final SRT timing should come from local forced alignment when available.
- Chinese, English abbreviations, numbers, scripture text, and mantras require separate display-text and alignment-text normalization.
- Google Drive mounted files must be stable before processing.
- Media fingerprint changes must invalidate old segment results to prevent stale resume data.
- Cross-segment audio overlap requires deterministic duplicate-text removal.

## Delivery phases

1. Validate the complete foundation branch.
2. Fix stale SQLite segment reuse after media changes.
3. Validate FFmpeg against real media.
4. Adapt existing Whisper providers.
5. Integrate local Qwen ASR.
6. Integrate Qwen forced alignment and reversible text normalization.
7. Build whole-file orchestration and CLI.
8. Add Vertex AI Gemini.
9. Add smart fallback decisions and real-world validation.
10. Add the Traditional Chinese batch GUI and complete regression testing.
