"""
Tests for the schema_loader module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from metadata_transformer.exceptions import SchemaValidationError
from metadata_transformer.schema_loader import SchemaLoader


class TestSchemaLoader:
    """Test cases for SchemaLoader class."""

    def test_init(self) -> None:
        """Test SchemaLoader initialization."""
        loader = SchemaLoader()
        assert isinstance(loader.schema_fields, dict)
        assert len(loader.schema_fields) == 0
        assert isinstance(loader.required_fields, list)
        assert len(loader.required_fields) == 0
        assert isinstance(loader.processing_log, list)
        assert len(loader.processing_log) == 0

    def test_load_schema_nonexistent_file(self) -> None:
        """Test loading non-existent schema file raises error."""
        loader = SchemaLoader()
        nonexistent_file = Path("/nonexistent/schema.json")

        with pytest.raises(SchemaValidationError, match="Schema file not found"):
            loader.load_schema(nonexistent_file)

    def test_load_schema_invalid_json(self) -> None:
        """Test loading invalid JSON schema file raises error."""
        loader = SchemaLoader()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            schema_file = temp_path / "invalid_schema.json"
            schema_file.write_text("{ invalid json }")

            with pytest.raises(SchemaValidationError, match="Invalid JSON"):
                loader.load_schema(schema_file)

    def test_load_schema_non_array_json(self) -> None:
        """Test loading schema file that's not a JSON array raises error."""
        loader = SchemaLoader()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            schema_file = temp_path / "object_schema.json"
            schema_file.write_text('{"not": "an array"}')

            with pytest.raises(
                SchemaValidationError, match="must contain a JSON array"
            ):
                loader.load_schema(schema_file)

    def test_load_schema_valid_schema(self) -> None:
        """Test loading valid schema file."""
        loader = SchemaLoader()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            schema_file = temp_path / "valid_schema.json"

            schema_data = [
                {
                    "name": "required_field",
                    "description": "A required field",
                    "type": "text",
                    "required": True,
                    "regex": "^test.*",
                    "default_value": "default",
                    "permissible_values": ["value1", "value2"],
                },
                {
                    "name": "optional_field",
                    "description": "An optional field",
                    "type": "number",
                    "required": False,
                    "default_value": None,
                },
            ]
            schema_file.write_text(json.dumps(schema_data))

            loader.load_schema(schema_file)

            # Check schema fields were loaded
            assert len(loader.schema_fields) == 2
            assert "required_field" in loader.schema_fields
            assert "optional_field" in loader.schema_fields

            # Check required fields
            assert len(loader.required_fields) == 1
            assert "required_field" in loader.required_fields

            # Check field definitions
            required_def = loader.schema_fields["required_field"]
            assert required_def["description"] == "A required field"
            assert required_def["type"] == "text"
            assert required_def["required"] is True
            assert required_def["regex"] == "^test.*"
            assert required_def["default_value"] == "default"
            assert required_def["permissible_values"] == ["value1", "value2"]

            optional_def = loader.schema_fields["optional_field"]
            assert optional_def["description"] == "An optional field"
            assert optional_def["type"] == "number"
            assert optional_def["required"] is False
            assert optional_def["default_value"] is None

    def test_load_schema_with_invalid_field_definitions(self) -> None:
        """Test loading schema with invalid field definitions logs warnings."""
        loader = SchemaLoader()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            schema_file = temp_path / "schema_with_invalid.json"

            schema_data = [
                "not a dict",  # Should be skipped
                {"description": "No name field"},  # Should be skipped
                {
                    "name": "valid_field",
                    "description": "Valid field",
                },  # Should be loaded
            ]
            schema_file.write_text(json.dumps(schema_data))

            loader.load_schema(schema_file)

            # Only valid field should be loaded
            assert len(loader.schema_fields) == 1
            assert "valid_field" in loader.schema_fields

            # Check warnings - schema warnings no longer logged
            # Invalid field definitions are silently skipped during loading
            assert len(loader.processing_log) == 0

    def test_get_schema_fields(self) -> None:
        """Test getting schema fields returns a copy."""
        loader = SchemaLoader()
        original_fields = {"field1": {"type": "text"}}
        loader.schema_fields = original_fields

        retrieved_fields = loader.get_schema_fields()

        assert retrieved_fields == original_fields
        # Should be a copy, not the same object
        assert retrieved_fields is not loader.schema_fields

    def test_get_required_fields(self) -> None:
        """Test getting required fields returns a copy."""
        loader = SchemaLoader()
        original_required = ["field1", "field2"]
        loader.required_fields = original_required

        retrieved_required = loader.get_required_fields()

        assert retrieved_required == original_required
        # Should be a copy, not the same object
        assert retrieved_required is not loader.required_fields

    def test_is_field_required(self) -> None:
        """Test checking if field is required."""
        loader = SchemaLoader()
        loader.required_fields = ["required_field"]

        assert loader.is_field_required("required_field") is True
        assert loader.is_field_required("optional_field") is False

    def test_get_field_definition(self) -> None:
        """Test getting field definition."""
        loader = SchemaLoader()
        field_def = {"type": "text", "required": True}
        loader.schema_fields = {"test_field": field_def}

        result = loader.get_field_definition("test_field")
        assert result == field_def

        result = loader.get_field_definition("nonexistent")
        assert result is None

    def test_get_default_value(self) -> None:
        """Test getting default value for field."""
        loader = SchemaLoader()
        loader.schema_fields = {
            "field_with_default": {"default_value": "test_default"},
            "field_without_default": {"type": "text"},
            "field_with_null_default": {"default_value": None},
        }

        assert loader.get_default_value("field_with_default") == "test_default"
        assert loader.get_default_value("field_without_default") is None
        assert loader.get_default_value("field_with_null_default") is None
        assert loader.get_default_value("nonexistent") is None

    def test_validate_field_value_with_permissible_values(self) -> None:
        """Test field value validation with permissible values."""
        loader = SchemaLoader()
        loader.schema_fields = {
            "restricted_field": {
                "permissible_values": ["allowed1", "allowed2", "allowed3"]
            },
            "unrestricted_field": {"type": "text"},
        }

        # Valid values
        assert loader.validate_field_value("restricted_field", "allowed1") is True
        assert loader.validate_field_value("restricted_field", "allowed2") is True
        assert loader.validate_field_value("unrestricted_field", "any_value") is True

        # Invalid value
        assert loader.validate_field_value("restricted_field", "not_allowed") is False

        # Nonexistent field should be valid
        assert loader.validate_field_value("nonexistent", "any_value") is True

    def test_get_processing_log(self) -> None:
        """Test getting processing log returns a copy."""
        loader = SchemaLoader()
        test_log = [{"phase": "test", "action": "test_action"}]
        loader.processing_log = test_log

        retrieved_log = loader.get_processing_log()

        assert retrieved_log == test_log
        # Should be a copy, not the same object
        assert retrieved_log is not loader.processing_log
