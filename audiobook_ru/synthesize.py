"""Synthesis module for audiobook_ru.

Provides functions to synthesize audio from prepared segments using Piper TTS.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from . import tts as tts_mod
from .pipeline import manifest as manifest_mod


def synthesize_segment(work_dir: str, segment_id: str, model_path: str) -> str:
    """Synthesize a single segment to WAV audio.

    Args:
        work_dir: Base work directory containing the manifest and segments.
        segment_id: The segment ID to synthesize (e.g. 'segment_0001').
        model_path: Path to the Piper ONNX model file.

    Returns:
        Path to the synthesized WAV file.
    """
    work_path = Path(work_dir)
    manifest_path = work_path / "manifest.json"

    # Load manifest
    manifest_loader = manifest_mod.Manifest(work_path)
    manifest = manifest_loader.load()

    # Get segment text
    segment_text = ""
    for chapter in manifest.get("chapters", []):
        segment_ids = chapter.get("segment_ids", [])
        if segment_id in segment_ids:
            # Find the segment index within the chapter
            seg_idx = segment_ids.index(segment_id)
            # Read the segment text file
            seg_file = work_path / "segments" / f"{segment_id}.txt"
            if seg_file.exists():
                with open(seg_file, "r", encoding="utf-8") as f:
                    segment_text = f.read()
            break

    if not segment_text.strip():
        print(f"Warning: No text found for segment {segment_id}")
        return str(work_path / "output" / f"{segment_id}.wav")

    # Use the TTS engine to synthesize
    tts_engine = tts_mod.PiperEngine(model_path=model_path, work_dir=work_dir)
    output_path = work_path / "output" / f"{segment_id}.wav"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = tts_engine.synthesize(segment_text, str(output_path))

    print(f"Synthesized segment {segment_id}: {result['duration']:.2f}s")
    return str(output_path)


def run_synthesis(
    work_dir: str,
    model_path: str,
    force: bool = False,
    retry_failed: bool = False,
) -> int:
    """Run synthesis for all missing/invalid segments.

    Args:
        work_dir: Base work directory containing the manifest and segments.
        model_path: Path to the Piper ONNX model file.
        force: If True, regenerate all segments even if valid audio exists.
        retry_failed: If True, retry only failed segments.

    Returns:
        Exit code (0 for success).
    """
    work_path = Path(work_dir)
    manifest_path = work_path / "manifest.json"

    # Load manifest
    manifest_loader = manifest_mod.Manifest(work_path)
    manifest = manifest_loader.load()

    # Get all segments from manifest
    all_segment_ids = []
    for chapter in manifest.get("chapters", []):
        segment_ids = chapter.get("segment_ids", [])
        all_segment_ids.extend(segment_ids)

    # Filter segments to synthesize
    output_dir = work_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    synthesized_count = 0
    failed_count = 0

    for segment_id in all_segment_ids:
        seg_output = output_dir / f"{segment_id}.wav"

        # Check if segment already has valid audio
        should_synthesize = False

        if force:
            should_synthesize = True
        elif not seg_output.exists():
            should_synthesize = True
        elif retry_failed:
            # Check if previous synthesis failed (no output file or invalid)
            if not seg_output.exists():
                should_synthesize = True

        if should_synthesize:
            # Get segment text
            segment_text = ""
            for chapter in manifest.get("chapters", []):
                segment_ids = chapter.get("segment_ids", [])
                if segment_id in segment_ids:
                    seg_idx = segment_ids.index(segment_id)
                    seg_file = work_path / "segments" / f"{segment_id}.txt"
                    if seg_file.exists():
                        with open(seg_file, "r", encoding="utf-8") as f:
                            segment_text = f.read()
                    break

            if segment_text.strip():
                try:
                    tts_engine = tts_mod.PiperEngine(model_path=model_path, work_dir=work_dir)
                    tts_engine.synthesize(segment_text, str(seg_output))
                    synthesized_count += 1
                    print(f"Synthesized {segment_id}")
                except Exception as e:
                    print(f"Failed to synthesize {segment_id}: {e}")
                    failed_count += 1
            else:
                print(f"Warning: No text for segment {segment_id}, skipping")
                failed_count += 1

    print(f"Synthesis complete: {synthesized_count} synthesized, {failed_count} failed")
    return 0