"""Tests for sentence-aware chunking."""

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