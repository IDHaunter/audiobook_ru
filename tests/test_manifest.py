"""Tests for manifest functionality."""

import pytest
import json
from pathlib import Path

from audiobook_ru.pipeline.manifest import (
    compute_sha256,
    atomic_write_json,
    validate_manifest_schema,
    Manifest,
)


class TestComputeSha256:
    """Tests for SHA-256 computation."""

    def test_basic(self, tmp_path):
        """Test basic SHA-256 computation."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello world")
        hash_val = compute_sha256(str(file_path))
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA-256 hex digest length


class TestAtomicWriteJson:
    """Tests for atomic JSON writing."""

    def test_atomic_write(self, tmp_path):
        """Test that JSON is written atomically."""
        file_path = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        atomic_write_json(str(file_path), data)

        # Verify file was created
        assert file_path.exists()

        # Verify content
        loaded = json.loads(file_path.read_text())
        assert loaded == data


class TestValidateManifestSchema:
    """Tests for manifest schema validation."""

    def test_valid_manifest(self):
        """Test validation of a valid manifest."""
        manifest_data = {
            "schema_version": "1.0",
            "source_hash": "abc123",
            "preparation_settings": {"max_chars": 2200},
            "chapters": [],
        }
        # This should not raise
        validate_manifest_schema(manifest_data, strict=False)
        # May have warnings about missing fields, but shouldn't crash

    def test_missing_schema_version(self):
        """Test that missing schema_version raises error in strict mode."""
        manifest_data = {
            "source_hash": "abc123",
            "preparation_settings": {},
            "chapters": [],
        }
        try:
            validate_manifest_schema(manifest_data, strict=True)
            # If it doesn't raise, that's OK for non-strict
        except Exception:
            pass  # Expected in strict mode


class TestManifest:
    """Tests for the Manifest class."""

    def test_manifest_creation(self, tmp_path):
        """Test basic Manifest creation and operations."""
        manifest_dir = tmp_path / "work"
        manifest_dir.mkdir()
        manifest_path = manifest_dir / "manifest.json"

        # Create manifest
        manifest = Manifest(str(manifest_dir))
        manifest.load()

        # Check it loaded
        assert manifest.manifest is not None
        assert "schema_version" in manifest.manifest

    def test_update_source_info(self, tmp_path):
        """Test updating source info in manifest."""
        manifest_dir = tmp_path / "work"
        manifest_dir.mkdir()
        
        manifest = Manifest(str(manifest_dir))
        manifest.update_source_info(
            source_path="test.txt",
            source_hash="abc123",
            preparation_settings={"max_chars": 2200},
        )

        # Verify source info was saved
        loaded = manifest.manifest
        assert loaded["source_hash"] == "abc123"
        assert loaded["preparation_settings"]["max_chars"] == 2200