"""Sentence-aware chunking for audiobook_ru."""

import re


# Russian abbreviations that should NOT trigger sentence splits
RUSSIAN_ABBREVIATIONS = {
    "т. д.",  # and so on
    "т. п.",  # and the like
    "т. н.",  # so-called
    "г.",     # city
    "ул.",    # street
    "пр.",    # avenue/prospect
    "пер.",   # lane/alley
    "пл.",    # square
    "м.",     # meter
    "кв.",    # apartment
    "фл.",    # floor
    "д.",     # house/building
    "кв. м.",  # square meter
    "стр.",   # page
    "бл.",    # block
    "изд.",   # edition
    "т. ч.",  # including
    "фнд.",   # fund
    "д. р.",  # date of birth
}

# Common initials patterns: A. B. or A.B.
INITIALS_PATTERN = re.compile(r"[A-Z]\.\s*[A-Z]\.")


def split_into_chunks(
    text: str,
    max_chars: int = 2200,
) -> list[str]:
    """Split text into chunks suitable for TTS synthesis.

    Splits on paragraph and sentence boundaries wherever possible.
    Does not split a sentence unless it alone exceeds the limit.
    If a sentence is too long, splits at whitespace near the limit.

    Args:
        text: Text to split (already normalized).
        max_chars: Maximum characters per chunk.

    Returns:
        List of text chunks, each within max_chars limit (except
        atomic tokens that are longer).
    """
    if not text.strip():
        return []

    chunks = []
    remaining = text.strip()

    while remaining:
        chunk, remaining = _split_one_chunk(remaining, max_chars)
        if chunk:
            chunks.append(chunk)

    return chunks


def _split_one_chunk(remaining: str, max_chars: int) -> tuple[str, str]:
    """Split one chunk from the remaining text.

    Returns:
        Tuple of (chunk_text, remaining_text).
        remaining_text may be empty string if no more text.
    """
    if not remaining.strip():
        return "", ""

    # If the entire remaining text fits, return it
    if len(remaining) <= max_chars:
        return remaining, ""

    # Try to split on sentence boundary within the limit
    sentence_result = _try_split_by_sentence(remaining, max_chars)
    if sentence_result:
        return sentence_result

    # Try to split on paragraph boundary
    paragraph_result = _try_split_by_paragraph(remaining, max_chars)
    if paragraph_result:
        return paragraph_result

    # Fall back to whitespace split near the limit
    return _split_by_whitespace(remaining, max_chars)


def _try_split_by_sentence(text: str, max_chars: int) -> tuple[str, str] | None:
    """Try to split text at the furthest possible sentence boundary within the limit.

    Accumulates as many sentences as fit within max_chars.

    Returns:
        Tuple of (chunk_text, remaining_text) or None if no suitable boundary found.
    """
    abbr_set = set(RUSSIAN_ABBREVIATIONS)

    # Find all potential sentence endings (. ? !) in the text
    # We look for . ? ! followed by whitespace or end of string
    sentence_positions = []
    for match in re.finditer(r"[.!?](\s+|$)", text):
        end_pos = match.end()
        preceding_text = text[:end_pos].strip()

        # Check if the sentence ending follows an abbreviation
        words = preceding_text.split()
        if words:
            last_word = words[-1]
            word_without_trailing = last_word.rstrip(".!?")
            if word_without_trailing in abbr_set:
                continue  # Skip this sentence ending - it follows an abbreviation

        sentence_positions.append(match.end())

    if not sentence_positions:
        return None

    best_pos = None

    # Find the furthest sentence boundary that fits within max_chars
    for pos in sentence_positions:
        chunk_end = pos - 1  # Include the sentence ending punctuation
        chunk = text[:chunk_end].strip()

        if len(chunk) <= max_chars:
            best_pos = pos
        else:
            # Positions are sorted in ascending order; further positions will exceed max_chars
            break

    if best_pos is not None:
        chunk_end = best_pos - 1
        chunk = text[:chunk_end].strip()
        rest = text[chunk_end + 1 :].lstrip()
        if chunk:
            return chunk, rest

    # No suitable sentence boundary found within limit
    return None


def _try_split_by_paragraph(text: str, max_chars: int) -> tuple[str, str] | None:
    """Try to split text at a paragraph boundary within the limit.

    Returns:
        Tuple of (chunk_text, remaining_text) or None.
    """
    # Look for double newline
    idx = text.find("\n\n")
    if idx == -1:
        return None

    chunk = text[:idx].strip()
    rest = text[idx + 2 :].strip()

    if not chunk:
        return None

    if len(chunk) <= max_chars:
        return chunk, rest

    return None


def _split_by_whitespace(text: str, max_chars: int) -> tuple[str, str]:
    """Fall back to splitting at whitespace near the limit.

    Returns:
        Tuple of (chunk, remaining).
    """
    # Find a good break point near the limit
    limit = max_chars

    if len(text) <= limit:
        return text, ""

    # Find the last space within the limit
    split_pos = text.rfind(" ", 0, limit)

    if split_pos <= 0:
        # No space found; split at limit and warn
        split_pos = limit

    chunk = text[:split_pos].strip()
    rest = text[split_pos:].lstrip()

    return chunk, rest