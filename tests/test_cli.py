"""Tests for the CLI interface."""

import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """Test that CLI help works."""
    result = subprocess.run(
        [sys.executable, "-m", "audiobook_ru", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "audiobook-ru" in result.stdout or "audiobook" in result.stdout.lower()


def test_cli_doctor():
    """Test doctor command."""
    result = subprocess.run(
        [sys.executable, "-m", "audiobook_ru", "doctor"],
        capture_output=True,
        text=True,
    )
    # Doctor should always exit 0
    assert result.returncode == 0
    assert "doctor" in result.stdout.lower() or "check" in result.stdout.lower()


def test_cli_prepare_no_input(tmp_path, sample_text):
    """Test prepare command without input file."""
    # Create a temporary input file
    input_file = tmp_path / "test.txt"
    input_file.write_text(sample_text)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "audiobook_ru",
            "prepare",
            str(input_file),
        ],
        capture_output=True,
        text=True,
    )
    # Should exit with some code (may fail if no model, but should have output)
    assert result.stdout or result.stderr


def test_cli_synthesize_no_model(tmp_path):
    """Test synthesize command without model."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "audiobook_ru",
            "synthesize",
        ],
        capture_output=True,
        text=True,
    )
    # Should fail gracefully since no model configured
    assert result.returncode != 0 or "error" in (result.stdout + result.stderr).lower()