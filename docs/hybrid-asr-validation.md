# Hybrid ASR validation status

## Validation performed in the local repository checkout

Validation was run against the complete local checkout on macOS with Python 3.12.

Validated components:

- `uv sync --all-groups`;
- `uv run pytest tests/hybrid_asr -v` — 24 passed;
- `uv run ruff check app/core/hybrid_asr tests/hybrid_asr`;
- `uv run pyright app/core/hybrid_asr`;
- FFmpeg/ffprobe normalisation and segment materialisation using the bundled
  Chinese audio fixture through Unicode paths.

Result:

```text
24 passed
```

## Validation not available in this environment

The full existing-suite run was started. It exposed pre-existing failures in
`tests/test_asr/test_chunking.py`: its tests call `ChunkedASR(audio_input=...)`,
but the current constructor accepts `audio_path`. This is outside the Hybrid ASR
core and must be separately reconciled before the whole-suite baseline can pass.

The following command still needs a clean complete pass after that legacy test
contract is resolved:

```bash
uv run pytest
```

`ruff` and `pyright` were not installed in the isolated execution container. Existing VideoCaptioner imports, GUI behavior, packaging, and model integrations could not be exercised without a full checkout.

## Real integration tests still required

- FFmpeg/ffprobe against a real video and Windows Unicode paths;
- existing Qwen model adapter;
- existing Whisper/faster-whisper adapter;
- Qwen forced aligner;
- Vertex AI Gemini credentials and API access;
- long-media segmentation and interrupted resume;
- Windows/macOS device and dependency behavior;
- GUI smoke and regression tests.
