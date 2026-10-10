"""Versioned manifest and safe path handling for audiobook_ru."""

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

MANIFEST_SCHEMA_VERSION = "1.0"
WORK_DIR = "work"
MANIFEST_FILE = "manifest.json"
SEGMENTS_DIR = "segments"
ERROR_CATEGORY_NONE = "none"
ERROR_CATEGORY_TEXT = "text"
ERROR_CATEGORY_SYNTHESIS = "synthesis"
ERROR_CATEGORY_FILE = "file"


class ManifestError(Exception):
    """Raised when manifest operations fail."""


class ManifestValidationError(ManifestError):
    """Raised when manifest validation fails."""


def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def atomic_write_json(file_path: str, data: dict) -> None:
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        shutil.move(str(temp_file), str(target))
    except Exception:
        if Path(temp_file).exists():
            Path(temp_file).unlink()
        raise


def validate_manifest_schema(manifest_data: dict, strict: bool = True) -> list[str]:
    warnings = []
    if "schema_version" not in manifest_data:
        if strict:
            raise ManifestValidationError("Missing required field: schema_version")
        warnings.append("Missing schema_version field")
    else:
        if manifest_data["schema_version"] != MANIFEST_SCHEMA_VERSION:
            warnings.append(
                f"Schema version mismatch: expected {MANIFEST_SCHEMA_VERSION}, got {manifest_data['schema_version']}"
            )
    required_top_level = ["source_hash", "preparation_settings", "chapters"]
    for field in required_top_level:
        if field not in manifest_data:
            if strict:
                raise ManifestValidationError(f"Missing required field: {field}")
            warnings.append(f"Missing top-level field: {field}")
    if "chapters" in manifest_data:
        chapters = manifest_data["chapters"]
        if not isinstance(chapters, list):
            warnings.append("chapters should be a list")
        else:
            for i, chapter in enumerate(chapters):
                if not isinstance(chapter, dict):
                    warnings.append(f"Chapter {i} is not a dict")
                    continue
                chapter_required = ["index", "title", "segment_ids"]
                for req_field in chapter_required:
                    if req_field not in chapter:
                        warnings.append(f"Chapter {i} missing required field: {req_field}")
                if "segment_ids" in chapter:
                    seg_ids = chapter["segment_ids"]
                    if not isinstance(seg_ids, list):
                        warnings.append(f"Chapter {i} segment_ids should be a list")
    if "preparation_settings" in manifest_data:
        settings = manifest_data["preparation_settings"]
        if not isinstance(settings, dict):
            warnings.append("preparation_settings should be a dict")
        else:
            known_settings = {"max_chars", "normalizer_version"}
            for key in settings:
                if key not in known_settings:
                    warnings.append(f"Unknown preparation setting: {key}")
    return warnings


class Manifest:
    """Versioned manifest management for audiobook_ru."""

    def __init__(self, work_dir: str):
        """Initialize manifest."""
        self.work_dir = Path(work_dir).resolve()
        self.manifest_path = self.work_dir / "manifest.json"
        self.manifest: Optional[dict] = None

    def load(self) -> dict:
        """Load manifest from disk."""
        if not self.manifest_path.exists():
            self.manifest = self._empty_manifest()
            self.save()
            return self.manifest
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise ManifestValidationError(f"Failed to load manifest: {e}") from e
        return self.manifest

    def _empty_manifest(self) -> dict:
        """Create an empty base manifest structure."""
        return {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "source_hash": "",
            "source_file": "",
            "preparation_settings": {},
            "chapters": [],
            "segments": [],
        }

    def save(self) -> None:
        """Save manifest to disk atomically."""
        if self.manifest is None:
            raise ManifestError("No manifest to save; call load() first")
        atomic_write_json(str(self.manifest_path), self.manifest)

    def update_source_info(
        self, source_path: str, source_hash: str, preparation_settings: dict
    ) -> None:
        """Update source file information in manifest."""
        if self.manifest is None:
            self.manifest = self._empty_manifest()
        self.manifest["source_hash"] = source_hash
        self.manifest["source_file"] = Path(source_path).name
        self.manifest["preparation_settings"] = preparation_settings
        self.save()

    def add_chapter(self, index: int, title: str, segment_ids: list[str]) -> None:
        """Add a chapter to the manifest."""
        if self.manifest is None:
            self.manifest = self._empty_manifest()
        self.manifest["chapters"].append(
            {"index": index, "title": title, "segment_ids": segment_ids}
        )
        self.save()

    def get_segment_path(self, segment_id: str) -> Path:
        """Get the file path for a segment's text file."""
        segment_file = self.work_dir / "segments" / f"{segment_id}.txt"
        resolved = segment_file.resolve()
        work_resolved = self.work_dir.resolve()
        if not str(resolved).startswith(str(work_resolved) + "/") and str(
            resolved
        ) != str(work_resolved):
            raise ValueError(
                f"Segment path escapes work directory: {segment_file}"
            )
        return segment_file

    def validate_segment_text(self, segment_id: str, expected_text: str) -> bool:
        """Validate that segment text file matches expected content."""
        segment_path = self.get_segment_path(segment_id)
        if not segment_path.exists():
            return False
        try:
            with open(segment_path, "r", encoding="utf-8") as f:
                actual_text = f.read()
            return actual_text == expected_text
        except (OSError, UnicodeDecodeError):
            return False

    def write_segment_text(self, segment_id: str, text: str) -> None:
        """Write segment text to file."""
        segment_path = self.get_segment_path(segment_id)
        segment_path.parent.mkdir(parents=True, exist_ok=True)
        with open(segment_path, "w", encoding="utf-8") as f:
            f.write(text)

    @staticmethod
    def default_settings() -> dict:
        """Return default preparation settings."""
        return {"max_chars": 2200, "normalizer_version": "1.0.0"}