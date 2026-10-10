"""Piper TTS engine adapter for audiobook_ru."""

import json
import logging
import os
import wave
from pathlib import Path
from typing import Optional, Dict, Any

import piper

logger = logging.getLogger(__name__)


class PiperEngine:
    """Piper TTS engine adapter.

    Uses the official piper-tts Python API:
    - PiperVoice.load(model_path, config_path=None)
    - voice.synthesize_wav(text, wave_file)
    """

    def __init__(
        self,
        model_path: str,
        config_path: Optional[str] = None,
        work_dir: str = "work",
    ):
        """Initialize Piper TTS engine.

        Args:
            model_path: Path to the .onnx voice model file.
            config_path: Path to the .onnx.json config file.
                If None, derived from model_path (.onnx.json).
            work_dir: Base work directory for temporary files.
        """
        self.model_path = str(model_path)
        self.work_dir = work_dir

        # Resolve config path
        if config_path is None:
            config_path = str(Path(model_path).with_suffix(".onnx.json"))
        self.config_path = config_path if os.path.exists(config_path) else None

        # Validate model exists
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Piper model not found: {self.model_path}")

        if self.config_path and not os.path.exists(self.config_path):
            logger.warning(
                "Piper config file not found: %s", self.config_path
            )

        self._voice: Optional[piper.PiperVoice] = None
        self._model_info: Optional[Dict[str, Any]] = None

    def synthesize(self, text: str, output_path: str) -> dict:
        """Synthesize text to WAV file using Piper.

        Args:
            text: Text to synthesize.
            output_path: Path to write the output WAV file.

        Returns:
            Dictionary with synthesis metadata.
        """
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")

        # Load voice once if not already loaded
        if self._voice is None:
            self._voice = piper.PiperVoice.load(
                self.model_path,
                self.config_path,
            )

        # Write to WAV file
        output_path = str(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with wave.open(output_path, "wb") as wav_file:
            self._voice.synthesize_wav(text, wav_file)

        # Read back metadata from the WAV
        with wave.open(output_path, "rb") as reread:
            params = reread.getparams()
            metadata = {
                "sample_rate": params.framerate,
                "sample_width": params.sampwidth,
                "n_channels": params.nchannels,
                "duration": params.nframes / params.framerate
                if params.framerate > 0
                else 0,
                "text": text,
                "model": self.get_model_info(),
            }

        logger.info(
            "Synthesized %d chars to %s (sample_rate=%d, channels=%d, duration=%.2f s)",
            len(text),
            output_path,
            metadata["sample_rate"],
            metadata["n_channels"],
            metadata["duration"],
        )

        return metadata

    def get_model_info(self) -> dict:
        """Return information about the current model/voice.

        Returns:
            Dictionary with model name, language, speaker, etc.
        """
        if self._model_info is None:
            self._model_info = self._extract_model_info()

        return self._model_info

    def _extract_model_info(self) -> dict:
        """Extract model information from the model file and config.

        Returns:
            Dictionary with model metadata.
        """
        info: Dict[str, Any] = {
            "model_path": self.model_path,
            "language": "ru",  # Russian voices
        }

        # Try to read config file for additional metadata
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # Extract relevant fields
                if "name" in config:
                    info["voice_name"] = config["name"]
                if "language" in config:
                    info["language"] = config["language"]
                if "speaker" in config:
                    info["speaker"] = config["speaker"]
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Error reading Piper config: %s", e)

        # Try to extract from model filename
        model_name = os.path.basename(self.model_path)
        info["model_filename"] = model_name

        return info

    def supports_language(self, language_code: str) -> bool:
        """Check if engine supports a given language.

        Args:
            language_code: ISO language code (e.g. "ru", "en").

        Returns:
            True if the engine supports the language.
        """
        lang = language_code.lower()
        # Russian voices support 'ru' and ' Russian'
        if lang in ("ru", "Russian", "rus"):
            return True
        # English voices
        if lang in ("en", "English", "eng"):
            return True
        return False

    def is_loaded(self) -> bool:
        """Check if the voice model is loaded.

        Returns:
            True if the PiperVoice is loaded and ready.
        """
        return self._voice is not None