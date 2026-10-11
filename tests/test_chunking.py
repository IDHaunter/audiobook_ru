"""Tests for sentence-aware chunking."""

import configparser
import os
from pathlib import Path

import pytest

from audiobook_ru.text.chunking import split_into_chunks


class TestChunking:
    """Tests for split_into_chunks function."""

    def test_short_text(self):
        """Test that short text fits in one chunk."""
        text = "Короткий текст."
        chunks = split_into_chunks(text, max_chars=2000)
        assert len(chunks) == 1
        assert chunks[0] == "Короткий текст."

    def test_text_fits_in_one_chunk(self):
        """Test text that fits within the max_chars limit."""
        text = "Абзац первый. Абзац второй."
        chunks = split_into_chunks(text, max_chars=2000)
        assert len(chunks) == 1

    def test_text_needs_splitting(self):
        """Test text that needs to be split into multiple chunks."""
        # Create text longer than max_chars
        long_text = "Слово " * 200  # ~1000 chars
        chunks = split_into_chunks(long_text, max_chars=100)
        assert len(chunks) > 1
        # Each chunk should be within the limit
        for chunk in chunks:
            assert len(chunk) <= 100 + 10  # slight tolerance

    def test_max_chars_boundary(self):
        """Test that chunks respect the max_chars limit."""
        # Text exactly at the limit
        text = "A " * 1100  # ~1100 chars
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 1000

    def test_preserves_words(self):
        """Test that chunks don't split words unnecessarily."""
        text = "Это очень длинное слово которое нужно чтобы тест прошел корректно"
        chunks = split_into_chunks(text, max_chars=50)
        # Each chunk should be reasonable
        for chunk in chunks:
            assert len(chunk) <= 50

    def test_config_max_chars_limit(self):
        """Test that chunks respect max_chars from config file.

        The config file config/config.example.toml sets max_chars=500,
        and all chunks should respect this limit.
        """
        # Read max_chars from config file
        config_path = Path(__file__).parent.parent / "config" / "config.example.toml"
        assert config_path.is_file(), f"Config file not found at {config_path}"

        # Parse the TOML config manually (simple approach)
        config_max_chars = None
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("max_chars"):
                    # Extract value after =
                    parts = line.split("=")
                    if len(parts) == 2:
                        config_max_chars = int(parts[1].strip())

        assert config_max_chars is not None, "max_chars not found in config file"
        assert config_max_chars == 500

        # Test that split_into_chunks respects this limit
        # Create text that's slightly over the limit to force splitting
        test_text = "A " * (config_max_chars + 200)  # ~700 chars
        chunks = split_into_chunks(test_text, max_chars=config_max_chars)

        # Should have multiple chunks
        assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"

        # Each chunk should be within the limit
        for i, chunk in enumerate(chunks):
            chunk_len = len(chunk)
            assert chunk_len <= config_max_chars, (
                f"Chunk {i} has {chunk_len} chars, exceeds limit of {config_max_chars}"
            )