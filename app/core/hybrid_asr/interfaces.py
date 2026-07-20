"""Stable boundaries for model adapters.

Adapters must keep expensive models alive themselves; the pipeline calls one
adapter instance for many audio segments.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .models import AlignmentResult, TranscriptionRequest, TranscriptionResult


class Transcriber(ABC):
    provider_name: str

    @abstractmethod
    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        """Return transcript text. Implementations must not write subtitle files."""


class ForcedAligner(ABC):
    provider_name: str

    @abstractmethod
    def align(
        self, audio_path: Path, transcript: str, language: Optional[str] = None
    ) -> AlignmentResult:
        """Align exactly *transcript* to audio without modifying its wording."""
