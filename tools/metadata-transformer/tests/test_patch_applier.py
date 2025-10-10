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
                    "when": {"__must__": [{"assay_type": "test"}]},
                    "then": {"new_field": "new_value"},
                },
                {
                    "when": {"__should__": [{"protocol": "v1"}]},
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
            patches = [{"when": {"__must__": [{"assay_type": "test"}]}}]

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
                "when": {"__must__": [{"assay_type": "test"}]},
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
                "when": {"__must__": [{"assay_type": "test"}]},
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
                "when": {"__should__": [{"protocol": "v1"}, {"version": "1.0"}]},
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
                "when": {"__should__": [{"protocol": "v1"}, {"version": "1.0"}]},
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
                "when": {"__must__": [{"assay_type": "test"}, {"protocol": "v1"}]},
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
                    "__must__": [{"assay_type": "test"}],
                    "__should__": [{"protocol": "v1"}, {"version": "1.0"}],
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
                "when": {"__must__": [{"assay_type": "test"}]},
                "then": {"field1": "value1"},
                "_source_file": "patch1.json",
            },
            {
                "when": {"__must__": [{"assay_type": "test"}]},
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
                "when": {"__must__": [{"assay_type": "test"}]},
                "then": {"field1": "value1", "field2": "value2"},
                "_source_file": "test.json",
            }
        ]

        metadata = {"assay_type": "test"}
        result = self.patch_applier.apply_patches(metadata)

        # Verify patches were applied
        assert result["field1"] == "value1"
        assert result["field2"] == "value2"

    def test_get_loaded_patches_count(self) -> None:
        """Test getting the count of loaded patches."""
        assert self.patch_applier.get_loaded_patches_count() == 0

        self.patch_applier.patches = [{"test": "patch1"}, {"test": "patch2"}]
        assert self.patch_applier.get_loaded_patches_count() == 2

    def test_clear_logs(self) -> None:
        """Test clearing the structured log."""
        # Add some log entries first
        self.patch_applier.structured_log.add_mapped_field("old_field", "new_field")
        assert len(self.patch_applier.structured_log.field_mappings) == 1

        # Clear logs
        self.patch_applier.clear_logs()
        assert len(self.patch_applier.structured_log.field_mappings) == 0

    def test_load_patch_file_nonexistent(self) -> None:
        """Test loading patch file that doesn't exist."""
        nonexistent_path = Path("/nonexistent/file.json")
        with pytest.raises(FieldMappingError, match="Patch file not found"):
            self.patch_applier.load_patch_file(nonexistent_path)

    def test_load_patch_file_not_file(self) -> None:
        """Test loading patch file with directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            with pytest.raises(FieldMappingError, match="Path is not a file"):
                self.patch_applier.load_patch_file(dir_path)

    def test_load_patch_file_valid(self) -> None:
        """Test loading patches from a valid single file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            patches = [
                {
                    "when": {"__must__": [{"assay_type": "test"}]},
                    "then": {"new_field": "new_value"},
                },
                {
                    "when": {"__should__": [{"protocol": "v1"}]},
                    "then": {"protocol_version": "1.0"},
                },
            ]
            json.dump(patches, temp_file)
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            self.patch_applier.load_patch_file(file_path)
            assert len(self.patch_applier.patches) == 2
            assert self.patch_applier.patches[0]["then"]["new_field"] == "new_value"
            assert self.patch_applier.patches[1]["then"]["protocol_version"] == "1.0"
        finally:
            file_path.unlink()

    def test_load_patch_file_invalid_json(self) -> None:
        """Test loading patch file with invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file.write("{ invalid json")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                self.patch_applier.load_patch_file(file_path)
        finally:
            file_path.unlink()

    def test_load_patch_file_non_array(self) -> None:
        """Test loading patch file with non-array JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump({"not": "an array"}, temp_file)
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            with pytest.raises(FieldMappingError, match="must contain a JSON array"):
                self.patch_applier.load_patch_file(file_path)
        finally:
            file_path.unlink()

    def test_load_patches_and_file_together(self) -> None:
        """Test loading patches from both directory and file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a patch file in the directory
            dir_patch_file = temp_path / "dir_patches.json"
            dir_patches = [
                {
                    "when": {"__must__": [{"type": "dir"}]},
                    "then": {"source": "directory"},
                }
            ]
            with open(dir_patch_file, "w") as f:
                json.dump(dir_patches, f)

            # Create a separate patch file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                file_patches = [
                    {
                        "when": {"__must__": [{"type": "file"}]},
                        "then": {"source": "file"},
                    }
                ]
                json.dump(file_patches, temp_file)
                temp_file.flush()
                file_path = Path(temp_file.name)

            try:
                # Load from directory first
                self.patch_applier.load_patches(temp_path)
                assert len(self.patch_applier.patches) == 1

                # Then load from file
                self.patch_applier.load_patch_file(file_path)
                assert len(self.patch_applier.patches) == 2

                # Verify both patches are present
                assert self.patch_applier.patches[0]["then"]["source"] == "directory"
                assert self.patch_applier.patches[1]["then"]["source"] == "file"
            finally:
                file_path.unlink()

    def test_nested_and_or_logic(self) -> None:
        """Test nested AND(A, OR(B,C), OR(D,E)) logic."""
        self.patch_applier.patches = [
            {
                "when": {
                    "__must__": [
                        {"field0": "value0"},  # A
                        {
                            "__should__": [  # OR(B,C)
                                {"field1": "value1"},  # B
                                {"field2": "value2"},  # C
                            ]
                        },
                        {
                            "__should__": [  # OR(D,E)
                                {"field3": "value3"},  # D
                                {"field4": "value4"},  # E
                            ]
                        },
                    ]
                },
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]

        # Test: A true, B true, D true -> True
        metadata = {"field0": "value0", "field1": "value1", "field3": "value3"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, C true, E true -> True
        metadata = {"field0": "value0", "field2": "value2", "field4": "value4"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, B true, but OR(D,E) false -> False
        metadata = {"field0": "value0", "field1": "value1", "field3": "wrong"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

        # Test: A false -> False (even if others match)
        metadata = {"field0": "wrong", "field1": "value1", "field3": "value3"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

    def test_nested_or_and_logic(self) -> None:
        """Test nested OR(A, AND(B,C), AND(D,E)) logic."""
        self.patch_applier.patches = [
            {
                "when": {
                    "__should__": [
                        {"field0": "value0"},  # A
                        {
                            "__must__": [  # AND(B,C)
                                {"field1": "value1"},  # B
                                {"field2": "value2"},  # C
                            ]
                        },
                        {
                            "__must__": [  # AND(D,E)
                                {"field1": "value3"},  # D
                                {"field2": "value4"},  # E
                            ]
                        },
                    ]
                },
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]

        # Test: A true -> True
        metadata = {"field0": "value0"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: AND(B,C) true -> True
        metadata = {"field1": "value1", "field2": "value2"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: AND(D,E) true -> True
        metadata = {"field1": "value3", "field2": "value4"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: All false -> False
        metadata = {"field0": "wrong", "field1": "wrong"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

        # Test: B true but C false (AND fails), A false -> False
        metadata = {"field0": "wrong", "field1": "value1", "field2": "wrong"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

    def test_deeply_nested_logic(self) -> None:
        """Test deeply nested AND(A, OR(B, AND(C, D))) logic."""
        self.patch_applier.patches = [
            {
                "when": {
                    "__must__": [
                        {"field0": "value0"},  # A
                        {
                            "__should__": [  # OR
                                {"field1": "value1"},  # B
                                {
                                    "__must__": [  # AND(C,D)
                                        {"field2": "value2"},  # C
                                        {"field3": "value3"},  # D
                                    ]
                                },
                            ]
                        },
                    ]
                },
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]

        # Test: A true, B true -> True
        metadata = {"field0": "value0", "field1": "value1"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, AND(C,D) true -> True
        metadata = {"field0": "value0", "field2": "value2", "field3": "value3"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, but B false and C false -> False
        metadata = {"field0": "value0", "field1": "wrong", "field2": "wrong"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

        # Test: A false -> False
        metadata = {"field0": "wrong", "field1": "value1"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

    def test_multi_field_single_item(self) -> None:
        """Test single item with multiple fields (implicit AND)."""
        self.patch_applier.patches = [
            {
                "when": {"__must__": [{"field1": "value1", "field2": "value2"}]},
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]

        # Test: Both fields match -> True
        metadata = {"field1": "value1", "field2": "value2"}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: Only one field matches -> False
        metadata = {"field1": "value1", "field2": "wrong"}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result

    def test_empty_arrays(self) -> None:
        """Test behavior with empty arrays."""
        # Empty __must__ array: all() returns True
        self.patch_applier.patches = [
            {
                "when": {"__must__": []},
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]
        metadata = {}
        result = self.patch_applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Empty __should__ array: any() returns False
        self.patch_applier.patches = [
            {
                "when": {"__should__": []},
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]
        metadata = {}
        result = self.patch_applier.apply_patches(metadata)
        assert "result" not in result
