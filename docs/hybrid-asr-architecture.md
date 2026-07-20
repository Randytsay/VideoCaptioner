# Hybrid ASR architecture

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

## Module boundaries

```text
app/core/hybrid_asr/
  models.py       shared immutable data structures
  interfaces.py   Transcriber and ForcedAligner protocols
  quality.py      deterministic quality checks
  srt.py          cue building, validation, atomic output
  persistence.py  SQLite schema and resumable job repository
```

Future modules:

```text
  audio.py        ffmpeg extraction and smart segmentation
  glossary.py     folder mapping and text normalization
  orchestrator.py pipeline coordination and fallback decisions
  providers/
    qwen.py
    whisper.py
    gemini_vertex.py
  alignment/
    qwen.py
  cli.py
```

## Compatibility strategy

The new core is isolated from existing VideoCaptioner code in the first phase. Existing GUI and ASR paths remain untouched. Providers will later adapt existing model-loading code rather than duplicate it.

## Known integration risks

- Qwen, Whisper, PyTorch, transformers, vLLM, and PyQt may require incompatible dependency versions.
- Model providers should eventually run in a separate local worker process if dependency conflicts appear.
- Gemini timestamps are rough guidance only; final SRT timing should come from local forced alignment when available.
- Chinese, English abbreviations, numbers, sutra text, and mantras require separate display-text and alignment-text normalization.
- Google Drive mounted files must be stable before processing.

## Delivery phases

1. Core interfaces, models, quality checks, SRT writer, SQLite repository.
2. FFmpeg audio extraction and smart segmentation.
3. Existing Qwen and Whisper adapters.
4. Qwen forced aligner adapter and real local validation.
5. Vertex AI Gemini provider.
6. Hybrid orchestrator and CLI.
7. Batch GUI and end-to-end long-media validation.
