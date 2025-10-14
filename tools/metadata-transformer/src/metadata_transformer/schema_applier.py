"""
Schema specification and application functionality for target schema definitions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from metadata_transformer.exceptions import SchemaValidationError
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.processing_log_provider import ProcessingLogProvider


class Schema:
    """
    Repository holding schema specification loaded from files.

    This class is responsible for loading and storing schema definitions.
    Once loaded, the schema can be used to create multiple SchemaApplier
    instances for concurrent or sequential transformations.
    """

    def __init__(self) -> None:
        """Initialize an empty Schema repository."""
        self._schema_fields: Dict[str, Dict[str, Any]] = {}
        self._required_fields: List[str] = []

    def load_schema(self, schema_file: Path) -> None:
        """
        Load a target schema file.

        Args:
            schema_file: Path to the JSON schema file

        Raises:
            SchemaValidationError: If schema file can't be loaded or is invalid
        """
        if not schema_file.exists():
            raise SchemaValidationError(f"Schema file not found: {schema_file}")

        # Schema loading info moved to stdout - handled by CLI

        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(
                f"Invalid JSON in schema file {schema_file}: {e}"
            )
        except Exception as e:
            raise SchemaValidationError(f"Error reading schema file {schema_file}: {e}")

        if not isinstance(schema_data, list):
            raise SchemaValidationError(
                f"Schema file must contain a JSON array: {schema_file}"
            )

        self._parse_schema_fields(schema_data)

        # Schema loading completion info moved to stdout - handled by CLI

    def _parse_schema_fields(self, schema_data: List[Dict[str, Any]]) -> None:
        """
        Parse schema field definitions from schema data.

        Args:
            schema_data: List of field definitions from schema file

        Raises:
            SchemaValidationError: If schema structure is invalid
        """
        for field_def in schema_data:
            if not isinstance(field_def, dict):
                # Schema warnings moved to stdout - handled by CLI
                continue

            field_name = field_def.get("name")
            if not field_name:
                # Schema warnings moved to stdout - handled by CLI
                continue

            # Store field definition
            self._schema_fields[field_name] = {
                "description": field_def.get("description", ""),
                "type": field_def.get("type", "text"),
                "required": field_def.get("required", False),
                "regex": field_def.get("regex"),
                "default_value": field_def.get("default_value"),
                "permissible_values": field_def.get("permissible_values"),
            }

            # Track required fields
            if field_def.get("required", False):
                self._required_fields.append(field_name)

    def get_schema_fields(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all schema field definitions.

        Returns:
            Dictionary of field definitions
        """
        return self._schema_fields.copy()

    def get_required_fields(self) -> List[str]:
        """
        Get list of required field names.

        Returns:
            List of required field names
        """
        return self._required_fields.copy()

    def is_field_required(self, field_name: str) -> bool:
        """
        Check if a field is required by the schema.

        Args:
            field_name: Name of the field to check

        Returns:
            True if field is required, False otherwise
        """
        return field_name in self._required_fields

    def get_field_definition(self, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema definition for a specific field.

        Args:
            field_name: Name of the field

        Returns:
            Field definition dictionary, or None if field not in schema
        """
        return self._schema_fields.get(field_name)

    def get_default_value(self, field_name: str) -> Any:
        """
        Get the default value for a schema field.

        Args:
            field_name: Name of the field

        Returns:
            Default value for the field, or None if no default specified
        """
        field_def = self._schema_fields.get(field_name, {})
        return field_def.get("default_value")

    def validate_field_value(self, field_name: str, value: Any) -> bool:
        """
        Validate a field value against its schema definition.

        Args:
            field_name: Name of the field
            value: Value to validate

        Returns:
            True if value is valid, False otherwise
        """
        field_def = self.get_field_definition(field_name)
        if not field_def:
            return True  # If field not in schema, assume valid

        # Check permissible values
        permissible_values = field_def.get("permissible_values")
        if permissible_values is not None and value not in permissible_values:
            return False

        # Additional validation could be added here for regex, type checking, etc.

        return True

    def get_applier(self, log_provider: ProcessingLogProvider) -> "SchemaApplier":
        """
        Create a SchemaApplier instance with the loaded schema and a log provider.

        This factory method ensures immutability - each transformation gets its own
        applier instance with an isolated processing log.

        Args:
            log_provider: Provider for creating processing logs

        Returns:
            New SchemaApplier instance with schema and log provider
        """
        return SchemaApplier(self._schema_fields.copy(), log_provider)


class SchemaApplier:
    """
    Immutable schema applier that ensures metadata conforms to schema.

    This class is created per transformation and contains both the schema definition
    and a processing log for that specific transformation. It is immutable after
    construction, ensuring thread-safety and preventing accidental state mutations.
    """

    def __init__(
        self,
        schema_fields: Dict[str, Dict[str, Any]],
        log_provider: ProcessingLogProvider,
    ) -> None:
        """
        Initialize a SchemaApplier with schema and log provider.

        Args:
            schema_fields: Dictionary of schema field definitions.
            log_provider: Provider for creating processing logs.
        """
        self._schema_fields = schema_fields
        self._log = log_provider.create_log()

    def apply_schema(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply schema compliance to metadata.

        Args:
            metadata: Metadata with field and value mappings applied

        Returns:
            Schema-compliant metadata
        """
        compliant_metadata = {}

        # Add all schema fields with appropriate values
        for schema_field in self._schema_fields:
            if schema_field in metadata:
                compliant_metadata[schema_field] = metadata[schema_field]
            else:
                default_value = self._get_default_value(schema_field)
                compliant_metadata[schema_field] = default_value

        # Log obsolete fields that don't map to schema
        for field_name, field_value in metadata.items():
            if field_name not in self._schema_fields:
                self._log.add_unmapped_field_with_value(field_name, field_value)

        return compliant_metadata

    def _get_default_value(self, field_name: str) -> Any:
        """
        Get the default value for a schema field.

        Args:
            field_name: Name of the field

        Returns:
            Default value for the field, or None if no default specified
        """
        field_def = self._schema_fields.get(field_name, {})
        return field_def.get("default_value")

    def get_processing_log(self) -> StructuredProcessingLog:
        """
        Get the processing log for schema compliance operations.

        Returns:
            StructuredProcessingLog object
        """
        return self._log

    def get_schema_fields(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all schema field definitions.

        Returns:
            Dictionary of field definitions
        """
        return self._schema_fields.copy()
