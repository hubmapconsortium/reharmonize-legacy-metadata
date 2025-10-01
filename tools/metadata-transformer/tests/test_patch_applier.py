"""Tests for PatchApplier class."""

import json
import tempfile
from pathlib import Path

import pytest

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.patch_applier import PatchApplier
from metadata_transformer.processing_log import StructuredProcessingLog


class TestPatchApplier:
    """Test cases for PatchApplier class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.patch_applier = PatchApplier()

    def test_init(self) -> None:
        """Test PatchApplier initialization."""
        assert len(self.patch_applier.patches) == 0
        assert isinstance(self.patch_applier.structured_log, StructuredProcessingLog)

    def test_load_patches_nonexistent_directory(self) -> None:
        """Test loading patches from nonexistent directory."""
        nonexistent_path = Path("/nonexistent/path")
        with pytest.raises(FieldMappingError, match="Patches directory not found"):
            self.patch_applier.load_patches(nonexistent_path)

    def test_load_patches_not_directory(self) -> None:
        """Test loading patches from a file path instead of directory."""
        with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
            file_path = Path(temp_file.name)
            with pytest.raises(FieldMappingError, match="Path is not a directory"):
                self.patch_applier.load_patches(file_path)

    def test_load_patches_empty_directory(self) -> None:
        """Test loading patches from directory with no JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Should not raise an error, just continue without patches
            self.patch_applier.load_patches(temp_path)
            assert len(self.patch_applier.patches) == 0

    def test_load_patches_valid_file(self) -> None:
        """Test loading patches from valid patch file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "test_patches.json"

            patches = [
                {
                    "when": {"must": {"assay_type": "test"}},
                    "then": {"new_field": "new_value"},
                },
                {
                    "when": {"should": {"protocol": "v1"}},
                    "then": {"protocol_version": "1.0"},
                },
            ]

            with open(patch_file, "w") as f:
                json.dump(patches, f)

            self.patch_applier.load_patches(temp_path)
            assert len(self.patch_applier.patches) == 2

    def test_load_patches_invalid_json(self) -> None:
        """Test loading patches with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "invalid.json"

            with open(patch_file, "w") as f:
                f.write("{ invalid json")

            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                self.patch_applier.load_patches(temp_path)

    def test_load_patches_non_array(self) -> None:
        """Test loading patches with non-array JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "non_array.json"

            with open(patch_file, "w") as f:
                json.dump({"not": "an array"}, f)

            with pytest.raises(FieldMappingError, match="must contain a JSON array"):
                self.patch_applier.load_patches(temp_path)

    def test_load_patches_invalid_patch_structure(self) -> None:
        """Test loading patches with invalid patch structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "invalid_structure.json"

            # Missing "then" key
            patches = [{"when": {"must": {"assay_type": "test"}}}]

            with open(patch_file, "w") as f:
                json.dump(patches, f)

            with pytest.raises(
                FieldMappingError, match="must have 'when' and 'then' keys"
            ):
                self.patch_applier.load_patches(temp_path)

    def test_apply_patches_no_patches(self) -> None:
        """Test applying patches when no patches are loaded."""
        metadata = {"field1": "value1", "field2": "value2"}
        result = self.patch_applier.apply_patches(metadata)
        assert result == metadata

    def test_apply_patches_must_condition_match(self) -> None:
        """Test applying patches with matching 'must' conditions."""
        self.patch_applier.patches = [
            {
                "when": {"must": {"assay_type": "test"}},
                "then": {"new_field": "new_value"},
                "_source_file": "test.json",
            }
        ]

        metadata = {"assay_type": "test", "existing_field": "existing_value"}
        result = self.patch_applier.apply_patches(metadata)

        assert result["assay_type"] == "test"
        assert result["existing_field"] == "existing_value"
        assert result["new_field"] == "new_value"

    def test_apply_patches_must_condition_no_match(self) -> None:
        """Test applying patches with non-matching 'must' conditions."""
        self.patch_applier.patches = [
            {
                "when": {"must": {"assay_type": "test"}},
                "then": {"new_field": "new_value"},
                "_source_file": "test.json",
            }
        ]

        metadata = {"assay_type": "different", "existing_field": "existing_value"}
        result = self.patch_applier.apply_patches(metadata)

        # Should be unchanged
        assert result == metadata

    def test_apply_patches_should_condition_match(self) -> None:
        """Test applying patches with matching 'should' conditions."""
        self.patch_applier.patches = [
            {
                "when": {"should": {"protocol": "v1", "version": "1.0"}},
                "then": {"standardized_protocol": "version_1"},
                "_source_file": "test.json",
            }
        ]

        metadata = {"protocol": "v1", "other_field": "value"}
        result = self.patch_applier.apply_patches(metadata)

        assert result["protocol"] == "v1"
        assert result["other_field"] == "value"
        assert result["standardized_protocol"] == "version_1"

    def test_apply_patches_should_condition_no_match(self) -> None:
        """Test applying patches with non-matching 'should' conditions."""
        self.patch_applier.patches = [
            {
                "when": {"should": {"protocol": "v1", "version": "1.0"}},
                "then": {"standardized_protocol": "version_1"},
                "_source_file": "test.json",
            }
        ]

        metadata = {"protocol": "v2", "version": "2.0", "other_field": "value"}
        result = self.patch_applier.apply_patches(metadata)

        # Should be unchanged
        assert result == metadata

    def test_apply_patches_multiple_must_conditions(self) -> None:
        """Test applying patches with multiple 'must' conditions (AND logic)."""
        self.patch_applier.patches = [
            {
                "when": {"must": {"assay_type": "test", "protocol": "v1"}},
                "then": {"combined_field": "test_v1"},
                "_source_file": "test.json",
            }
        ]

        # Both conditions match
        metadata = {"assay_type": "test", "protocol": "v1", "other": "value"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["combined_field"] == "test_v1"

        # Only one condition matches
        metadata = {"assay_type": "test", "protocol": "v2", "other": "value"}
        result = self.patch_applier.apply_patches(metadata)
        assert "combined_field" not in result

    def test_apply_patches_mixed_conditions(self) -> None:
        """Test applying patches with both 'must' and 'should' conditions."""
        self.patch_applier.patches = [
            {
                "when": {
                    "must": {"assay_type": "test"},
                    "should": {"protocol": "v1", "version": "1.0"},
                },
                "then": {"mixed_condition": "applied"},
                "_source_file": "test.json",
            }
        ]

        # Must condition matches, should condition matches
        metadata = {"assay_type": "test", "protocol": "v1", "other": "value"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["mixed_condition"] == "applied"

        # Must condition matches, should condition doesn't match
        metadata = {
            "assay_type": "test",
            "protocol": "v2",
            "version": "2.0",
            "other": "value",
        }
        result = self.patch_applier.apply_patches(metadata)
        assert "mixed_condition" not in result

    def test_apply_patches_multiple_patches(self) -> None:
        """Test applying multiple patches in sequence."""
        self.patch_applier.patches = [
            {
                "when": {"must": {"assay_type": "test"}},
                "then": {"field1": "value1"},
                "_source_file": "patch1.json",
            },
            {
                "when": {"must": {"assay_type": "test"}},
                "then": {"field2": "value2", "field1": "overwritten"},
                "_source_file": "patch2.json",
            },
        ]

        metadata = {"assay_type": "test"}
        result = self.patch_applier.apply_patches(metadata)

        assert result["assay_type"] == "test"
        assert result["field1"] == "overwritten"  # Second patch overwrote first
        assert result["field2"] == "value2"

    def test_apply_patches_logs_applications(self) -> None:
        """Test that patch applications are logged correctly."""
        self.patch_applier.patches = [
            {
                "when": {"must": {"assay_type": "test"}},
                "then": {"field1": "value1", "field2": "value2"},
                "_source_file": "test.json",
            }
        ]

        metadata = {"assay_type": "test"}
        self.patch_applier.apply_patches(metadata)

        log = self.patch_applier.get_structured_log()
        assert len(log.metadata_patches) == 2  # Two fields were patched

        patch_entries = log.metadata_patches
        fields = [entry.field for entry in patch_entries]
        assert "field1" in fields
        assert "field2" in fields

        # Verify conditions are logged but source_file is not
        for entry in patch_entries:
            assert entry.conditions == {"must": {"assay_type": "test"}}
            assert not hasattr(entry, "source_file")

    def test_get_loaded_patches_count(self) -> None:
        """Test getting the count of loaded patches."""
        assert self.patch_applier.get_loaded_patches_count() == 0

        self.patch_applier.patches = [{"test": "patch1"}, {"test": "patch2"}]
        assert self.patch_applier.get_loaded_patches_count() == 2

    def test_clear_logs(self) -> None:
        """Test clearing the structured log."""
        # Add some log entries first
        self.patch_applier.structured_log.add_applied_patch(
            "test_field", "test_value", {}
        )
        assert len(self.patch_applier.structured_log.metadata_patches) == 1

        # Clear logs
        self.patch_applier.clear_logs()
        assert len(self.patch_applier.structured_log.metadata_patches) == 0
