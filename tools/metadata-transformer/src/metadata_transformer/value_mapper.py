"""
Value mapping functionality for transforming legacy field values to target schema values.
"""

import json
from pathlib import Path
from typing import Any, Dict

from metadata_transformer.exceptions import ValueMappingError
from metadata_transformer.processing_log import StructuredProcessingLog


class ValueMapper:
    """Handles loading and application of value mapping files."""

    def __init__(self) -> None:
        """Initialize the ValueMapper."""
        self.value_mappings: Dict[str, Dict[str, Any]] = {}
        self.structured_log: StructuredProcessingLog = StructuredProcessingLog()

    def load_value_mappings(self, value_mapping_dir: Path) -> None:
        """
        Load all JSON value mapping files from the specified directory.

        Args:
            value_mapping_dir: Path to directory containing value mapping JSON files

        Raises:
            ValueMappingError: If directory doesn't exist or files can't be processed
        """
        if not value_mapping_dir.exists():
            raise ValueMappingError(
                f"Value mapping directory not found: {value_mapping_dir}"
            )

        if not value_mapping_dir.is_dir():
            raise ValueMappingError(f"Path is not a directory: {value_mapping_dir}")

        json_files = list(value_mapping_dir.glob("*.json"))
        if not json_files:
            raise ValueMappingError(f"No JSON files found in: {value_mapping_dir}")

        # File loading info moved to stdout - handled by CLI

        for json_file in json_files:
            self._load_mapping_file(json_file)

        # Statistics calculation removed - not currently used
        # If needed: total_fields = len(self.value_mappings)
        # If needed: total_mappings = sum(len(m) for m in self.value_mappings.values())

    def _load_mapping_file(self, mapping_file: Path) -> None:
        """
        Load a single value mapping file.

        Args:
            mapping_file: Path to the JSON mapping file

        Raises:
            ValueMappingError: If file can't be read or parsed
        """
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueMappingError(f"Invalid JSON in {mapping_file}: {e}")
        except Exception as e:
            raise ValueMappingError(f"Error reading {mapping_file}: {e}")

        if not isinstance(mapping_data, dict):
            raise ValueMappingError(
                f"Mapping file must contain a JSON object: {mapping_file}"
            )

        file_mappings = 0
        field_name = mapping_file.stem  # Use filename without extension as field name

        # Handle nested structure where field mappings are nested under field names
        for key, value in mapping_data.items():
            if isinstance(value, dict):
                # This is a field with its value mappings
                self.value_mappings[key] = value
                file_mappings += len(value)
            else:
                # This is a direct field-value mapping, use filename as field name
                if field_name not in self.value_mappings:
                    self.value_mappings[field_name] = {}
                self.value_mappings[field_name][key] = value
                file_mappings += 1

        # File processing info moved to stdout - handled by CLI

    def map_value(self, field_name: str, legacy_value: Any) -> Any:
        """
        Map a legacy field value to its target schema equivalent.

        Args:
            field_name: The field name to look up mappings for
            legacy_value: The legacy value to map

        Returns:
            The mapped value, or the original value if no mapping exists
        """
        if field_name not in self.value_mappings:
            return legacy_value

        value_mapping = self.value_mappings[field_name]

        # Convert value to string for lookup if it's not already
        lookup_key = str(legacy_value) if legacy_value is not None else None

        if lookup_key in value_mapping:
            mapped_value = value_mapping[lookup_key]

            # Check if mapped_value is a list with multiple options
            if isinstance(mapped_value, list) and len(mapped_value) > 1:
                # Don't replace the value, keep original and log need for manual selection
                self.structured_log.add_unmapped_value(
                    field_name, legacy_value, mapped_value
                )
                return legacy_value
            else:
                # Single value or single-item list - proceed with replacement
                # If it's a single-item list, extract the single value
                if isinstance(mapped_value, list) and len(mapped_value) == 1:
                    mapped_value = mapped_value[0]

                # Add to structured log
                self.structured_log.add_mapped_value(
                    legacy_value, mapped_value, field_name
                )

                return mapped_value

        return legacy_value

    def has_mapping_for_field(self, field_name: str) -> bool:
        """
        Check if value mappings exist for a given field.

        Args:
            field_name: The field name to check

        Returns:
            True if mappings exist for the field, False otherwise
        """
        return field_name in self.value_mappings

    def get_field_mappings(self, field_name: str) -> Dict[str, Any]:
        """
        Get all value mappings for a specific field.

        Args:
            field_name: The field name to get mappings for

        Returns:
            Dictionary of value mappings for the field, empty dict if none exist
        """
        return self.value_mappings.get(field_name, {})

    def get_all_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all value mappings.

        Returns:
            Dictionary of all value mappings organized by field name
        """
        return self.value_mappings.copy()

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for value mapping operations.

        Returns:
            StructuredProcessingLog object
        """
        return self.structured_log

    def clear_logs(self) -> None:
        """Clear structured processing log."""
        self.structured_log = StructuredProcessingLog()
