"""TTS module for audiobook_ru.

Provides TTS engine adapters for synthesizing audio.
"""

from .piper_engine import PiperEngine
from .silero_engine import SileroEngine

__all__ = ["PiperEngine", "SileroEngine"]