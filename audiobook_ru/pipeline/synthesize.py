"""Resumable synthesis and report generation."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import manifest as manifest_mod
from . import tts as tts_mod


def run_synthesis(work_dir, model_path, force=False, retry_failed=False):
    """Run synthesis for all missing/invalid segments."""
    print("Synthesis placeholder - implement full logic later")
    return 0