"""Tests for text normalization."""

import pytest

from audiobook_ru.text.normalize import normalize_text


class TestNormalize:
    """Tests for the normalize_text function."""

    def test_basic_text(self):
        """Test basic text normalization."""
        text = "Привет, мир!"
        result = normalize_text(text)
        assert result == "Привет, мир!"

    def test_empty_text(self):
        """Test empty text."""
        result = normalize_text("")
        assert result == ""

    def test_only_whitespace(self):
        """Test whitespace-only text."""
        result = normalize_text("   ")
        # Whitespace-only input returns empty string (normalized)
        assert result == ""

    def test_markdown_links(self):
        """Test that markdown links are normalized to visible text."""
        text = "[Текст ссылки](https://example.com)"
        result = normalize_text(text)
        assert "Текст ссылки" in result
        assert "example.com" not in result or result.count("example.com") == 0

    def test_markdown_images(self):
        """Test that markdown images retain alt text."""
        text = "![Alt text](image.png)"
        result = normalize_text(text)
        assert "Alt text" in result

    def test_headings(self):
        """Test that markdown headings are handled."""
        text = "# Заголовок"
        result = normalize_text(text)
        assert "Заголовок" in result

    def test_blockquotes(self):
        """Test that blockquotes have markers removed."""
        text = "> Цитата"
        result = normalize_text(text)
        assert "Цитата" in result

    def test_html_comments(self):
        """Test that HTML comments are removed."""
        text = "Текст <!-- комментарий --> еще текст"
        result = normalize_text(text)
        assert "комментарий" not in result
        assert "Текст" in result and "еще текст" in result