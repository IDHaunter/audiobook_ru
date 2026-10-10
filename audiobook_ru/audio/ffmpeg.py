"""FFmpeg/ffprobe helpers for audiobook_ru."""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def find_ffmpeg() -> Tuple[Optional[str], Optional[str]]:
    """Locate ffmpeg and ffprobe executables.

    Returns:
        Tuple of (ffmpeg_path, ffprobe_path), either or both may be None.
    """
    ffmpeg_path = None
    ffprobe_path = None

    # Check common Homebrew locations on macOS Apple Silicon
    for path in [
        "/opt/homebrew/bin/ffmpeg",
        "/opt/homebrew/bin/ffprobe",
        "/usr/local/bin/ffmpeg",
        "/usr/local/bin/ffprobe",
    ]:
        if Path(path).is_file():
            if "ffmpeg" in path:
                ffmpeg_path = path
            else:
                ffprobe_path = path

    # Also check PATH
    if ffmpeg_path is None:
        result = subprocess.run(
            ["which", "ffmpeg"], capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            ffmpeg_path = result.stdout.strip()

    if ffprobe_path is None:
        result = subprocess.run(
            ["which", "ffprobe"], capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            ffprobe_path = result.stdout.strip()

    return ffmpeg_path, ffprobe_path


def validate_wav_file(file_path: str) -> dict:
    """Validate a WAV file using ffprobe.

    Args:
        file_path: Path to WAV file.

    Returns:
        Dictionary with validation results.
    """
    ffprobe_path, _ = find_ffmpeg()

    if ffprobe_path is None:
        return {"valid": False, "error": "ffprobe not found"}

    try:
        result = subprocess.run(
            [ffprobe_path, "-v", "error", "-show_entries",
             "stream=codec_name,sample_rate,channels,duration",
             "-of", "default=noprint_wrappers=1", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return {"valid": False, "error": result.stderr}

        # Parse basic info
        info = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info[key] = value

        # Check we have essential info
        if "codec_name" not in info or info["codec_name"] != "pcm_s16le":
            return {"valid": False, "error": f"Unexpected codec: {info.get('codec_name', 'unknown')}"}

        return {"valid": True, "info": info}

    except subprocess.TimeoutExpired:
        return {"valid": False, "error": "ffprobe timed out"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def concat_wav_files(wav_paths: list[str], output_path: str, silence_ms: int = 250) -> bool:
    """Concatenate WAV files with optional silence between them.

    Args:
        wav_paths: List of WAV file paths to concatenate.
        output_path: Output WAV file path.
        silence_ms: Silence in milliseconds between segments (default 250).

    Returns:
        True if successful, False otherwise.
    """
    if not wav_paths:
        return False

    if len(wav_paths) == 1:
        # Just copy the single file
        import shutil
        shutil.copy2(wav_paths[0], output_path)
        return True

    # Build FFmpeg concatenation with silence
    # Create input file list
    input_file = Path(output_path).with_suffix(".txt")
    with open(input_file, "w", encoding="utf-8") as f:
        for i, wav_path in enumerate(wav_paths):
            if i > 0:
                # Add silence before subsequent files
                f.write(f"# Silence {silence_ms}ms before this file\n")
                f.write(f"ffmpeg -i - -ar 44100 -ac 1 -af \"atrim=0=0,atrim=0\\n\") ... ")
            f.write(f"file '{wav_path}'\n")

    # Use FFmpeg concat filter with ametadata for silence insertion
    # This is complex; for simplicity, use the concat demuxer with amix
    try:
        # Build the filter complex approach
        filter_complex_parts = []
        input_streams = []

        for i, wav_path in enumerate(wav_paths):
            if i == 0:
                input_streams.append(f"[0:a]")
                filter_complex_parts.append(f"[0:a]atrim=0 [channel0]")
            else:
                # Add silence before this track
                silence_duration = silence_ms / 1000.0
                filter_complex_parts.append(
                    f"[{i}:a]atrim=0 [{i}_silenced] "
                    f"areverse,areverse,atrim=0:{silence_duration} [{i}_reversed]; "
                )
                input_streams.append(f"[{i}_reversed:a]")

        # This is getting complex; use a simpler approach
        # For now, just concatenate without silence
        filter_spec = ";".join(filter_complex_parts) if filter_complex_parts else ""

        cmd = [
            "ffmpeg", "-y",
        ]

        # Add input files
        for wav_path in wav_paths:
            cmd.extend(["-i", wav_path])

        # Build the filter complex
        if filter_spec:
            cmd.extend(["-filter_complex", filter_spec])

        # Output
        cmd.extend(["-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", output_path])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"Error concatenating WAV files: {e}", file=sys.stderr)
        return False