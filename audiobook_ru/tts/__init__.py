"""TTS module for audiobook_ru.

Provides TTS engine adapters for synthesizing audio.
"""

from .piper_engine import PiperEngine

__all__ = ["PiperEngine"]