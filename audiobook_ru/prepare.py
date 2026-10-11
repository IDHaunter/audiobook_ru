"""Prepare a book for audiobook synthesis."""

from pathlib import Path
import shutil

from .pipeline import manifest as manifest_mod
from .pipeline.manifest import compute_sha256
from .text.chapters import split_book
from .text.normalize import normalize_text
from .text import chunking


def prepare_book(
    input_path: str,
    work_dir: str = "work",
    max_chars: int = 1000,
    config_path: str = None,
) -> dict:
    """Parse a book into chapters and TTS-sized text segments.

    Markdown chapter headings such as ``## 1. Утопия`` are treated as
    chapter boundaries. An initial unnumbered heading such as
    ``## Последний враг человечества`` is treated as the book title.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be greater than zero")

    source_path = Path(input_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    source_bytes = source_path.read_bytes()
    # utf-8-sig transparently handles an optional UTF-8 BOM.
    raw_text = source_bytes.decode("utf-8-sig")
    source_hash = compute_sha256(str(source_path))

    front_matter, parsed_chapters = split_book(raw_text)
    if not parsed_chapters:
        body = normalize_text(raw_text).strip()
        if not body:
            raise ValueError(f"No readable text found in {input_path}")
        parsed_chapters = [(1, "Full Text", body)]

    work_path = Path(work_dir).resolve()
    segments_dir = work_path / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    # Remove previous segment text files: IDs and chapter membership are rebuilt
    # from scratch, so stale files must not survive a new preparation run.
    for old_file in segments_dir.glob("segment_*.txt"):
        old_file.unlink()

    manifest = manifest_mod.Manifest(str(work_path))
    manifest.load()
    manifest.manifest["chapters"] = []
    manifest.manifest["segments"] = []
    manifest.update_source_info(
        source_path=str(source_path),
        source_hash=source_hash,
        preparation_settings={
            "max_chars": max_chars,
            "normalizer_version": "1.1.0",
        },
    )

    all_segment_ids = []
    segment_idx = 1

    for chapter_index, chapter_title, chapter_body in parsed_chapters:
        body = normalize_text(chapter_body).strip()
        if not body:
            # A heading with no body is not useful as an audio chapter.
            continue

        # Include the chapter heading in narration, but not the book title.
        # Avoid duplicating it if the source body already begins with the title.
        if chapter_title and not body.casefold().startswith(chapter_title.casefold()):
            body = f"{chapter_title}.\n\n{body}"

        chunks = chunking.split_into_chunks(body, max_chars)
        segment_ids = []

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            segment_id = f"segment_{segment_idx:04d}"
            segment_idx += 1
            (segments_dir / f"{segment_id}.txt").write_text(
                chunk, encoding="utf-8"
            )
            segment_ids.append(segment_id)
            all_segment_ids.append(segment_id)

        if segment_ids:
            manifest.add_chapter(
                index=chapter_index,
                title=chapter_title,
                segment_ids=segment_ids,
            )

    if not manifest.manifest["chapters"]:
        raise ValueError(
            "No non-empty chapters were found. Check the input file and heading format."
        )

    manifest.save()

    print(f"\n[📚] Prepared: {source_path}")
    print(f"[📂] Segments: {segments_dir}")
    print(
        f"[📊] Chapters: {len(manifest.manifest['chapters'])}; "
        f"segments: {len(all_segment_ids)}\n"
    )

    return {
        "chapters": len(manifest.manifest["chapters"]),
        "segments": len(all_segment_ids),
        "source_hash": source_hash,
        "front_matter": front_matter,
    }
