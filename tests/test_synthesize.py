"""Tests for synthesize audio functionality."""

import json
import os
import tempfile
from pathlib import Path

from audiobook_ru.synthesize import synthesize_segment


def test_synthesize_segment_piper():
    """Test synthesizing a segment with piper engine."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        manifest = {"chapters": [{"segment_ids": ["segment_0001"]}]}
        with open(work_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)
        # Create segments directory
        (work_dir / "segments").mkdir(exist_ok=True)
        (work_dir / "segments" / "segment_0001.txt").write_text("Тестовый текст для синтеза.")
        result = synthesize_segment(
            work_dir=str(work_dir),
            segment_id="segment_0001",
            model_path="models/ru_RU-dmitri-medium.onnx",
            engine="piper",
        )
        assert result is not None


def test_synthesize_segment_silero():
    """Test synthesizing a segment with silero engine."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        manifest = {"chapters": [{"segment_ids": ["segment_0001"]}]}
        with open(work_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)
        # Create segments directory
        (work_dir / "segments").mkdir(exist_ok=True)
        (work_dir / "segments" / "segment_0001.txt").write_text("Тестовый текст для синтеза.")
        result = synthesize_segment(
            work_dir=str(work_dir),
            segment_id="segment_0001",
            model_path="dummy",
            engine="silero",
        )
        assert result is not None


def test_synthesize_segment_no_text():
    """Test synthesizing a segment with no text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        manifest = {"chapters": [{"segment_ids": ["segment_0001"]}]}
        with open(work_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)
        result = synthesize_segment(
            work_dir=str(work_dir),
            segment_id="segment_0001",
            model_path="models/ru_RU-dmitri-medium.onnx",
            engine="piper",
        )
        assert result is not None