"""
Tests for structured processing log functionality.
"""

from metadata_transformer.processing_log import (
    StructuredProcessingLog,
    UnmappedValueEntry,
)


class TestUnmappedValueEntry:
    """Test the UnmappedValueEntry dataclass."""

    def test_unmapped_value_entry_creation(self):
        """Test creating an UnmappedValueEntry."""
        entry = UnmappedValueEntry(
            field="test_field",
            value="test_value",
            permissible_values=["option1", "option2"],
        )

        assert entry.field == "test_field"
        assert entry.value == "test_value"
        assert entry.permissible_values == ["option1", "option2"]

    def test_unmapped_value_entry_default_permissible_values(self):
        """Test UnmappedValueEntry with default empty permissible_values."""
        entry = UnmappedValueEntry(field="test_field", value="test_value")
        assert entry.permissible_values == []


class TestStructuredProcessingLog:
    """Test the StructuredProcessingLog class."""

    def test_initialization(self):
        """Test StructuredProcessingLog initialization."""
        log = StructuredProcessingLog()

        assert log.field_mappings == {}
        assert log.ambiguous_mappings == []
        assert log.value_mappings == {}
        assert log.excluded_data == {}

    def test_add_unmapped_field_with_value(self):
        """Test adding unmapped fields with values."""
        log = StructuredProcessingLog()

        log.add_unmapped_field_with_value("field1", "value1")
        log.add_unmapped_field_with_value("field2", {"complex": "value"})

        # Check that excluded data dict is populated
        assert log.excluded_data == {"field1": "value1", "field2": {"complex": "value"}}

    def test_add_mapped_field(self):
        """Test adding mapped fields."""
        log = StructuredProcessingLog()

        log.add_mapped_field("legacy_field", "target_field")

        assert log.field_mappings == {"legacy_field": "target_field"}

    def test_add_unmapped_value(self):
        """Test adding unmapped values."""
        log = StructuredProcessingLog()

        log.add_unmapped_value("field1", "value1", ["option1", "option2"])
        log.add_unmapped_value("field2", "value2")  # No permissible values

        assert len(log.ambiguous_mappings) == 2
        assert log.ambiguous_mappings[0].field == "field1"
        assert log.ambiguous_mappings[0].value == "value1"
        assert log.ambiguous_mappings[0].permissible_values == ["option1", "option2"]
        assert log.ambiguous_mappings[1].field == "field2"
        assert log.ambiguous_mappings[1].value == "value2"
        assert log.ambiguous_mappings[1].permissible_values == []

    def test_add_mapped_value(self):
        """Test adding mapped values."""
        log = StructuredProcessingLog()

        log.add_mapped_value("False", "No", "test_field1")
        log.add_mapped_value(
            123, "456", "test_field2"
        )  # Non-string values should be converted
        log.add_mapped_value(
            "True", "Yes", "test_field1"
        )  # Multiple values for same field

        assert log.value_mappings == {
            "test_field1": {"False": "No", "True": "Yes"},
            "test_field2": {"123": "456"},
        }

    def test_to_dict(self):
        """Test converting to dictionary format."""
        log = StructuredProcessingLog()

        log.add_mapped_field("legacy_field", "target_field")
        log.add_unmapped_value("field1", "value1", ["option1", "option2"])
        log.add_mapped_value("False", "No", "test_field")

        result = log.to_dict()

        expected = {
            "field_mappings": {"legacy_field": "target_field"},
            "value_mappings": {"test_field": {"False": "No"}},
            "ambiguous_mappings": [
                {
                    "field": "field1",
                    "value": "value1",
                    "permissible_values": ["option1", "option2"],
                }
            ],
            "excluded_data": {},
            "metadata_patches": [],
        }

        assert result == expected

    def test_to_dict_with_excluded_data(self):
        """Test converting to dictionary format with excluded data."""
        log = StructuredProcessingLog()

        log.add_unmapped_field_with_value("field1", "value1")
        log.add_unmapped_field_with_value("field2", {"complex": "value"})

        result = log.to_dict()

        expected = {
            "field_mappings": {},
            "value_mappings": {},
            "ambiguous_mappings": [],
            "excluded_data": {"field1": "value1", "field2": {"complex": "value"}},
            "metadata_patches": [],
        }

        assert result == expected

    def test_merge_with(self):
        """Test merging two structured logs."""
        log1 = StructuredProcessingLog()
        log1.add_mapped_field("legacy1", "target1")
        log1.add_mapped_value("False", "No", "field1")

        log2 = StructuredProcessingLog()
        log2.add_mapped_field("legacy2", "target2")
        log2.add_unmapped_value("field_x", "value_x", ["opt1", "opt2"])
        log2.add_mapped_value("True", "Yes", "field2")
        log2.add_unmapped_field_with_value("field_detail", "detail_value")

        log1.merge_with(log2)

        assert log1.field_mappings == {"legacy1": "target1", "legacy2": "target2"}
        assert len(log1.ambiguous_mappings) == 1
        assert log1.ambiguous_mappings[0].field == "field_x"
        assert log1.value_mappings == {
            "field1": {"False": "No"},
            "field2": {"True": "Yes"},
        }
        assert log1.excluded_data == {"field_detail": "detail_value"}
