# Makefile for audiobook_ru
# ========================
# Local-first TTS audiobook generator using Piper
# ========================

.PHONY: all help doctor prepare synthesize assemble clean test lint format

# --- Default target ---
all: help

# --- Help ---
help:
	@echo "audiobook_ru Makefile targets:"
	@echo ""
	@echo "  install       Install package in development mode"
	@echo "  doctor        Check environment and configuration"
	@echo "  prepare       Prepare book text (needs input file)"
	@echo "  synthesize    Synthesize audio from prepared segments"
	@echo "  assemble      Assemble chapter MP3s and full audiobook"
	@echo "  clean         Clean work and output directories"
	@echo "  test          Run pytest test suite"
	@echo "  lint          Run ruff linter"
	@echo "  format        Format code with ruff"
	@echo "  install-deps  Install Python dependencies"
	@echo "  new-voice     Download a new Piper voice model"

# --- Installation ---
install:
	pip install -e ".[dev]"

install-deps:
	pip install piper-tts ffmpeg-python

# --- Environment checks ---
doctor:
	@echo "=== audiobook_ru doctor ==="
	@python3 -c "import piper; print('Piper: OK')" 2/echo "Piper: checking..."
	@which ffmpeg > /dev/null 2>&1 && echo "FFmpeg: OK" || echo "FFmpeg: NOT FOUND"
	@python3 --version

# --- Text preparation ---
prepare:
	@echo "Usage: make prepare INPUT=path/to/book.txt [MAX_CHARS=2200]"
	@if [ -z "$(INPUT)" ]; then \
		echo "Error: INPUT variable not set"; \
		echo "Example: make prepare INPUT=book.txt"; \
	else \
		python -m audiobook_ru prepare "$(INPUT)" $(MAX_CHARS); \
	fi

# --- Synthesis ---
synthesize:
	@echo "Usage: make synthesize MODEL=path/to/model.onnx [FORCE=1] [RETRY_FAILED=1]"
	@if [ -z "$(MODEL)" ]; then \
		echo "Error: MODEL variable not set"; \
		echo "Example: make synthesize MODEL=ru_RU-medium-high.onnx"; \
	else \
		python -m audiobook_ru synthesize --model "$(MODEL)" $(FORCE_PARAM) $(RETRY_PARAM); \
	fi

# Convenience targets for synthesis
synthesize-force: MODEL ?= 
synthesize-force: FORCE_PARAM=--force
synthesize-force: synthesize

synthesize-retry: MODEL ?= 
synthesize-retry: RETRY_PARAM=--retry-failed
synthesize-retry: synthesize

# --- Assembly ---
assemble:
	@echo "Usage: make assemble [BITRATE=192k]"
	@if [ -z "$(BITRATE)" ]; then \
		echo "Using default bitrate 192k"; \
	else \
		python -m audiobook_ru assemble --bitrate "$(BITRATE)"; \
	fi

assemble-default: BITRATE=192k
assemble-default: assemble

# --- Cleanup ---
clean:
	rm -rf work/
	rm -rf output/
	rm -f manifest.json
	rm -f synthesis_report.json
	@echo "Cleaned work/ and output/ directories"

# --- Tests ---
test:
	pytest tests/ -v

test-quick:
	pytest tests/ -v -x --timeout=60

# --- Linting ---
lint:
	ruff check src/audiobook_ru/ tests/

format:
	ruff format src/audiobook_ru/ tests/

# --- Voice management ---
new-voice:
	@echo "Usage: make new-voice VOICE=en_US-lessac-medium"
	@if [ -z "$(VOICE)" ]; then \
		echo "Error: VOICE variable not set"; \
		echo "Example: make new-voice VOICE=en_US-lessac-medium"; \
	else \
		python -m piper.download_voices "$(VOICE)"; \
	fi