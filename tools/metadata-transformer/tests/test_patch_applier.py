"""Tests for Patches and PatchApplier classes."""

import json
import tempfile
from pathlib import Path

import pytest

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.patch_applier import Patches, PatchApplier
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.processing_log_provider import ProcessingLogProvider


class TestPatches:
    """Test cases for Patches class."""

    def test_init(self) -> None:
        """Test Patches initialization."""
        patches = Patches()
        assert patches.get_loaded_patches_count() == 0

    def test_load_patches_nonexistent_directory(self) -> None:
        """Test loading patches from nonexistent directory."""
        patches = Patches()
        nonexistent_path = Path("/nonexistent/path")
        with pytest.raises(FieldMappingError, match="Patches directory not found"):
            patches.load_patches(nonexistent_path)

    def test_load_patches_not_directory(self) -> None:
        """Test loading patches from a file path instead of directory."""
        patches = Patches()
        with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
            file_path = Path(temp_file.name)
            with pytest.raises(FieldMappingError, match="Path is not a directory"):
                patches.load_patches(file_path)

    def test_load_patches_empty_directory(self) -> None:
        """Test loading patches from directory with no JSON files."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Should not raise an error, just continue without patches
            patches.load_patches(temp_path)
            assert patches.get_loaded_patches_count() == 0

    def test_load_patches_valid_file(self) -> None:
        """Test loading patches from valid patch file."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "test_patches.json"

            patches_data = [
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
                json.dump(patches_data, f)

            patches.load_patches(temp_path)
            assert patches.get_loaded_patches_count() == 2

    def test_load_patches_invalid_json(self) -> None:
        """Test loading patches with invalid JSON."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "invalid.json"

            with open(patch_file, "w") as f:
                f.write("{ invalid json")

            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                patches.load_patches(temp_path)

    def test_load_patches_non_array(self) -> None:
        """Test loading patches with non-array JSON."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "non_array.json"

            with open(patch_file, "w") as f:
                json.dump({"not": "an array"}, f)

            with pytest.raises(FieldMappingError, match="must contain a JSON array"):
                patches.load_patches(temp_path)

    def test_load_patches_invalid_patch_structure(self) -> None:
        """Test loading patches with invalid patch structure."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            patch_file = temp_path / "invalid_structure.json"

            # Missing "then" key
            patches_data = [{"when": {"__must__": [{"assay_type": "test"}]}}]

            with open(patch_file, "w") as f:
                json.dump(patches_data, f)

            with pytest.raises(
                FieldMappingError, match="must have 'when' and 'then' keys"
            ):
                patches.load_patches(temp_path)

    def test_load_patch_file_nonexistent(self) -> None:
        """Test loading patch file that doesn't exist."""
        patches = Patches()
        nonexistent_path = Path("/nonexistent/file.json")
        with pytest.raises(FieldMappingError, match="Patch file not found"):
            patches.load_patch_file(nonexistent_path)

    def test_load_patch_file_not_file(self) -> None:
        """Test loading patch file with directory path."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            with pytest.raises(FieldMappingError, match="Path is not a file"):
                patches.load_patch_file(dir_path)

    def test_load_patch_file_valid(self) -> None:
        """Test loading patches from a valid single file."""
        patches = Patches()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            patches_data = [
                {
                    "when": {"__must__": [{"assay_type": "test"}]},
                    "then": {"new_field": "new_value"},
                },
                {
                    "when": {"__should__": [{"protocol": "v1"}]},
                    "then": {"protocol_version": "1.0"},
                },
            ]
            json.dump(patches_data, temp_file)
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            patches.load_patch_file(file_path)
            assert patches.get_loaded_patches_count() == 2
            all_patches = patches.get_all_patches()
            assert all_patches[0]["then"]["new_field"] == "new_value"
            assert all_patches[1]["then"]["protocol_version"] == "1.0"
        finally:
            file_path.unlink()

    def test_load_patch_file_invalid_json(self) -> None:
        """Test loading patch file with invalid JSON."""
        patches = Patches()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file.write("{ invalid json")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                patches.load_patch_file(file_path)
        finally:
            file_path.unlink()

    def test_load_patch_file_non_array(self) -> None:
        """Test loading patch file with non-array JSON."""
        patches = Patches()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump({"not": "an array"}, temp_file)
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            with pytest.raises(FieldMappingError, match="must contain a JSON array"):
                patches.load_patch_file(file_path)
        finally:
            file_path.unlink()

    def test_load_patches_and_file_together(self) -> None:
        """Test loading patches from both directory and file."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a patch file in the directory
            dir_patch_file = temp_path / "dir_patches.json"
            dir_patches_data = [
                {
                    "when": {"__must__": [{"type": "dir"}]},
                    "then": {"source": "directory"},
                }
            ]
            with open(dir_patch_file, "w") as f:
                json.dump(dir_patches_data, f)

            # Create a separate patch file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                file_patches_data = [
                    {
                        "when": {"__must__": [{"type": "file"}]},
                        "then": {"source": "file"},
                    }
                ]
                json.dump(file_patches_data, temp_file)
                temp_file.flush()
                file_path = Path(temp_file.name)

            try:
                # Load from directory first
                patches.load_patches(temp_path)
                assert patches.get_loaded_patches_count() == 1

                # Then load from file
                patches.load_patch_file(file_path)
                assert patches.get_loaded_patches_count() == 2

                # Verify both patches are present
                all_patches = patches.get_all_patches()
                assert all_patches[0]["then"]["source"] == "directory"
                assert all_patches[1]["then"]["source"] == "file"
            finally:
                file_path.unlink()

    def test_get_applier(self) -> None:
        """Test get_applier creates PatchApplier with correct data."""
        patches = Patches()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            patch_file = temp_path / "test.json"
            patches_data = [
                {
                    "when": {"__must__": [{"field1": "value1"}]},
                    "then": {"field2": "value2"},
                }
            ]
            with open(patch_file, "w") as f:
                json.dump(patches_data, f)

            patches.load_patches(temp_path)

            log_provider = ProcessingLogProvider()
            applier = patches.get_applier(log_provider)

            assert isinstance(applier, PatchApplier)
            assert applier.get_loaded_patches_count() == 1
            assert isinstance(applier.get_processing_log(), StructuredProcessingLog)


class TestPatchApplier:
    """Test cases for PatchApplier class."""

    def test_init_default(self) -> None:
        """Test PatchApplier initialization with empty patches."""
        applier = PatchApplier([], ProcessingLogProvider())
        assert applier.get_loaded_patches_count() == 0
        assert isinstance(applier.get_processing_log(), StructuredProcessingLog)

    def test_init_with_patches(self) -> None:
        """Test PatchApplier initialization with patches."""
        patches_list = [
            {
                "when": {"__must__": [{"field1": "value1"}]},
                "then": {"field2": "value2"},
                "_source_file": "test.json",
            }
        ]
        log_provider = ProcessingLogProvider()

        applier = PatchApplier(patches_list, log_provider)

        assert applier.get_loaded_patches_count() == 1
        assert isinstance(applier.get_processing_log(), StructuredProcessingLog)

    def test_apply_patches_no_patches(self) -> None:
        """Test applying patches when no patches are loaded."""
        applier = PatchApplier([], ProcessingLogProvider())
        metadata = {"field1": "value1", "field2": "value2"}
        result = applier.apply_patches(metadata)
        assert result == metadata

    def test_apply_patches_must_condition_match(self) -> None:
        """Test applying patches with matching 'must' conditions."""
        patches_list = [
            {
                "when": {"__must__": [{"assay_type": "test"}]},
                "then": {"new_field": "new_value"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        metadata = {"assay_type": "test", "existing_field": "existing_value"}
        result = applier.apply_patches(metadata)

        assert result["assay_type"] == "test"
        assert result["existing_field"] == "existing_value"
        assert result["new_field"] == "new_value"

    def test_apply_patches_must_condition_no_match(self) -> None:
        """Test applying patches with non-matching 'must' conditions."""
        patches_list = [
            {
                "when": {"__must__": [{"assay_type": "test"}]},
                "then": {"new_field": "new_value"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        metadata = {"assay_type": "different", "existing_field": "existing_value"}
        result = applier.apply_patches(metadata)

        # Should be unchanged
        assert result == metadata

    def test_apply_patches_should_condition_match(self) -> None:
        """Test applying patches with matching 'should' conditions."""
        patches_list = [
            {
                "when": {"__should__": [{"protocol": "v1"}, {"version": "1.0"}]},
                "then": {"standardized_protocol": "version_1"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        metadata = {"protocol": "v1", "other_field": "value"}
        result = applier.apply_patches(metadata)

        assert result["protocol"] == "v1"
        assert result["other_field"] == "value"
        assert result["standardized_protocol"] == "version_1"

    def test_apply_patches_should_condition_no_match(self) -> None:
        """Test applying patches with non-matching 'should' conditions."""
        patches_list = [
            {
                "when": {"__should__": [{"protocol": "v1"}, {"version": "1.0"}]},
                "then": {"standardized_protocol": "version_1"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        metadata = {"protocol": "v2", "version": "2.0", "other_field": "value"}
        result = applier.apply_patches(metadata)

        # Should be unchanged
        assert result == metadata

    def test_apply_patches_multiple_must_conditions(self) -> None:
        """Test applying patches with multiple 'must' conditions (AND logic)."""
        patches_list = [
            {
                "when": {"__must__": [{"assay_type": "test"}, {"protocol": "v1"}]},
                "then": {"combined_field": "test_v1"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        # Both conditions match
        metadata = {"assay_type": "test", "protocol": "v1", "other": "value"}
        result = applier.apply_patches(metadata)
        assert result["combined_field"] == "test_v1"

        # Only one condition matches
        metadata = {"assay_type": "test", "protocol": "v2", "other": "value"}
        result = applier.apply_patches(metadata)
        assert "combined_field" not in result

    def test_apply_patches_mixed_conditions(self) -> None:
        """Test applying patches with both 'must' and 'should' conditions."""
        patches_list = [
            {
                "when": {
                    "__must__": [{"assay_type": "test"}],
                    "__should__": [{"protocol": "v1"}, {"version": "1.0"}],
                },
                "then": {"mixed_condition": "applied"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        # Must condition matches, should condition matches
        metadata = {"assay_type": "test", "protocol": "v1", "other": "value"}
        result = applier.apply_patches(metadata)
        assert result["mixed_condition"] == "applied"

        # Must condition matches, should condition doesn't match
        metadata = {
            "assay_type": "test",
            "protocol": "v2",
            "version": "2.0",
            "other": "value",
        }
        result = applier.apply_patches(metadata)
        assert "mixed_condition" not in result

    def test_apply_patches_multiple_patches(self) -> None:
        """Test applying multiple patches in sequence."""
        patches_list = [
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
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        metadata = {"assay_type": "test"}
        result = applier.apply_patches(metadata)

        assert result["assay_type"] == "test"
        assert result["field1"] == "overwritten"  # Second patch overwrote first
        assert result["field2"] == "value2"

    def test_nested_and_or_logic(self) -> None:
        """Test nested AND(A, OR(B,C), OR(D,E)) logic."""
        patches_list = [
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
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        # Test: A true, B true, D true -> True
        metadata = {"field0": "value0", "field1": "value1", "field3": "value3"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, C true, E true -> True
        metadata = {"field0": "value0", "field2": "value2", "field4": "value4"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, B true, but OR(D,E) false -> False
        metadata = {"field0": "value0", "field1": "value1", "field3": "wrong"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

        # Test: A false -> False (even if others match)
        metadata = {"field0": "wrong", "field1": "value1", "field3": "value3"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

    def test_nested_or_and_logic(self) -> None:
        """Test nested OR(A, AND(B,C), AND(D,E)) logic."""
        patches_list = [
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
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        # Test: A true -> True
        metadata = {"field0": "value0"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: AND(B,C) true -> True
        metadata = {"field1": "value1", "field2": "value2"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: AND(D,E) true -> True
        metadata = {"field1": "value3", "field2": "value4"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: All false -> False
        metadata = {"field0": "wrong", "field1": "wrong"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

        # Test: B true but C false (AND fails), A false -> False
        metadata = {"field0": "wrong", "field1": "value1", "field2": "wrong"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

    def test_deeply_nested_logic(self) -> None:
        """Test deeply nested AND(A, OR(B, AND(C, D))) logic."""
        patches_list = [
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
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        # Test: A true, B true -> True
        metadata = {"field0": "value0", "field1": "value1"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, AND(C,D) true -> True
        metadata = {"field0": "value0", "field2": "value2", "field3": "value3"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: A true, but B false and C false -> False
        metadata = {"field0": "value0", "field1": "wrong", "field2": "wrong"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

        # Test: A false -> False
        metadata = {"field0": "wrong", "field1": "value1"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

    def test_multi_field_single_item(self) -> None:
        """Test single item with multiple fields (implicit AND)."""
        patches_list = [
            {
                "when": {"__must__": [{"field1": "value1", "field2": "value2"}]},
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())

        # Test: Both fields match -> True
        metadata = {"field1": "value1", "field2": "value2"}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Test: Only one field matches -> False
        metadata = {"field1": "value1", "field2": "wrong"}
        result = applier.apply_patches(metadata)
        assert "result" not in result

    def test_empty_arrays(self) -> None:
        """Test behavior with empty arrays."""
        # Empty __must__ array: all() returns True
        patches_list = [
            {
                "when": {"__must__": []},
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())
        metadata = {}
        result = applier.apply_patches(metadata)
        assert result["result"] == "applied"

        # Empty __should__ array: any() returns False
        patches_list = [
            {
                "when": {"__should__": []},
                "then": {"result": "applied"},
                "_source_file": "test.json",
            }
        ]
        applier = PatchApplier(patches_list, ProcessingLogProvider())
        metadata = {}
        result = applier.apply_patches(metadata)
        assert "result" not in result
