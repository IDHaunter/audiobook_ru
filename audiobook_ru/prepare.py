"""Prepare: normalize, chapters, segments, and manifest generation."""

import re
from pathlib import Path

from .pipeline import manifest as manifest_mod
from .pipeline.manifest import compute_sha256


def prepare_book(input_path: str, work_dir: str = "work", max_chars: int = 2200, config_path: str = None) -> dict:
    """Prepare a book for TTS synthesis.

    Steps:
        1. Read and normalize the input text
        2. Detect chapters
        3. Split chapters into segments
        4. Write segment text files
        5. Generate versioned manifest

    Args:
        input_path: Path to input .txt or .md file
        work_dir: Work directory for output
        max_chars: Maximum characters per segment
        config_path: Optional config file path

    Returns:
        Dictionary with preparation results
    """
    from .text.normalize import normalize_text
    from .text.chapters import split_front_matter

    work_path = Path(work_dir).resolve()
    work_path.mkdir(parents=True, exist_ok=True)
    segments_dir = work_path / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[📚] Preparing the book: {input_path}")
    print(f"[📂] Work path: {work_path}")

    # Read source text
    source_path = Path(input_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read raw bytes for hash computation
    source_bytes = source_path.read_bytes()
    source_hash = compute_sha256(str(source_path))

    # Read and decode text
    raw_text = source_bytes.decode("utf-8-sig")  # handles BOM
    normalized = normalize_text(raw_text)

    # Detect chapters
    front_matter, chapters = split_front_matter(normalized)

    # If no chapters found, treat entire text as one chapter
    if not chapters:
        chapters = [(1, "Full Text")]
        normalized_body = normalized
    else:
        normalized_body = normalized

    # Build manifest
    prep_settings = {"max_chars": max_chars}

    manifest = manifest_mod.Manifest(str(work_path))
    manifest.load()

    # Update source info
    manifest.update_source_info(
        source_path=input_path,
        source_hash=source_hash,
        preparation_settings=prep_settings,
    )

    # Process each chapter
    all_segment_ids = []
    segment_idx = 0

    for chap_index, chap_title in chapters:
        chap_segments = _split_chapter_into_segments(
            normalized_body, max_chars, chap_index
        )

        segment_ids = []
        for seg_index, seg_text in chap_segments:
            segment_id = f"segment_{segment_idx:04d}"
            segment_idx += 1

            # Write segment text file
            segment_file = segments_dir / f"{segment_id}.txt"
            segment_file.write_text(seg_text, encoding="utf-8")

            segment_ids.append(segment_id)
            all_segment_ids.append(segment_id)

        # Add chapter to manifest
        manifest.add_chapter(
            index=chap_index,
            title=chap_title,
            segment_ids=segment_ids,
        )

    # Save manifest
    manifest.save()

    # Information
    print(f"[✨] Normalized texts (segments) are saved in: {segments_dir}")
    print(f"[📄] Project manifest updated/saved in: {work_path}")
    print(f"[📊] Statistics: heads detected — {len(chapters)}, segments created — {len(all_segment_ids)}\n")

    result = {
        "chapters": len(chapters),
        "segments": len(all_segment_ids),
        "source_hash": source_hash,
        "front_matter": front_matter if "front_matter" in locals() else "",
    }

    return result


def _split_chapter_into_segments(normalized_text: str, max_chars: int, chap_index: int):
    """Split a chapter's text into segments.

    Args:
        normalized_text: Normalized chapter text
        max_chars: Maximum characters per segment
        chap_index: Chapter index (for context)

    Yields:
        Tuples of (segment_index, segment_text)
    """
    from .text import chunking

    chunks = chunking.split_into_chunks(normalized_text, max_chars)

    for chunk_idx, chunk_text in enumerate(chunks):
        yield chunk_idx, chunk_text.strip()