# Development rules

- Preserve all existing VideoCaptioner user-facing behavior unless a task explicitly changes it.
- Do not commit credentials, model weights, private media, generated databases, logs, or temporary audio.
- Keep ASR transcription, forced alignment, subtitle segmentation, persistence, and GUI concerns separated.
- A forced aligner may assign timing only; it must never rewrite transcript text.
- Core hybrid-ASR modules must not import PyQt.
- Use dependency injection for model providers so tests do not download or load models.
- New generated subtitle files must use atomic writes.
- Preserve Windows, macOS, Linux, Unicode paths, and Traditional Chinese compatibility.
- Do not claim an integration works unless a real integration test was executed.
- Every new feature requires unit tests; model-dependent tests must be marked integration/slow.
- Run pytest, ruff, and pyright before marking a phase complete.
- Record skipped tests and the reason in the handoff document.
- Keep commits focused and do not mix unrelated cleanup with hybrid-ASR work.
