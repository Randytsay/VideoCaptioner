from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import AlignmentRequest, AlignmentResult, TranscriptionRequest, TranscriptionResult


@runtime_checkable
class Transcriber(Protocol):
    """Converts audio into faithful text.

    Providers may return rough timestamps, but final subtitle timing is owned by a
    ForcedAligner whenever one is configured.
    """

    @property
    def provider_name(self) -> str: ...

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult: ...


@runtime_checkable
class ForcedAligner(Protocol):
    """Assigns timing to supplied text without rewriting that text."""

    @property
    def provider_name(self) -> str: ...

    def align(self, request: AlignmentRequest) -> AlignmentResult: ...
