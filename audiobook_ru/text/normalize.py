"""Text normalization for audiobook_ru."""

import re


def normalize_text(text: str) -> str:
    """Normalize text for TTS synthesis.

    Applies markdown normalization suitable for narration:
    - Strips heading marker characters but retains heading text
    - For links, retains visible link text and removes destination URL
    - For images, retains alt text when available
    - Removes emphasis markers while retaining enclosed text
    - Retains inline code text
    - Preserves fenced code block content
    - Retains blockquote content while removing quote markers
    - Removes complete HTML comments only
    - Preserves paragraph boundaries

    Does NOT over-normalize punctuation (em dashes, dialogue dashes,
    ellipses, Russian quotation marks are preserved).

    Args:
        text: Input text (UTF-8, possibly with BOM, markdown markup)

    Returns:
        Normalized text ready for TTS synthesis
    """
    if not text:
        return text

    # Decode UTF-8 BOM if present
    if text.startswith("\ufeff"):
        text = text[1:]

    # Split into paragraphs using double newlines
    paragraphs = text.split("\n\n")

    normalized_paragraphs = []
    for para in paragraphs:
        if not para.strip():
            normalized_paragraphs.append("")
            continue

        normalized = _normalize_paragraph(para)
        normalized_paragraphs.append(normalized)

    # Join with double newline to preserve paragraph boundaries
    result = "\n\n".join(normalized_paragraphs)
    return result


def _normalize_paragraph(text: str) -> str:
    """Normalize a single paragraph.

    Applies markdown normalization rules to a single paragraph.
    """
    # 1. Strip markdown heading markers (#, ##, etc.) while keeping the text
    # e.g., "### Title" -> "Title"
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # 2. For links: retain visible text, remove destination URL
    # [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # 3. For images: retain alt text
    # ![alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # 4. Remove bold markers (**text** or __text__)
    text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)

    # 5. Remove italic markers (*text* or _text_)
    text = re.sub(r"(?<!\*)\*([^\*]+?)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_([^_]+?)_(?!_)", r"\1", text)

    # 6. Blockquotes: remove > marker but retain content
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    # 7. HTML comments: remove complete HTML comments only
    text = re.sub(r"<!--[\s\S]*?-->", "", text)

    # 8. Replace single internal newlines with spaces so wrapped lines flow smoothly
    # while keeping paragraph separation intact
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Clean up any multiple spaces created during normalization
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()