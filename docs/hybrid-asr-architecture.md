# Hybrid ASR architecture

## Current repository findings

The existing application has mature `ASRData`/SRT handling, FFmpeg audio extraction,
and FasterWhisper/WhisperCpp/API adapters. It does **not** currently contain a Qwen
ASR or Qwen Forced Aligner implementation. Qwen references are LLM settings, not an
ASR provider.

## New core

`app/core/hybrid_asr` is deliberately independent of PyQt and existing task threads.
It supplies provider-neutral contracts, FFmpeg normalisation and silence-aware segment
planning, validated atomic SRT output, conservative glossaries, deterministic quality
checks, and SQLite segment persistence. Existing GUI code remains untouched.

```
media -> normalize -> segment -> Transcriber -> Glossary -> ForcedAligner
      -> quality -> SRT (atomic) -> SQLite state
```

Qwen, Gemini Vertex AI, and a real forced aligner remain optional adapters because no
installed provider/API credentials can be inferred from this repository.

## Required validation before model adapters

1. Run `pytest tests/hybrid_asr -v`.
2. Run `ruff check app/core/hybrid_asr tests/hybrid_asr`.
3. Run each real model against a non-private Chinese audio sample.
4. Record package/model/device, transcript length, aligned coverage, and resulting SRT.
