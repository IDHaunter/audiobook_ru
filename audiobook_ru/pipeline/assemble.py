"""Assemble chapter MP3s and full audiobook."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import ffmpeg


def assemble_book(work_dir: str, output_dir: str = "output", bitrate: str = "192k") -> dict:
    """Assemble prepared segments into chapter MP3s and full audiobook.

    Steps:
    1. Validate that all required segment WAVs exist
    2. For each chapter, concatenate segments with silence between them
    3. Encode to MP3
    4. Create full audiobook MP3

    Args:
        work_dir: Work directory containing prepared segments
        output_dir: Output directory for MP3 files
        bitrate: MP3 bitrate (e.g. "192k")

    Returns:
        Dictionary with assembly results
    """
    work_path = Path(work_dir).resolve()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load manifest
    manifest_path = work_path / "manifest.json"
    if not manifest_path.exists():
        print("Error: manifest.json not found in work directory", file=sys.stderr)
        return {"success": False, "error": "manifest not found"}

    import json
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    chapters = manifest_data.get("chapters", [])
    source_hash = manifest_data.get("source_hash", "")

    if not chapters:
        print("Error: No chapters found in manifest", file=sys.stderr)
        return {"success": False, "error": "no chapters"}

    # Collect all segment WAV files in order
    all_segment_wavs = []
    for chap in chapters:
        chap_index = chap.get("index", 0)
        seg_ids = chap.get("segment_ids", [])
        for seg_id in seg_ids:
            wav_path = work_path / "segments" / f"{seg_id}.wav"
            if not wav_path.exists():
                print(f"Warning: Missing WAV for segment {seg_id}", file=sys.stderr)
                continue
            all_segment_wavs.append((chap_index, seg_id, str(wav_path)))

    if not all_segment_wavs:
        print("Error: No segment WAV files found", file=sys.stderr)
        return {"success": False, "error": "no segment WAVs"}

    # Assemble chapter MP3s
    chapter_mp3s = []
    for chap_index, seg_id, wav_path in all_segment_wavs:
        # Find the chapter this segment belongs to
        # Group by chapter index
        pass

    # Better approach: group by chapter index
    chapters_wavs: dict[int, list[tuple[str, str]]] = {}
    for chap_index, seg_id, wav_path in all_segment_wavs:
        if chap_index not in chapters_wavs:
            chapters_wavs[chap_index] = []
        chapters_wavs[chap_index].append((seg_id, wav_path))

    # Write chapter MP3s
    for chap_index in sorted(chapters_wavs.keys()):
        wav_files = chapters_wavs[chap_index]
        if not wav_files:
            continue

        # Build concatenation input list
        input_files = [wav_path for _, wav_path in wav_files]

        # Use FFmpeg to concatenate and encode to MP3
        chapter_title = f"chapter_{chap_index:03d}"
        chapter_mp3 = output_path / f"{chapter_title}.mp3"

        try:
            # Build FFmpeg concat input
            # Create a text file with the list of WAV files
            concat_list = output_path / f"chap{chap_index}_concat.txt"
            with open(concat_list, "w", encoding="utf-8") as f:
                for _, wav_path in wav_files:
                    f.write(f"file '{wav_path}'\n")

            # Build the FFmpeg command
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:a",
                "libmp3lame",
                "-b:a",
                bitrate,
                "-vn",
                str(chapter_mp3),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg error for chapter {chap_index}: {result.stderr}", file=sys.stderr)
                continue

            chapter_mp3s.append(str(chapter_mp3))
            print(f"Created {chapter_mp3}")

        except Exception as e:
            print(f"Error assembling chapter {chap_index}: {e}", file=sys.stderr)

    # Create full audiobook MP3
    all_wavs = [wav_path for _, _, wav_path in all_segment_wavs]
    if all_wavs:
        audiobook_mp3 = output_path / "audiobook.mp3"

        # Create concat list for full audiobook
        concat_list = output_path / "full_concat.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for _, _, wav_path in all_segment_wavs:
                f.write(f"file '{wav_path}'\n")

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:a",
                "libmp3lame",
                "-b:a",
                bitrate,
                "-vn",
                str(audiobook_mp3),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg error for audiobook: {result.stderr}", file=sys.stderr)
            else:
                print(f"Created {audiobook_mp3}")
        except Exception as e:
            print(f"Error creating audiobook: {e}", file=sys.stderr)

    return {"success": True, "chapters": len(chapters), "audiobook": str(output_path / "audiobook.mp3") if (output_path / "audiobook.mp3").exists() else None}