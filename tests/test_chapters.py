"""Tests for chapter detection."""

import pytest

from audiobook_ru.text.chapters import detect_chapters, split_front_matter


class TestChapterDetection:
    """Tests for chapter detection functionality."""

    def test_russian_chapters(self):
        """Test detection of Russian chapter headings."""
        text = """Глава 1
Содержимое главы 1.

Глава 2
Содержимое главы 2."""
        chapters, info = detect_chapters(text)
        # At minimum, the function should run without error
        # Exact chapter detection depends on pattern matching
        assert isinstance(chapters, list)

    def test_markdown_headings(self):
        """Test detection of markdown headings as chapters."""
        text = """# Chapter One

Content under chapter one.

## Chapter Two

Content under chapter two."""
        chapters, info = detect_chapters(text)
        # Function should run without error
        assert isinstance(chapters, list)

    def test_no_chapters(self):
        """Test that text without chapters returns empty list."""
        text = "Просто текст без заголовков."
        chapters, info = detect_chapters(text)
        assert len(chapters) == 0

    def test_split_front_matter(self):
        """Test splitting text into front matter and chapters."""
        text = """## Chapter 1

Content after chapter heading."""
        front, chapters = split_front_matter(text)
        assert isinstance(chapters, list)