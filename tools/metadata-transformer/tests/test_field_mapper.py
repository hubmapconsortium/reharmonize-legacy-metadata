"""
Tests for the field_mapper module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.field_mapper import FieldMapper
from metadata_transformer.processing_log import StructuredProcessingLog


class TestFieldMapper:
    """Test cases for FieldMapper class."""

    def test_init(self) -> None:
        """Test FieldMapper initialization."""
        mapper = FieldMapper()
        assert isinstance(mapper.field_mappings, dict)
        assert len(mapper.field_mappings) == 0
        assert isinstance(mapper.structured_log, StructuredProcessingLog)
        assert len(mapper.structured_log.field_mappings) == 0

    def test_load_field_mappings_nonexistent_directory(self) -> None:
        """Test loading from non-existent directory raises error."""
        mapper = FieldMapper()
        nonexistent_dir = Path("/nonexistent/directory")

        with pytest.raises(
            FieldMappingError, match="Field mapping directory not found"
        ):
            mapper.load_field_mappings(nonexistent_dir)

    def test_load_field_mappings_not_directory(self) -> None:
        """Test loading from file instead of directory raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_file = temp_path / "not_a_dir.txt"
            temp_file.write_text("test")

            with pytest.raises(FieldMappingError, match="Path is not a directory"):
                mapper.load_field_mappings(temp_file)

    def test_load_field_mappings_no_json_files(self) -> None:
        """Test loading from directory with no JSON files raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create a non-JSON file
            (temp_path / "not_json.txt").write_text("test")

            with pytest.raises(FieldMappingError, match="No JSON files found"):
                mapper.load_field_mappings(temp_path)

    def test_load_field_mappings_single_file(self) -> None:
        """Test loading field mappings from single file."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test mapping file
            mapping_file = temp_path / "test_mapping.json"
            mapping_data = {
                "legacy_field1": "target_field1",
                "legacy_field2": "target_field2",
                "legacy_field3": None,
            }
            mapping_file.write_text(json.dumps(mapping_data))

            mapper.load_field_mappings(temp_path)

            assert len(mapper.field_mappings) == 3
            assert mapper.field_mappings["legacy_field1"] == "target_field1"
            assert mapper.field_mappings["legacy_field2"] == "target_field2"
            assert mapper.field_mappings["legacy_field3"] is None

            # Check processing log - file loading no longer creates log entries
            assert len(mapper.structured_log.field_mappings) == 0

    def test_load_field_mappings_multiple_files_no_conflicts(self) -> None:
        """Test loading field mappings from multiple files without conflicts."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create first mapping file
            mapping1 = temp_path / "mapping1.json"
            data1 = {"field_a": "target_a", "field_b": "target_b"}
            mapping1.write_text(json.dumps(data1))

            # Create second mapping file
            mapping2 = temp_path / "mapping2.json"
            data2 = {"field_c": "target_c", "field_d": None}
            mapping2.write_text(json.dumps(data2))

            mapper.load_field_mappings(temp_path)

            assert len(mapper.field_mappings) == 4
            assert mapper.field_mappings["field_a"] == "target_a"
            assert mapper.field_mappings["field_b"] == "target_b"
            assert mapper.field_mappings["field_c"] == "target_c"
            assert mapper.field_mappings["field_d"] is None

    def test_load_field_mappings_with_conflicts(self) -> None:
        """Test loading field mappings with conflicts logs and skips new mappings."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create first mapping file
            mapping1 = temp_path / "mapping1.json"
            data1 = {"field_a": "target_a", "field_b": "target_b"}
            mapping1.write_text(json.dumps(data1))

            # Create second mapping file with conflict
            mapping2 = temp_path / "mapping2.json"
            data2 = {"field_a": "different_target", "field_c": "target_c"}
            mapping2.write_text(json.dumps(data2))

            mapper.load_field_mappings(temp_path)

            # Should keep original mapping
            assert mapper.field_mappings["field_a"] == "target_a"
            assert mapper.field_mappings["field_b"] == "target_b"
            assert mapper.field_mappings["field_c"] == "target_c"

            # Check conflict handling - conflicts no longer logged during file loading
            # Conflicts are handled by keeping existing mapping and ignoring new one
            assert len(mapper.structured_log.field_mappings) == 0

    def test_load_field_mappings_invalid_json(self) -> None:
        """Test loading invalid JSON file raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid JSON file
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                mapper.load_field_mappings(temp_path)

    def test_load_field_mappings_non_dict_json(self) -> None:
        """Test loading JSON file that's not a dictionary raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create JSON array instead of object
            json_array = temp_path / "array.json"
            json_array.write_text('["not", "a", "dict"]')

            with pytest.raises(FieldMappingError, match="must contain a JSON object"):
                mapper.load_field_mappings(temp_path)

    def test_map_field(self) -> None:
        """Test field mapping functionality."""
        mapper = FieldMapper()
        mapper.field_mappings = {
            "legacy_field": "target_field",
            "another_field": None,
            "third_field": "mapped_field",
        }

        assert mapper.map_field("legacy_field") == "target_field"
        assert mapper.map_field("another_field") is None
        assert mapper.map_field("third_field") == "mapped_field"
        assert mapper.map_field("nonexistent_field") is None

    def test_get_all_mappings(self) -> None:
        """Test getting all field mappings returns a copy."""
        mapper = FieldMapper()
        original_mappings = {"field1": "target1", "field2": "target2"}
        mapper.field_mappings = original_mappings

        retrieved_mappings = mapper.get_all_mappings()

        assert retrieved_mappings == original_mappings
        # Should be a copy, not the same object
        assert retrieved_mappings is not mapper.field_mappings

        # Modifying returned dict shouldn't affect original
        retrieved_mappings["new_field"] = "new_target"
        assert "new_field" not in mapper.field_mappings

    def test_get_structured_log(self) -> None:
        """Test getting structured processing log."""
        mapper = FieldMapper()

        # Add some field mappings to the log
        mapper.log_field_mapping("legacy_field", "target_field")

        structured_log = mapper.get_structured_log()

        assert "legacy_field" in structured_log.field_mappings
        assert structured_log.field_mappings["legacy_field"] == "target_field"

    def test_load_field_mapping_file_success(self) -> None:
        """Test loading field mappings from a single file."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test mapping file
            mapping_file = temp_path / "test_mapping.json"
            mapping_data = {
                "legacy_field1": "target_field1",
                "legacy_field2": "target_field2",
                "legacy_field3": None,
            }
            mapping_file.write_text(json.dumps(mapping_data))

            mapper.load_field_mapping_file(mapping_file)

            assert len(mapper.field_mappings) == 3
            assert mapper.field_mappings["legacy_field1"] == "target_field1"
            assert mapper.field_mappings["legacy_field2"] == "target_field2"
            assert mapper.field_mappings["legacy_field3"] is None

    def test_load_field_mapping_file_nonexistent_file(self) -> None:
        """Test loading from non-existent file raises error."""
        mapper = FieldMapper()
        nonexistent_file = Path("/nonexistent/file.json")

        with pytest.raises(FieldMappingError, match="Field mapping file not found"):
            mapper.load_field_mapping_file(nonexistent_file)

    def test_load_field_mapping_file_not_file(self) -> None:
        """Test loading from directory instead of file raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(FieldMappingError, match="Path is not a file"):
                mapper.load_field_mapping_file(temp_path)

    def test_load_field_mapping_file_not_json(self) -> None:
        """Test loading non-JSON file raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            text_file = temp_path / "not_json.txt"
            text_file.write_text("not json")

            with pytest.raises(FieldMappingError, match="must be a JSON file"):
                mapper.load_field_mapping_file(text_file)

    def test_load_field_mapping_file_invalid_json(self) -> None:
        """Test loading invalid JSON file raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid JSON file
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                mapper.load_field_mapping_file(invalid_json)

    def test_load_field_mapping_file_non_dict_json(self) -> None:
        """Test loading JSON file that's not a dictionary raises error."""
        mapper = FieldMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create JSON array instead of object
            json_array = temp_path / "array.json"
            json_array.write_text('["not", "a", "dict"]')

            with pytest.raises(FieldMappingError, match="must contain a JSON object"):
                mapper.load_field_mapping_file(json_array)

    def test_load_field_mapping_file_clears_existing(self) -> None:
        """Test that loading a new file clears existing mappings."""
        mapper = FieldMapper()

        # Set some initial mappings
        mapper.field_mappings = {"old_field": "old_target"}

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test mapping file
            mapping_file = temp_path / "new_mapping.json"
            mapping_data = {"new_field": "new_target"}
            mapping_file.write_text(json.dumps(mapping_data))

            mapper.load_field_mapping_file(mapping_file)

            # Should only have new mapping, old one should be cleared
            assert len(mapper.field_mappings) == 1
            assert "old_field" not in mapper.field_mappings
            assert mapper.field_mappings["new_field"] == "new_target"
