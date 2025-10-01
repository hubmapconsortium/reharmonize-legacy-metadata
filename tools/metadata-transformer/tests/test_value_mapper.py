"""
Tests for the value_mapper module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from metadata_transformer.exceptions import ValueMappingError
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.value_mapper import ValueMapper


class TestValueMapper:
    """Test cases for ValueMapper class."""

    def test_init(self) -> None:
        """Test ValueMapper initialization."""
        mapper = ValueMapper()
        assert isinstance(mapper.value_mappings, dict)
        assert len(mapper.value_mappings) == 0
        assert isinstance(mapper.structured_log, StructuredProcessingLog)
        assert len(mapper.structured_log.field_mappings) == 0
        assert len(mapper.structured_log.ambiguous_mappings) == 0

    def test_load_value_mappings_nonexistent_directory(self) -> None:
        """Test loading from non-existent directory raises error."""
        mapper = ValueMapper()
        nonexistent_dir = Path("/nonexistent/directory")

        with pytest.raises(
            ValueMappingError, match="Value mapping directory not found"
        ):
            mapper.load_value_mappings(nonexistent_dir)

    def test_load_value_mappings_not_directory(self) -> None:
        """Test loading from file instead of directory raises error."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_file = temp_path / "not_a_dir.txt"
            temp_file.write_text("test")

            with pytest.raises(ValueMappingError, match="Path is not a directory"):
                mapper.load_value_mappings(temp_file)

    def test_load_value_mappings_no_json_files(self) -> None:
        """Test loading from directory with no JSON files raises error."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create a non-JSON file
            (temp_path / "not_json.txt").write_text("test")

            with pytest.raises(ValueMappingError, match="No JSON files found"):
                mapper.load_value_mappings(temp_path)

    def test_load_value_mappings_nested_structure(self) -> None:
        """Test loading value mappings with nested field structure."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mapping file with nested structure
            mapping_file = temp_path / "assay_type.json"
            mapping_data = {
                "assay_type": {
                    "AF": "Auto-fluorescence",
                    "LC-MS": "LC-MS",
                    "CODEX": "CODEX",
                }
            }
            mapping_file.write_text(json.dumps(mapping_data))

            mapper.load_value_mappings(temp_path)

            assert "assay_type" in mapper.value_mappings
            assert len(mapper.value_mappings["assay_type"]) == 3
            assert mapper.value_mappings["assay_type"]["AF"] == "Auto-fluorescence"

    def test_load_value_mappings_flat_structure(self) -> None:
        """Test loading value mappings with flat structure (uses filename as field)."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mapping file with flat structure
            mapping_file = temp_path / "instrument_vendor.json"
            mapping_data = {
                "Zeiss": "Zeiss Microscopy",
                "Thermo": "Thermo Fisher Scientific",
            }
            mapping_file.write_text(json.dumps(mapping_data))

            mapper.load_value_mappings(temp_path)

            assert "instrument_vendor" in mapper.value_mappings
            assert (
                mapper.value_mappings["instrument_vendor"]["Zeiss"]
                == "Zeiss Microscopy"
            )
            assert (
                mapper.value_mappings["instrument_vendor"]["Thermo"]
                == "Thermo Fisher Scientific"
            )

    def test_load_value_mappings_multiple_files(self) -> None:
        """Test loading value mappings from multiple files."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create first mapping file
            mapping1 = temp_path / "assay_type.json"
            data1 = {"assay_type": {"AF": "Auto-fluorescence", "CODEX": "CODEX"}}
            mapping1.write_text(json.dumps(data1))

            # Create second mapping file
            mapping2 = temp_path / "vendor.json"
            data2 = {"Zeiss": "Zeiss Microscopy", "Thermo": "Thermo Fisher"}
            mapping2.write_text(json.dumps(data2))

            mapper.load_value_mappings(temp_path)

            assert "assay_type" in mapper.value_mappings
            assert "vendor" in mapper.value_mappings
            assert mapper.value_mappings["assay_type"]["AF"] == "Auto-fluorescence"
            assert mapper.value_mappings["vendor"]["Zeiss"] == "Zeiss Microscopy"

    def test_load_value_mappings_invalid_json(self) -> None:
        """Test loading invalid JSON file raises error."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid JSON file
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(ValueMappingError, match="Invalid JSON"):
                mapper.load_value_mappings(temp_path)

    def test_load_value_mappings_non_dict_json(self) -> None:
        """Test loading JSON file that's not a dictionary raises error."""
        mapper = ValueMapper()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create JSON array instead of object
            json_array = temp_path / "array.json"
            json_array.write_text('["not", "a", "dict"]')

            with pytest.raises(ValueMappingError, match="must contain a JSON object"):
                mapper.load_value_mappings(temp_path)

    def test_map_value_with_mapping(self) -> None:
        """Test value mapping when mapping exists."""
        mapper = ValueMapper()
        mapper.value_mappings = {
            "assay_type": {"AF": "Auto-fluorescence", "CODEX": "CODEX"}
        }

        result = mapper.map_value("assay_type", "AF")
        assert result == "Auto-fluorescence"

        # Check that mapping was logged using structured format
        structured_log = mapper.get_structured_log()
        assert "assay_type" in structured_log.value_mappings
        assert structured_log.value_mappings["assay_type"]["AF"] == "Auto-fluorescence"

    def test_map_value_no_field_mapping(self) -> None:
        """Test value mapping when no field mapping exists."""
        mapper = ValueMapper()
        mapper.value_mappings = {"other_field": {"key": "value"}}

        result = mapper.map_value("nonexistent_field", "some_value")
        assert result == "some_value"  # Should return original value

    def test_map_value_no_value_mapping(self) -> None:
        """Test value mapping when field exists but value doesn't have mapping."""
        mapper = ValueMapper()
        mapper.value_mappings = {"assay_type": {"AF": "Auto-fluorescence"}}

        result = mapper.map_value("assay_type", "unknown_value")
        assert result == "unknown_value"  # Should return original value

    def test_map_value_with_none(self) -> None:
        """Test value mapping with None value."""
        mapper = ValueMapper()
        mapper.value_mappings = {"field": {"None": "null_value"}}

        result = mapper.map_value("field", None)
        assert result is None  # None converted to "None" for lookup, but no match

    def test_map_value_numeric_conversion(self) -> None:
        """Test value mapping with numeric values converted to strings for lookup."""
        mapper = ValueMapper()
        mapper.value_mappings = {
            "numeric_field": {"123": "one-two-three", "456": "four-five-six"}
        }

        result = mapper.map_value("numeric_field", 123)
        assert result == "one-two-three"

    def test_has_mapping_for_field(self) -> None:
        """Test checking if field has value mappings."""
        mapper = ValueMapper()
        mapper.value_mappings = {"field1": {"key": "value"}, "field2": {}}

        assert mapper.has_mapping_for_field("field1") is True
        assert mapper.has_mapping_for_field("field2") is True
        assert mapper.has_mapping_for_field("nonexistent") is False

    def test_get_field_mappings(self) -> None:
        """Test getting mappings for a specific field."""
        mapper = ValueMapper()
        field_mappings = {"key1": "value1", "key2": "value2"}
        mapper.value_mappings = {"test_field": field_mappings}

        result = mapper.get_field_mappings("test_field")
        assert result == field_mappings

        # Test nonexistent field returns empty dict
        result = mapper.get_field_mappings("nonexistent")
        assert result == {}

    def test_get_all_mappings(self) -> None:
        """Test getting all value mappings returns a copy."""
        mapper = ValueMapper()
        original_mappings = {"field1": {"key": "value"}}
        mapper.value_mappings = original_mappings

        retrieved_mappings = mapper.get_all_mappings()

        assert retrieved_mappings == original_mappings
        # Should be a copy, not the same object
        assert retrieved_mappings is not mapper.value_mappings

    def test_get_structured_log(self) -> None:
        """Test getting structured processing log."""
        mapper = ValueMapper()

        # Add some value mappings to the log
        mapper.value_mappings = {"test_field": {"old_value": "new_value"}}
        mapper.map_value("test_field", "old_value")

        structured_log = mapper.get_structured_log()

        assert "test_field" in structured_log.value_mappings
        assert structured_log.value_mappings["test_field"]["old_value"] == "new_value"

    def test_map_value_with_multi_value_mapping(self) -> None:
        """Test value mapping when mapping contains multiple target values."""
        mapper = ValueMapper()
        mapper.value_mappings = {
            "acquisition_instrument_model": {
                "NovaSeq": ["NovaSeq X", "NovaSeq 6000", "NovaSeq X Plus"]
            }
        }

        result = mapper.map_value("acquisition_instrument_model", "NovaSeq")

        # Should return original value unchanged
        assert result == "NovaSeq"

        # Should log skip message instead of replacement in structured format
        structured_log = mapper.get_structured_log()
        assert len(structured_log.ambiguous_mappings) == 1
        unmapped_entry = structured_log.ambiguous_mappings[0]
        assert unmapped_entry.field == "acquisition_instrument_model"
        assert unmapped_entry.value == "NovaSeq"
        assert unmapped_entry.permissible_values == [
            "NovaSeq X",
            "NovaSeq 6000",
            "NovaSeq X Plus",
        ]

    def test_map_value_with_single_item_list_mapping(self) -> None:
        """Test value mapping when mapping contains single-item list."""
        mapper = ValueMapper()
        mapper.value_mappings = {"test_field": {"old_value": ["new_value"]}}

        result = mapper.map_value("test_field", "old_value")

        # Should extract single value from list and replace
        assert result == "new_value"

        # Should log normal replacement message in structured format
        structured_log = mapper.get_structured_log()
        assert "test_field" in structured_log.value_mappings
        assert structured_log.value_mappings["test_field"]["old_value"] == "new_value"

    def test_map_value_with_empty_list_mapping(self) -> None:
        """Test value mapping when mapping contains empty list."""
        mapper = ValueMapper()
        mapper.value_mappings = {"test_field": {"old_value": []}}

        result = mapper.map_value("test_field", "old_value")

        # Should treat empty list as single value and replace
        assert result == []

        # Should log normal replacement message in structured format
        structured_log = mapper.get_structured_log()
        assert "test_field" in structured_log.value_mappings
        assert structured_log.value_mappings["test_field"]["old_value"] == []

    def test_map_value_mixed_mapping_types(self) -> None:
        """Test value mapping with mix of single values, lists, and multi-value lists."""
        mapper = ValueMapper()
        mapper.value_mappings = {
            "mixed_field": {
                "single": "single_target",
                "single_list": ["single_target_from_list"],
                "multi": ["option1", "option2", "option3"],
                "empty": [],
            }
        }

        # Test single value mapping
        result1 = mapper.map_value("mixed_field", "single")
        assert result1 == "single_target"

        # Test single-item list mapping
        result2 = mapper.map_value("mixed_field", "single_list")
        assert result2 == "single_target_from_list"

        # Test multi-value list mapping
        result3 = mapper.map_value("mixed_field", "multi")
        assert result3 == "multi"  # Should keep original

        # Test empty list mapping
        result4 = mapper.map_value("mixed_field", "empty")
        assert result4 == []

        # Check structured processing log has correct entries
        structured_log = mapper.get_structured_log()

        # Check mapped values
        assert "mixed_field" in structured_log.value_mappings
        assert structured_log.value_mappings["mixed_field"]["single"] == "single_target"
        assert (
            structured_log.value_mappings["mixed_field"]["single_list"]
            == "single_target_from_list"
        )
        assert structured_log.value_mappings["mixed_field"]["empty"] == []

        # Check unmapped values
        assert len(structured_log.ambiguous_mappings) == 1
        unmapped_entry = structured_log.ambiguous_mappings[0]
        assert unmapped_entry.field == "mixed_field"
        assert unmapped_entry.value == "multi"
        assert unmapped_entry.permissible_values == ["option1", "option2", "option3"]

    def test_map_value_with_null_mapping(self) -> None:
        """Test mapping values to null works correctly."""
        mapper = ValueMapper()

        # Set up value mappings with null targets
        mapper.value_mappings = {
            "barcode_read": {
                "I5": None,
                "I2": None,
                "['I1', 'I2']": None,
                "R1": "Read 1 (R1)",
            }
        }

        # Test mapping values to null
        assert mapper.map_value("barcode_read", "I5") is None
        assert mapper.map_value("barcode_read", "I2") is None
        assert mapper.map_value("barcode_read", "['I1', 'I2']") is None

        # Test mapping to non-null value still works
        assert mapper.map_value("barcode_read", "R1") == "Read 1 (R1)"

        # Test unmapped value returns original
        assert mapper.map_value("barcode_read", "unmapped") == "unmapped"

        # Check structured processing log has correct entries
        structured_log = mapper.get_structured_log()

        # Check mapped values include null mappings
        assert "barcode_read" in structured_log.value_mappings
        value_mappings = structured_log.value_mappings["barcode_read"]
        assert value_mappings["I5"] is None
        assert value_mappings["I2"] is None
        assert value_mappings["['I1', 'I2']"] is None
        assert value_mappings["R1"] == "Read 1 (R1)"

        # Should have no unmapped values for these cases
        assert len(structured_log.ambiguous_mappings) == 0
