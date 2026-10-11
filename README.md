# audiobook_ru

Creating an audiobook from a text format

## Overview

`audiobook_ru` is a Python package that converts text books into audiobooks using the open-source [Piper TTS](https://github.com/rhasspy/piper) engine. It handles text normalization, chapter detection, sentence-aware text chunking, audio synthesis, and audio assembly into chapter files and a full audiobook.

## Features

- Russian text normalization (links, images, headings, blockquotes, HTML comments)
- Chapter detection from markdown and front-matter splitting
- Sentence-aware text chunking with abbreviation handling
- Piper TTS adapter for high-quality voice synthesis
- FFmpeg-based audio conversion and chapter assembly
- Full CLI and Python API

## Installation

```bash
# Install in development mode with all dependencies
python3 -m pip install -e '.[dev]'

# Or using Makefile:
make install
```

## Prerequisites

- Python 3.12+
- macOS with Apple Silicon recommended (ffmpeg via Homebrew)
- Piper Russian voice model (download separately)

## 1. Prepare book text

```bash
python3 -m audiobook_ru prepare input/book.txt
```

## 2. Synthesize audio

### 2.1 Synthesize audio with a Russian Piper model

```bash
# Download model from HuggingFace
curl -L -o models/ru_RU-dmitri-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx

curl -L -o models/ru_RU-dmitri-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx.json

# run synthesizer
python3 -m audiobook_ru synthesize --model models/ru_RU-dmitri-medium.onnx
```

### 2.2 Synthesize audio with a Silero TTS

You can also use Silero TTS, which supports multiple Russian voice variants:

```bash
# Using default voice (kseniya)
python3 -m audiobook_ru synthesize --engine silero --model dummy

# Using a specific voice variant
python3 -m audiobook_ru synthesize --engine silero --voice aidar --model dummy

# Available voice variants: aidar, baya, kseniya, xenia, eugene
```

### Voice Variants

Silero Russian TTS supports the following voice speakers:

- `aidar` - male, clear Russian accent
- `baya` - female, expressive
- `kseniya` - female, neutral (default)
- `xenia` - female, warm
- `eugene` - male, different timbre

## 3. Assemble into chapters and full audiobook
python3 -m audiobook_ru assemble

Output: output/audiobook.mp3 and output/chapter_*.mp3

## 4. Clean up work 


```bash
make clean  
```

## Directory Structure

```
audiobook_ru/
├── .gitignore           # Python/project ignores
├── Makefile             # Build/deployment helpers
├── pyproject.toml       # Package configuration
├── config/
│   └── config.example.toml  # Configuration template
├── input/               # Input text files (book.txt, etc.)
├── models/              # Piper model .onnx files
├── work/                # Intermediate work directory
├── output/              # Final audio output
└── src/audiobook_ru/    # Python package
    ├── __init__.py
    ├── __main__.py
    ├── cli.py           # CLI with 5 commands
    ├── text/            # Text processing (normalize, chapters, chunking)
    ├── tts/             # TTS pipeline (Piper adapter)
    ├── pipeline/        # Pipeline orchestration
    └── audio/           # FFmpeg/ffprobe helpers
```

## CLI Commands

### `doctor`

Check environment and dependencies.

```bash
audiobook_ru doctor
```

**Output:**
- Python version
- Piper import status
- FFmpeg availability
- Work/Output directory writability

### `prepare`

Prepare book text into segments for synthesis.

```bash
audiobook_ru prepare input/book.txt [OPTIONS]
```

**Options:**
- `--max-chars N` - Max characters per segment (default: 2200)
- `--workdir DIR` - Work directory (default: `work`)
- `--config FILE` - TOML config file

**What it does:**
- Reads input text
- Normalizes text
- Detects chapters
- Splits into sentence-aware chunks
- Writes segment files to `work/segments/`

### `synthesize`

Synthesize audio from prepared segments.

```bash
audiobook_ru synthesize --model models/ru_RU-denis-medium.onnx [OPTIONS]
```

**Options:**
- `--model MODEL` - Path to Piper .onnx model file (required)
- `--force` - Regenerate all segments
- `--retry-failed` - Retry only previously failed segments
- `--workdir DIR` - Work directory (default: `work`)

**What it does:**
- Reads segments from `work/segments/`
- Synthesizes each segment using Piper TTS
- Writes WAV files to `work/audio/`
- Generates synthesis report

### `preview`

Preview a single synthesized segment as WAV.

```bash
audiobook_ru preview --segment segment_0001 --model models/ru_RU-denis-medium.onnx
```

**Options:**
- `--segment SEG` - Segment ID (e.g., `segment_0001`)
- `--model MODEL` - Path to Piper .onnx model file (required)

### `assemble`

Assemble chapter MP3s and full audiobook.

```bash
audiobook_ru assemble [OPTIONS]
```

**Options:**
- `--bitrate N` - MP3 bitrate in kbps (default: `192k`)
- `--workdir DIR` - Work directory (default: `work`)

**What it does:**
- Converts WAV segments to MP3 using FFmpeg
- Groups segments into chapters
- Concatenates chapter MP3s
- Creates full `output/audiobook.mp3`
- Creates individual `output/chapter_XXX.mp3` files

## Configuration

Copy the example config and adjust as needed:

```bash
cp config/config.example.toml config/config.toml
```

Config file (TOML format):

```toml
# Working directories
work_dir = "work"
output_dir = "output"

# Synthesis settings
max_chars_per_segment = 2200
default_bitrate = "192k"

# Audio settings
sample_rate = 22050
```

## Text Processing

The text processing pipeline handles:

- **Link normalization**: URLs, email addresses
- **Image markup**: `![alt](src)` → descriptive text
- **Headings**: `#`, `##`, etc. → structured text
- **Blockquotes**: `>` → plain text
- **HTML comments**: `<!-- ... -->` → stripped
- **Chapter detection**: `# Chapter` or `# Chapter N`
- **Front matter**: YAML front matter splitting

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v
```

## License

MIT License - see LICENSE for details.
