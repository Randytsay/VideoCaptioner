# Hybrid ASR development rules

- Keep the existing PyQt workflow working; the hybrid-ASR core must not import PyQt.
- ASR determines transcript text. Forced alignment determines timestamps and must never rewrite text.
- Do not commit model weights, credentials, private media, databases, logs, or generated subtitles.
- Model integrations are optional dependencies. Do not claim they work without a real integration test.
- Use atomic writes for generated SRT files and preserve Unicode paths on macOS and Windows.
- Add focused tests for every deterministic feature and run them before committing.
