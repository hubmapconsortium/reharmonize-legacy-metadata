"""
Field mapping functionality for transforming legacy field names to target schema field names.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.processing_log import StructuredProcessingLog


class FieldMapper:
    """Handles loading and merging of field mapping files."""

    def __init__(self) -> None:
        """Initialize the FieldMapper."""
        self.field_mappings: Dict[str, Optional[str]] = {}
        self.structured_log: StructuredProcessingLog = StructuredProcessingLog()

    def load_field_mappings(self, field_mapping_dir: Path) -> None:
        """
        Load and merge all JSON field mapping files from the specified directory.

        Args:
            field_mapping_dir: Path to directory containing field mapping JSON files

        Raises:
            FieldMappingError: If directory doesn't exist or files can't be processed
        """
        if not field_mapping_dir.exists():
            raise FieldMappingError(
                f"Field mapping directory not found: {field_mapping_dir}"
            )

        if not field_mapping_dir.is_dir():
            raise FieldMappingError(f"Path is not a directory: {field_mapping_dir}")

        json_files = list(field_mapping_dir.glob("*.json"))
        if not json_files:
            raise FieldMappingError(f"No JSON files found in: {field_mapping_dir}")

        # File loading info moved to stdout - handled by CLI

        for json_file in json_files:
            self._merge_mapping_file(json_file)

        # File loading completion info moved to stdout - handled by CLI

    def load_field_mapping_file(self, mapping_file: Path) -> None:
        """
        Load field mappings from a single JSON file.

        Args:
            mapping_file: Path to the JSON field mapping file

        Raises:
            FieldMappingError: If file doesn't exist, isn't a file, or can't be processed
        """
        if not mapping_file.exists():
            raise FieldMappingError(f"Field mapping file not found: {mapping_file}")

        if not mapping_file.is_file():
            raise FieldMappingError(f"Path is not a file: {mapping_file}")

        if mapping_file.suffix.lower() != ".json":
            raise FieldMappingError(
                f"Field mapping file must be a JSON file: {mapping_file}"
            )

        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
        except json.JSONDecodeError as e:
            raise FieldMappingError(f"Invalid JSON in {mapping_file}: {e}")
        except Exception as e:
            raise FieldMappingError(f"Error reading {mapping_file}: {e}")

        if not isinstance(mapping_data, dict):
            raise FieldMappingError(
                f"Mapping file must contain a JSON object: {mapping_file}"
            )

        # Clear existing mappings and load new ones
        self.field_mappings.clear()
        self.field_mappings.update(mapping_data)

    def _merge_mapping_file(self, mapping_file: Path) -> None:
        """
        Merge a single mapping file into the master field mappings.

        Args:
            mapping_file: Path to the JSON mapping file

        Raises:
            FieldMappingError: If file can't be read or parsed
        """
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
        except json.JSONDecodeError as e:
            raise FieldMappingError(f"Invalid JSON in {mapping_file}: {e}")
        except Exception as e:
            raise FieldMappingError(f"Error reading {mapping_file}: {e}")

        if not isinstance(mapping_data, dict):
            raise FieldMappingError(
                f"Mapping file must contain a JSON object: {mapping_file}"
            )

        conflicts = []
        new_mappings = 0

        for legacy_field, target_field in mapping_data.items():
            if legacy_field in self.field_mappings:
                existing_target = self.field_mappings[legacy_field]
                if existing_target != target_field:
                    conflicts.append(
                        {
                            "field": legacy_field,
                            "existing_target": existing_target,
                            "new_target": target_field,
                            "source_file": str(mapping_file.name),
                        }
                    )
                    # Field mapping conflicts moved to stdout - handled by CLI
                    continue

            self.field_mappings[legacy_field] = target_field
            new_mappings += 1

        # File processing info moved to stdout - handled by CLI

        # Conflicts summary moved to stdout - handled by CLI

    def map_field(self, legacy_field: str) -> Optional[str]:
        """
        Map a legacy field name to its target schema equivalent.

        Args:
            legacy_field: The legacy field name to map

        Returns:
            The target field name, or None if no mapping exists
        """
        return self.field_mappings.get(legacy_field)

    def log_field_mapping(self, legacy_field: str, target_field: str) -> None:
        """
        Log a field mapping operation using structured format.

        Args:
            legacy_field: The legacy field name
            target_field: The target field name
        """
        self.structured_log.add_mapped_field(legacy_field, target_field)

    def get_all_mappings(self) -> Dict[str, Optional[str]]:
        """
        Get all field mappings.

        Returns:
            Dictionary of all field mappings
        """
        return self.field_mappings.copy()

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for field mapping operations.

        Returns:
            StructuredProcessingLog object
        """
        return self.structured_log

    def clear_logs(self) -> None:
        """Clear structured processing log."""
        self.structured_log = StructuredProcessingLog()
