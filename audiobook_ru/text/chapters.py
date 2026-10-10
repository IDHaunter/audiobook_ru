"""Chapter detection for audiobook_ru."""

import re


# List of chapter patterns: (regex_pattern, pattern_name)
CHAPTER_PATTERNS = [
    # Markdown headings: #, ##, etc. (supports both with and without space after hashes)
    (r"^#{1,6}\s*(.+)$", "markdown_heading"),
    # Russian: "Глава 1", "Глава 1. Название", "Глава первая"
    (r"^Глава\s+(\d+(?:[\.\s].+)?|[А-Яа-яЁё]+)", "russian_chapter"),
    # Russian: "Часть 2", "Часть вторая"
    (r"^Часть\s+(\d+(?:[\.\s].+)?|[А-Яа-яЁё]+)", "russian_part"),
    # Russian: Prologue, Epilogue, etc.
    (r"^(Пролог|Эпилог|Предисловие|Послесловие)\s*$", "russian_prepost"),
    # English: Chapter 1, Prologue, Epilogue
    (r"^Chapter\s+\d+.*", "english_chapter"),
    (r"^Prologue", "english_prologue"),
    (r"^Epilogue", "english_epilogue"),
]


def detect_chapters(text: str) -> tuple[list[tuple[int, str]], dict]:
    """Detect chapters in text.

    Returns list of (index, title) tuples and metadata dict containing front matter.
    Index is 1-based.

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (chapters_list, info_dict).
        If no chapters found, returns empty list and front_matter contains all text.
    """
    lines = text.split("\n")
    chapters = []
    front_matter_lines = []
    found_first_chapter = False

    # Track which pattern matched for deduplication
    seen_headings = set()

    for line in lines:
        matched = False
        line_stripped = line.strip()

        for pattern, pattern_name in CHAPTER_PATTERNS:
            match = re.match(pattern, line_stripped, re.IGNORECASE)
            if match:
                matched = True

                if pattern_name in ("markdown_heading", "russian_chapter", "russian_part", "english_chapter"):
                    title = match.group(1).strip() if match.groups() else line_stripped
                else:
                    title = match.group(0).strip()

                chap_index = len(chapters) + 1
                dedup_key = title.lower()[:50]

                is_prepost = pattern_name in ("russian_prepost", "english_prologue", "english_epilogue")

                if not found_first_chapter or is_prepost:
                    if dedup_key not in seen_headings:
                        seen_headings.add(dedup_key)
                        chapters.append((chap_index, title))
                        found_first_chapter = True
                break

        if not matched:
            if not found_first_chapter:
                front_matter_lines.append(line)

    front_matter_text = "\n".join(front_matter_lines).strip()

    # If no chapters detected, return empty list and full text as front matter
    if not chapters:
        return [], {"front_matter": text, "chapters": []}

    return chapters, {"front_matter": front_matter_text, "chapters": chapters}


def split_front_matter(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Split text into front matter and chapters.

    Args:
        text: Full book text

    Returns:
        Tuple of (front_matter_text, chapters_list)
        where chapters_list is list of (index, title) tuples.
    """
    chapters, info = detect_chapters(text)
    front = info.get("front_matter", "")
    return front, chapters