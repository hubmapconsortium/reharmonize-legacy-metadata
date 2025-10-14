"""
Tests for the value_mapper module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from metadata_transformer.exceptions import ValueMappingError
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.value_mapper import ValueMapper, ValueMappings


class TestValueMappings:
    """Test cases for ValueMappings class."""

    def test_init(self) -> None:
        """Test ValueMappings initialization."""
        mappings = ValueMappings()
        assert isinstance(mappings.get_all_mappings(), dict)
        assert len(mappings.get_all_mappings()) == 0

    def test_load_value_mappings_nonexistent_directory(self) -> None:
        """Test loading from non-existent directory raises error."""
        mappings = ValueMappings()
        nonexistent_dir = Path("/nonexistent/directory")

        with pytest.raises(
            ValueMappingError, match="Value mapping directory not found"
        ):
            mappings.load_value_mappings(nonexistent_dir)

    def test_load_value_mappings_not_directory(self) -> None:
        """Test loading from file instead of directory raises error."""
        mappings = ValueMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_file = temp_path / "not_a_dir.txt"
            temp_file.write_text("test")

            with pytest.raises(ValueMappingError, match="Path is not a directory"):
                mappings.load_value_mappings(temp_file)

    def test_load_value_mappings_no_json_files(self) -> None:
        """Test loading from directory with no JSON files raises error."""
        mappings = ValueMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create a non-JSON file
            (temp_path / "not_json.txt").write_text("test")

            with pytest.raises(ValueMappingError, match="No JSON files found"):
                mappings.load_value_mappings(temp_path)

    def test_load_value_mappings_nested_structure(self) -> None:
        """Test loading value mappings with nested field structure."""
        mappings = ValueMappings()

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

            mappings.load_value_mappings(temp_path)

            all_mappings = mappings.get_all_mappings()
            assert "assay_type" in all_mappings
            assert len(all_mappings["assay_type"]) == 3
            assert all_mappings["assay_type"]["AF"] == "Auto-fluorescence"

    def test_load_value_mappings_flat_structure(self) -> None:
        """Test loading value mappings with flat structure (uses filename as field)."""
        mappings = ValueMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mapping file with flat structure
            mapping_file = temp_path / "instrument_vendor.json"
            mapping_data = {
                "Zeiss": "Zeiss Microscopy",
                "Thermo": "Thermo Fisher Scientific",
            }
            mapping_file.write_text(json.dumps(mapping_data))

            mappings.load_value_mappings(temp_path)

            all_mappings = mappings.get_all_mappings()
            assert "instrument_vendor" in all_mappings
            assert (
                all_mappings["instrument_vendor"]["Zeiss"]
                == "Zeiss Microscopy"
            )
            assert (
                all_mappings["instrument_vendor"]["Thermo"]
                == "Thermo Fisher Scientific"
            )

    def test_load_value_mappings_multiple_files(self) -> None:
        """Test loading value mappings from multiple files."""
        mappings = ValueMappings()

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

            mappings.load_value_mappings(temp_path)

            all_mappings = mappings.get_all_mappings()
            assert "assay_type" in all_mappings
            assert "vendor" in all_mappings
            assert all_mappings["assay_type"]["AF"] == "Auto-fluorescence"
            assert all_mappings["vendor"]["Zeiss"] == "Zeiss Microscopy"

    def test_load_value_mappings_invalid_json(self) -> None:
        """Test loading invalid JSON file raises error."""
        mappings = ValueMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid JSON file
            invalid_json = temp_path / "invalid.json"
            invalid_json.write_text("{ invalid json }")

            with pytest.raises(ValueMappingError, match="Invalid JSON"):
                mappings.load_value_mappings(temp_path)

    def test_load_value_mappings_non_dict_json(self) -> None:
        """Test loading JSON file that's not a dictionary raises error."""
        mappings = ValueMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create JSON array instead of object
            json_array = temp_path / "array.json"
            json_array.write_text('["not", "a", "dict"]')

            with pytest.raises(ValueMappingError, match="must contain a JSON object"):
                mappings.load_value_mappings(temp_path)

    def test_get_mapper(self) -> None:
        """Test get_mapper creates ValueMapper with correct data."""
        mappings = ValueMappings()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            mapping_file = temp_path / "test.json"
            mapping_data = {"field1": {"old": "new"}}
            mapping_file.write_text(json.dumps(mapping_data))

            mappings.load_value_mappings(temp_path)

            log = StructuredProcessingLog()
            mapper = mappings.get_mapper(log)

            assert isinstance(mapper, ValueMapper)
            assert mapper.get_all_mappings() == {"field1": {"old": "new"}}
            assert mapper.get_structured_log() is log


class TestValueMapper:
    """Test cases for ValueMapper class."""

    def test_init_default(self) -> None:
        """Test ValueMapper initialization with defaults."""
        mapper = ValueMapper()
        assert mapper.get_all_mappings() == {}
        assert isinstance(mapper.get_structured_log(), StructuredProcessingLog)

    def test_init_with_mappings(self) -> None:
        """Test ValueMapper initialization with mappings."""
        value_mappings = {"field1": {"old": "new"}}
        log = StructuredProcessingLog()

        mapper = ValueMapper(value_mappings, log)

        assert mapper.get_all_mappings() == value_mappings
        assert mapper.get_structured_log() is log

    def test_map_value_with_mapping(self) -> None:
        """Test value mapping when mapping exists."""
        value_mappings = {
            "assay_type": {"AF": "Auto-fluorescence", "CODEX": "CODEX"}
        }
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("assay_type", "AF")
        assert result == "Auto-fluorescence"

        # Check that mapping was logged using structured format
        structured_log = mapper.get_structured_log()
        assert "assay_type" in structured_log.value_mappings
        assert structured_log.value_mappings["assay_type"]["AF"] == "Auto-fluorescence"

    def test_map_value_no_field_mapping(self) -> None:
        """Test value mapping when no field mapping exists."""
        value_mappings = {"other_field": {"key": "value"}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("nonexistent_field", "some_value")
        assert result == "some_value"  # Should return original value

    def test_map_value_no_value_mapping(self) -> None:
        """Test value mapping when field exists but value doesn't have mapping."""
        value_mappings = {"assay_type": {"AF": "Auto-fluorescence"}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("assay_type", "unknown_value")
        assert result == "unknown_value"  # Should return original value

    def test_map_value_with_none(self) -> None:
        """Test value mapping with None value."""
        value_mappings = {"field": {"None": "null_value"}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("field", None)
        assert result is None  # None converted to "None" for lookup, but no match

    def test_map_value_numeric_conversion(self) -> None:
        """Test value mapping with numeric values converted to strings for lookup."""
        value_mappings = {
            "numeric_field": {"123": "one-two-three", "456": "four-five-six"}
        }
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("numeric_field", 123)
        assert result == "one-two-three"

    def test_has_mapping_for_field(self) -> None:
        """Test checking if field has value mappings."""
        value_mappings = {"field1": {"key": "value"}, "field2": {}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        assert mapper.has_mapping_for_field("field1") is True
        assert mapper.has_mapping_for_field("field2") is True
        assert mapper.has_mapping_for_field("nonexistent") is False

    def test_get_field_mappings(self) -> None:
        """Test getting mappings for a specific field."""
        field_mappings = {"key1": "value1", "key2": "value2"}
        value_mappings = {"test_field": field_mappings}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.get_field_mappings("test_field")
        assert result == field_mappings

        # Test nonexistent field returns empty dict
        result = mapper.get_field_mappings("nonexistent")
        assert result == {}

    def test_get_all_mappings(self) -> None:
        """Test getting all value mappings returns a copy."""
        original_mappings = {"field1": {"key": "value"}}
        mapper = ValueMapper(original_mappings, StructuredProcessingLog())

        retrieved_mappings = mapper.get_all_mappings()

        assert retrieved_mappings == original_mappings
        # Should be a copy, not the same object
        assert retrieved_mappings is not original_mappings

    def test_get_structured_log(self) -> None:
        """Test getting structured processing log."""
        value_mappings = {"test_field": {"old_value": "new_value"}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        mapper.map_value("test_field", "old_value")

        structured_log = mapper.get_structured_log()

        assert "test_field" in structured_log.value_mappings
        assert structured_log.value_mappings["test_field"]["old_value"] == "new_value"

    def test_map_value_with_multi_value_mapping(self) -> None:
        """Test value mapping when mapping contains multiple target values."""
        value_mappings = {
            "acquisition_instrument_model": {
                "NovaSeq": ["NovaSeq X", "NovaSeq 6000", "NovaSeq X Plus"]
            }
        }
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

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
        value_mappings = {"test_field": {"old_value": ["new_value"]}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("test_field", "old_value")

        # Should extract single value from list and replace
        assert result == "new_value"

        # Should log normal replacement message in structured format
        structured_log = mapper.get_structured_log()
        assert "test_field" in structured_log.value_mappings
        assert structured_log.value_mappings["test_field"]["old_value"] == "new_value"

    def test_map_value_with_empty_list_mapping(self) -> None:
        """Test value mapping when mapping contains empty list."""
        value_mappings = {"test_field": {"old_value": []}}
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

        result = mapper.map_value("test_field", "old_value")

        # Should treat empty list as single value and replace
        assert result == []

        # Should log normal replacement message in structured format
        structured_log = mapper.get_structured_log()
        assert "test_field" in structured_log.value_mappings
        assert structured_log.value_mappings["test_field"]["old_value"] == []

    def test_map_value_mixed_mapping_types(self) -> None:
        """Test value mapping with mix of single values, lists, and multi-value lists."""
        value_mappings = {
            "mixed_field": {
                "single": "single_target",
                "single_list": ["single_target_from_list"],
                "multi": ["option1", "option2", "option3"],
                "empty": [],
            }
        }
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

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
        value_mappings = {
            "barcode_read": {
                "I5": None,
                "I2": None,
                "['I1', 'I2']": None,
                "R1": "Read 1 (R1)",
            }
        }
        mapper = ValueMapper(value_mappings, StructuredProcessingLog())

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
        value_mappings_log = structured_log.value_mappings["barcode_read"]
        assert value_mappings_log["I5"] is None
        assert value_mappings_log["I2"] is None
        assert value_mappings_log["['I1', 'I2']"] is None
        assert value_mappings_log["R1"] == "Read 1 (R1)"

        # Should have no unmapped values for these cases
        assert len(structured_log.ambiguous_mappings) == 0
