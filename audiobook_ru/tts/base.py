"""Minimal TTS engine protocol/interface for audiobook_ru."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> dict:
        """Synthesize text to audio file.

        Args:
            text: Text to synthesize.
            output_path: Path to write the output WAV file.

        Returns:
            Dictionary with synthesis metadata (duration, sample_rate, etc.)
        """
        raise NotImplementedError

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return information about the current model/voice.

        Returns:
            Dictionary with model name, language, speaker, etc.
        """
        raise NotImplementedError

    @abstractmethod
    def supports_language(self, language_code: str) -> bool:
        """Check if engine supports a given language.

        Args:
            language_code: ISO language code (e.g. "ru", "en").

        Returns:
            True if the engine supports the language.
        """
        raise NotImplementedError