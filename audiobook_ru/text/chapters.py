"""Chapter and front-matter detection for plain-text and Markdown books.

Supported chapter markers:
- Markdown headings: ``## 1. Chapter title``, ``### Глава 2``, etc.
- Plain-text headings: ``Глава 1``, ``Часть вторая``, ``Пролог``, ``Эпилог``.
- Setext Markdown headings, e.g. ``Chapter 1`` followed by ``-----``.

A leading unnumbered Markdown heading (for example, the book title) is not
treated as a chapter unless it uses a known chapter label.
"""

from __future__ import annotations

import re
from typing import TypedDict

class ChapterInfo(TypedDict):
    front_matter: str
    chapters: list[tuple[int, str]]


# Chapter labels that can be recognized even without Markdown markers.
_TEXT_CHAPTER_RE = re.compile(
    r"^(?:"
    r"(?:глава|часть|книга|раздел)\s+.+|"
    r"(?:пролог|эпилог|предисловие|послесловие)"
    r")$",
    re.IGNORECASE,
)

# Numbered headings, e.g. "1. Title", "1 Title", "1.2 Title", "Глава 1".
_NUMBERED_HEADING_RE = re.compile(
    r"^(?:"
    r"\d+(?:\.\d+)*[.)]?\s+.*|"
    r"(?:глава|часть|книга|раздел)\s+.+|"
    r"(?:пролог|эпилог|предисловие|послесловие)"
    r")$",
    re.IGNORECASE,
)

_MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_SETEXT_HEADING_RE = re.compile(r"^\s*(=+|-{3,})\s*$")


def _clean_heading(value: str) -> str:
    """Strip surrounding whitespace and simple Markdown emphasis/code wrappers."""
    value = value.strip()

    # Repeatedly remove a single pair of wrappers to handle e.g. **`Title`**.
    wrappers = (("**", "**"), ("__", "__"), ("*", "*"), ("_", "_"), ("`", "`"))
    changed = True
    while changed and len(value) >= 2:
        changed = False
        for left, right in wrappers:
            if value.startswith(left) and value.endswith(right):
                value = value[len(left):-len(right)].strip()
                changed = True
                break

    return value


def _is_chapter_heading(title: str, markdown_level: int | None = None) -> bool:
    """Return whether a heading looks like a chapter marker."""
    title = _clean_heading(title)
    return bool(
        _NUMBERED_HEADING_RE.fullmatch(title)
        or _TEXT_CHAPTER_RE.fullmatch(title)
    )


def _collect_markdown_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """Collect Markdown ATX and Setext headings as (line, level, title)."""
    headings: list[tuple[int, int, str]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        match = _MARKDOWN_HEADING_RE.match(line)
        if match:
            title = _clean_heading(match.group(2))
            if title:
                headings.append((i, len(match.group(1)), title))
            i += 1
            continue

        # Setext headings: a non-empty line followed by === or ---.
        if i + 1 < len(lines) and line.strip():
            underline = _SETEXT_HEADING_RE.fullmatch(lines[i + 1].strip())
            if underline:
                marker = underline.group(1)
                level = 1 if marker.startswith("=") else 2
                headings.append((i, level, _clean_heading(line)))
                i += 2
                continue

        i += 1

    return headings


def split_book(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Split a book into front matter and chapters.

    Returns:
        ``(front_matter, [(chapter_index, chapter_title, chapter_body), ...])``.

    The heading line is excluded from ``chapter_body``. If no reliable chapter
    markers are found, the non-empty document is returned as one ``Full Text``
    chapter. A leading unnumbered heading such as ``## Book title`` is retained
    in front matter rather than treated as a chapter.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = text.split("\n")

    markdown_headings = _collect_markdown_headings(lines)
    chapter_heads = [
        heading
        for heading in markdown_headings
        if _is_chapter_heading(heading[2], heading[1])
    ]

    # Also detect plain-text chapter markers. Avoid mixing this fallback with
    # Markdown results: when Markdown chapter headings exist, they define the
    # document's chapter boundaries.
    if not chapter_heads:
        for line_no, line in enumerate(lines):
            candidate = _clean_heading(line)
            if candidate and _TEXT_CHAPTER_RE.fullmatch(candidate):
                chapter_heads.append((line_no, 0, candidate))

    if not chapter_heads:
        # No reliable chapter markers: return empty list.
        return "", []

    # Remove duplicate markers at the same line (defensive for future patterns).
    deduplicated: list[tuple[int, int, str]] = []
    seen_lines: set[int] = set()
    for heading in chapter_heads:
        if heading[0] not in seen_lines:
            deduplicated.append(heading)
            seen_lines.add(heading[0])
    chapter_heads = deduplicated

    first_start = chapter_heads[0][0]
    front_matter = "\n".join(lines[:first_start]).strip()
    chapters: list[tuple[int, str, str]] = []

    for position, (start_line, _level, title) in enumerate(chapter_heads):
        end_line = (
            chapter_heads[position + 1][0]
            if position + 1 < len(chapter_heads)
            else len(lines)
        )
        body = "\n".join(lines[start_line + 1:end_line]).strip()
        chapters.append((position + 1, title, body))

    return front_matter, chapters


def detect_chapters(text: str) -> tuple[list[tuple[int, str]], ChapterInfo]:
    """Compatibility wrapper for the original public API."""
    front_matter, chapters_with_body = split_book(text)
    chapters = [(index, title) for index, title, _body in chapters_with_body]
    return chapters, {"front_matter": front_matter, "chapters": chapters}


def split_front_matter(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Compatibility wrapper retained for existing callers."""
    chapters, info = detect_chapters(text)
    return info["front_matter"], chapters