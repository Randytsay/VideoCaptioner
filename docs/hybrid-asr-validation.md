# Hybrid ASR validation status

## Validation performed in the assistant execution environment

The GitHub repository could not be cloned because the execution container could not resolve `github.com`. Validation was therefore performed by recreating the new model-independent package and its focused tests in an isolated Python environment.

Validated components:

- glossary CSV loading, correction, review hits, and stable version hashing;
- deterministic subtitle segmentation and line wrapping;
- media scan filtering and file stability rules;
- injected transcription/alignment segment pipeline;
- Python module compilation.

Result:

```text
8 passed
```

## Validation not available in this environment

The following commands still need to run against the complete repository checkout:

```bash
uv sync
uv run pytest tests/hybrid_asr -v
uv run ruff check app/core/hybrid_asr tests/hybrid_asr
uv run pyright app/core/hybrid_asr
uv run pytest
```

`ruff` and `pyright` were not installed in the isolated execution container. Existing VideoCaptioner imports, GUI behavior, packaging, and model integrations could not be exercised without a full checkout.

## Real integration tests still required

- FFmpeg/ffprobe against real video and Unicode paths;
- existing Qwen model adapter;
- existing Whisper/faster-whisper adapter;
- Qwen forced aligner;
- Vertex AI Gemini credentials and API access;
- long-media segmentation and interrupted resume;
- Windows/macOS device and dependency behavior;
- GUI smoke and regression tests.
