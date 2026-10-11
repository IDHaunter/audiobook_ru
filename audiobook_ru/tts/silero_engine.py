"""Silero TTS engine adapter for audiobook_ru.

Uses Silero TTS via torch.hub:
- Loads model: torch.hub.load('snakers4/silero-models', 'silero_tts', language='ru')
- Speakers available: 'aidar', 'baya', 'kseniya', 'xenia', 'eugene'
- Sample rate: 48000 Hz
"""

import ssl
import torch

# Disable SSL verification for hub downloads
ssl._create_default_https_context = ssl._create_unverified_context

from pathlib import Path
from typing import Optional, Dict, Any

logger = __import__("logging").getLogger(__name__)


class SileroEngine:
    """Silero TTS engine adapter.

    Uses Silero TTS via torch.hub:
    - Loads model: torch.hub.load('snakers4/silero-models', 'silero_tts', language='ru')
    - Speakers available: 'aidar', 'baya', 'kseniya', 'xenia', 'eugene'
    - Sample rate: 48000 Hz
    """

    # Voice variants available in Silero Russian TTS
    VOICES = ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']

    # Mapping of user-friendly speaker names to actual model speaker names
    # This handles the case where torch.hub loads a newer model version with
    # different speaker naming conventions
    SPEAKER_ALIASES = {
        'aidar': ['aidar', 'aidar_v2', 'aidar_8khz', 'aidar_16khz'],
        'baya': ['baya', 'baya_v2', 'baya_8khz', 'baya_16khz'],
        'kseniya': ['kseniya', 'kseniya_v2', 'kseniya_8khz', 'kseniya_16khz'],
        'xenia': ['xenia'],
        'eugene': ['eugene'],
    }

    def __init__(
        self,
        model_name: str = 'silero_tts',
        speaker: str = 'kseniya',
        work_dir: str = "work",
    ):
        """Initialize Silero TTS engine.

        Args:
            model_name: Name of the Silero model to load from torch.hub
            speaker: Voice variant ('aidar', 'baya', 'kseniya', 'xenia', 'eugene')
            work_dir: Base work directory for temporary files.
        """
        self.model_name = model_name
        self.speaker = speaker
        self.work_dir = work_dir
        self._model = None
        self._sample_rate = 48000

        # Validate speaker - check against known voices
        if speaker not in self.VOICES:
            raise ValueError(
                f"Invalid speaker '{speaker}'. Available: {self.VOICES}"
            )

    def _get_available_speakers(self) -> list[str]:
        """Return list of available voice speakers."""
        return self.VOICES

    def _load_model(self):
        """Load the Silero TTS model from torch.hub."""
        if self._model is None:
            logger.info("Loading Silero TTS model (%s) with speaker %s...", self.model_name, self.speaker)

            # Try the speaker name as-is first, then try aliases
            speaker_variants = [self.speaker] + self.SPEAKER_ALIASES.get(self.speaker, [])
            
            loaded = False
            for speaker in speaker_variants:
                try:
                    result = torch.hub.load(
                        repo_or_dir='snakers4/silero-models',
                        model='silero_tts',
                        language='ru',
                        speaker=speaker,
                    )
                    # Handle different return formats from torch.hub.load
                    if isinstance(result, tuple):
                        self._model = result[0]
                    elif isinstance(result, list):
                        self._model = result[0]
                    else:
                        self._model = result
                    self._model.to(torch.device('cpu'))
                    logger.info("Loaded Silero model with speaker %s", speaker)
                    loaded = True
                    break
                except Exception as e:
                    logger.debug("Failed to load with speaker %s: %s", speaker, e)
                    continue

            if not loaded:
                # As a last resort, try loading without specifying a speaker
                # (will use default) or raise an error
                logger.warning("Could not load model with any speaker variant, trying without speaker...")
                try:
                    result = torch.hub.load(
                        repo_or_dir='snakers4/silero-models',
                        model='silero_tts',
                        language='ru',
                    )
                    # Handle different return formats
                    if isinstance(result, tuple):
                        self._model = result[0]
                    elif isinstance(result, list):
                        self._model = result[0]
                    else:
                        self._model = result
                    self._model.to(torch.device('cpu'))
                    logger.info("Loaded Silero model without speaker specification")
                except Exception as e:
                    raise RuntimeError(f"Failed to load Silero TTS model: {e}")

    def synthesize(self, text: str, output_path: str) -> dict:
        """Synthesize text to WAV file using Silero.

        Args:
            text: Text to synthesize.
            output_path: Path to write the output WAV file.

        Returns:
            Dictionary with synthesis metadata.
        """
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")

        # Load model if not already loaded
        self._load_model()

        # Write to WAV file
        output_path = str(output_path)
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Use Silero's apply_tts method
        audio = self._model.apply_tts(
            text=text,
            speaker=self.speaker,
            sample_rate=self._sample_rate,
        )

        # Save as WAV using soundfile
        import soundfile as sf
        sf.write(output_path, audio.numpy(), self._sample_rate)

        # Read back metadata
        import wave
        try:
            with wave.open(output_path, 'rb') as reread:
                params = reread.getparams()
                metadata = {
                    "sample_rate": params.framerate,
                    "sample_width": params.sampwidth,
                    "n_channels": params.nchannels,
                    "duration": params.nframes / params.framerate if params.framerate > 0 else 0,
                    "text": text,
                    "model": self.model_name,
                    "speaker": self.speaker,
                }
        except Exception:
            metadata = {
                "sample_rate": self._sample_rate,
                "sample_width": 2,
                "n_channels": 1,
                "duration": len(audio.numpy()) / self._sample_rate,
                "text": text,
                "model": self.model_name,
                "speaker": self.speaker,
            }

        logger.info(
            "Synthesized %d chars to %s (sample_rate=%d, duration=%.2f s)",
            len(text),
            output_path,
            metadata["sample_rate"],
            metadata["duration"],
        )

        return metadata

    def get_model_info(self) -> dict:
        """Return information about the current model/voice."""
        return {
            "model": self.model_name,
            "speaker": self.speaker,
            "language": "ru",
            "available_speakers": self._get_available_speakers(),
        }

    def supports_language(self, language_code: str) -> bool:
        """Check if engine supports a given language."""
        lang = language_code.lower()
        return lang in ("ru", "Russian", "rus")

    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._model is not None