"""
Tests for the field_mapper module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.field_mapper import FieldMapper, FieldMappings
from metadata_transformer.processing_log import StructuredProcessingLog


class TestFieldMappings:
    """Test cases for FieldMappings class."""

    def test_init(self) -> None:
        """Test FieldMappings initialization."""
        mappings = FieldMappings()
        assert isinstance(mappings.get_all_mappings(), dict)
        assert len(mappings.get_all_mappings()) == 0

    def test_load_field_mappings_nonexistent_directory(self) -> None:
        """Test loading from non-existent directory raises error."""
        mappings = FieldMappings()
        nonexistent_dir = Path("/nonexistent/directory")

        with pytest.raises(
            FieldMappingError, match="Field mapping directory not found"
        ):
            mappings.load_field_mappings(nonexistent_dir)

    def test_load_field_mappings_not_directory(self) -> None:
        """Test loading from file instead of directory raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_file = temp_path / "not_a_dir.txt"
            temp_file.write_text("test")

            with pytest.raises(FieldMappingError, match="Path is not a directory"):
                mappings.load_field_mappings(temp_file)

    def test_load_field_mappings_no_json_files(self) -> None:
        """Test loading from directory with no JSON files raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create a non-JSON file
            (temp_path / "not_json.txt").write_text("test")

            with pytest.raises(FieldMappingError, match="No JSON files found"):
                mappings.load_field_mappings(temp_path)

    def test_load_field_mappings_single_file(self) -> None:
        """Test loading field mappings from single file."""
        mappings = FieldMappings()

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

            mappings.load_field_mappings(temp_path)

            all_mappings = mappings.get_all_mappings()
            assert len(all_mappings) == 3
            assert all_mappings["legacy_field1"] == "target_field1"
            assert all_mappings["legacy_field2"] == "target_field2"
            assert all_mappings["legacy_field3"] is None

    def test_load_field_mappings_multiple_files_no_conflicts(self) -> None:
        """Test loading field mappings from multiple files without conflicts."""
        mappings = FieldMappings()

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

            mappings.load_field_mappings(temp_path)

            all_mappings = mappings.get_all_mappings()
            assert len(all_mappings) == 4
            assert all_mappings["field_a"] == "target_a"
            assert all_mappings["field_b"] == "target_b"
            assert all_mappings["field_c"] == "target_c"
            assert all_mappings["field_d"] is None

    def test_load_field_mappings_with_conflicts(self) -> None:
        """Test loading field mappings with conflicts keeps existing mappings."""
        mappings = FieldMappings()

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

            mappings.load_field_mappings(temp_path)

            all_mappings = mappings.get_all_mappings()
            # Should keep original mapping
            assert all_mappings["field_a"] == "target_a"
            assert all_mappings["field_b"] == "target_b"
            assert all_mappings["field_c"] == "target_c"

    def test_load_field_mappings_invalid_json(self) -> None:
        """Test loading invalid JSON file raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid JSON file
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                mappings.load_field_mappings(temp_path)

    def test_load_field_mappings_non_dict_json(self) -> None:
        """Test loading JSON file that's not a dictionary raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create JSON array instead of object
            json_array = temp_path / "array.json"
            json_array.write_text('["not", "a", "dict"]')

            with pytest.raises(FieldMappingError, match="must contain a JSON object"):
                mappings.load_field_mappings(temp_path)

    def test_load_field_mapping_file_success(self) -> None:
        """Test loading field mappings from a single file."""
        mappings = FieldMappings()

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

            mappings.load_field_mapping_file(mapping_file)

            all_mappings = mappings.get_all_mappings()
            assert len(all_mappings) == 3
            assert all_mappings["legacy_field1"] == "target_field1"
            assert all_mappings["legacy_field2"] == "target_field2"
            assert all_mappings["legacy_field3"] is None

    def test_load_field_mapping_file_nonexistent_file(self) -> None:
        """Test loading from non-existent file raises error."""
        mappings = FieldMappings()
        nonexistent_file = Path("/nonexistent/file.json")

        with pytest.raises(FieldMappingError, match="Field mapping file not found"):
            mappings.load_field_mapping_file(nonexistent_file)

    def test_load_field_mapping_file_not_file(self) -> None:
        """Test loading from directory instead of file raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(FieldMappingError, match="Path is not a file"):
                mappings.load_field_mapping_file(temp_path)

    def test_load_field_mapping_file_not_json(self) -> None:
        """Test loading non-JSON file raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            text_file = temp_path / "not_json.txt"
            text_file.write_text("not json")

            with pytest.raises(FieldMappingError, match="must be a JSON file"):
                mappings.load_field_mapping_file(text_file)

    def test_load_field_mapping_file_invalid_json(self) -> None:
        """Test loading invalid JSON file raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid JSON file
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(FieldMappingError, match="Invalid JSON"):
                mappings.load_field_mapping_file(invalid_json)

    def test_load_field_mapping_file_non_dict_json(self) -> None:
        """Test loading JSON file that's not a dictionary raises error."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create JSON array instead of object
            json_array = temp_path / "array.json"
            json_array.write_text('["not", "a", "dict"]')

            with pytest.raises(FieldMappingError, match="must contain a JSON object"):
                mappings.load_field_mapping_file(json_array)

    def test_load_field_mapping_file_clears_existing(self) -> None:
        """Test that loading a new file clears existing mappings."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Load initial mapping
            mapping_file1 = temp_path / "first_mapping.json"
            mapping_data1 = {"old_field": "old_target"}
            mapping_file1.write_text(json.dumps(mapping_data1))
            mappings.load_field_mapping_file(mapping_file1)

            # Load second mapping file - should clear existing
            mapping_file2 = temp_path / "new_mapping.json"
            mapping_data2 = {"new_field": "new_target"}
            mapping_file2.write_text(json.dumps(mapping_data2))
            mappings.load_field_mapping_file(mapping_file2)

            # Should only have new mapping, old one should be cleared
            all_mappings = mappings.get_all_mappings()
            assert len(all_mappings) == 1
            assert "old_field" not in all_mappings
            assert all_mappings["new_field"] == "new_target"

    def test_get_mapper(self) -> None:
        """Test get_mapper creates FieldMapper with correct data."""
        mappings = FieldMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            mapping_file = temp_path / "test.json"
            mapping_data = {"legacy_field": "target_field"}
            mapping_file.write_text(json.dumps(mapping_data))

            mappings.load_field_mappings(temp_path)

            log = StructuredProcessingLog()
            mapper = mappings.get_mapper(log)

            assert isinstance(mapper, FieldMapper)
            assert mapper.get_all_mappings() == {"legacy_field": "target_field"}
            assert mapper.get_structured_log() is log


class TestFieldMapper:
    """Test cases for FieldMapper class."""

    def test_init_default(self) -> None:
        """Test FieldMapper initialization with defaults."""
        mapper = FieldMapper()
        assert mapper.get_all_mappings() == {}
        assert isinstance(mapper.get_structured_log(), StructuredProcessingLog)

    def test_init_with_mappings(self) -> None:
        """Test FieldMapper initialization with mappings."""
        field_mappings = {"legacy_field": "target_field"}
        log = StructuredProcessingLog()

        mapper = FieldMapper(field_mappings, log)

        assert mapper.get_all_mappings() == field_mappings
        assert mapper.get_structured_log() is log

    def test_map_field(self) -> None:
        """Test field mapping functionality."""
        field_mappings = {
            "legacy_field": "target_field",
            "another_field": None,
            "third_field": "mapped_field",
        }
        mapper = FieldMapper(field_mappings, StructuredProcessingLog())

        assert mapper.map_field("legacy_field") == "target_field"
        assert mapper.map_field("another_field") is None
        assert mapper.map_field("third_field") == "mapped_field"
        assert mapper.map_field("nonexistent_field") is None

    def test_get_all_mappings(self) -> None:
        """Test getting all field mappings returns a copy."""
        original_mappings = {"field1": "target1", "field2": "target2"}
        mapper = FieldMapper(original_mappings, StructuredProcessingLog())

        retrieved_mappings = mapper.get_all_mappings()

        assert retrieved_mappings == original_mappings
        # Should be a copy, not the same object
        assert retrieved_mappings is not original_mappings

        # Modifying returned dict shouldn't affect original
        retrieved_mappings["new_field"] = "new_target"
        assert "new_field" not in mapper.get_all_mappings()

    def test_get_structured_log(self) -> None:
        """Test getting structured processing log."""
        mapper = FieldMapper({}, StructuredProcessingLog())

        # Add some field mappings to the log
        mapper.log_field_mapping("legacy_field", "target_field")

        structured_log = mapper.get_structured_log()

        assert "legacy_field" in structured_log.field_mappings
        assert structured_log.field_mappings["legacy_field"] == "target_field"
