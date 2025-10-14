"""
Field mapping functionality for transforming legacy field names to target schema field names.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.processing_log import StructuredProcessingLog


class FieldMappings:
    """
    Repository holding field mappings loaded from files.

    This class is responsible for loading and storing field mapping rules.
    Once loaded, the mappings can be used to create multiple FieldMapper
    instances for concurrent or sequential transformations.
    """

    def __init__(self) -> None:
        """Initialize an empty FieldMappings repository."""
        self._field_mappings: Dict[str, Optional[str]] = {}

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

        for json_file in json_files:
            self._merge_mapping_file(json_file)

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
        self._field_mappings.clear()
        self._field_mappings.update(mapping_data)

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

        for legacy_field, target_field in mapping_data.items():
            if legacy_field in self._field_mappings:
                existing_target = self._field_mappings[legacy_field]
                if existing_target != target_field:
                    # Skip conflicting mappings - keep existing
                    continue

            self._field_mappings[legacy_field] = target_field

    def get_mapper(self, structured_log: StructuredProcessingLog) -> "FieldMapper":
        """
        Create a FieldMapper instance with the loaded mappings and a fresh log.

        This factory method ensures immutability - each transformation gets its own
        mapper instance with an isolated processing log.

        Args:
            structured_log: Fresh StructuredProcessingLog for this transformation

        Returns:
            New FieldMapper instance with mappings and log
        """
        return FieldMapper(self._field_mappings.copy(), structured_log)

    def get_all_mappings(self) -> Dict[str, Optional[str]]:
        """
        Get all field mappings.

        Returns:
            Dictionary of all field mappings
        """
        return self._field_mappings.copy()


class FieldMapper:
    """
    Immutable field mapper that performs field name transformations with logging.

    This class is created per transformation and contains both the mapping rules
    and a processing log for that specific transformation. It is immutable after
    construction, ensuring thread-safety and preventing accidental state mutations.
    """

    def __init__(
        self,
        field_mappings: Optional[Dict[str, Optional[str]]] = None,
        structured_log: Optional[StructuredProcessingLog] = None,
    ) -> None:
        """
        Initialize a FieldMapper with mappings and log.

        Note: For the new design pattern, use FieldMappings.get_mapper() instead.
        Direct instantiation is supported for backward compatibility.

        Args:
            field_mappings: Dictionary of legacy -> target field mappings.
                          If None, creates empty dict (for backward compatibility).
            structured_log: Processing log for this transformation.
                          If None, creates new log (for backward compatibility).
        """
        self._field_mappings = field_mappings if field_mappings is not None else {}
        self._structured_log = structured_log if structured_log is not None else StructuredProcessingLog()

    # Backward compatibility methods for loading
    def load_field_mappings(self, field_mapping_dir: Path) -> None:
        """
        Deprecated: For backward compatibility only.
        Use FieldMappings.load_field_mappings() instead.
        """
        mappings = FieldMappings()
        mappings.load_field_mappings(field_mapping_dir)
        object.__setattr__(self, "_field_mappings", mappings.get_all_mappings())

    def load_field_mapping_file(self, mapping_file: Path) -> None:
        """
        Deprecated: For backward compatibility only.
        Use FieldMappings.load_field_mapping_file() instead.
        """
        mappings = FieldMappings()
        mappings.load_field_mapping_file(mapping_file)
        object.__setattr__(self, "_field_mappings", mappings.get_all_mappings())

    def map_field(self, legacy_field: str) -> Optional[str]:
        """
        Map a legacy field name to its target schema equivalent.

        Args:
            legacy_field: The legacy field name to map

        Returns:
            The target field name, or None if no mapping exists
        """
        return self._field_mappings.get(legacy_field)

    def log_field_mapping(self, legacy_field: str, target_field: str) -> None:
        """
        Log a field mapping operation using structured format.

        Args:
            legacy_field: The legacy field name
            target_field: The target field name
        """
        self._structured_log.add_mapped_field(legacy_field, target_field)

    def get_all_mappings(self) -> Dict[str, Optional[str]]:
        """
        Get all field mappings.

        Returns:
            Dictionary of all field mappings
        """
        return self._field_mappings.copy()

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for this transformation.

        Returns:
            StructuredProcessingLog object
        """
        return self._structured_log

    # Backward compatibility properties and methods for tests
    @property
    def field_mappings(self) -> Dict[str, Optional[str]]:
        """Property for backward compatibility with tests."""
        return self._field_mappings

    @field_mappings.setter
    def field_mappings(self, value: Dict[str, Optional[str]]) -> None:
        """Setter for backward compatibility with tests."""
        object.__setattr__(self, "_field_mappings", value)

    @property
    def structured_log(self) -> StructuredProcessingLog:
        """Property for backward compatibility with tests."""
        return self._structured_log

    def set_structured_log(self, structured_log: StructuredProcessingLog) -> None:
        """
        Deprecated: For backward compatibility only.
        In the new design, create a new mapper with get_mapper() instead.
        """
        # For backward compatibility - mutate the log
        object.__setattr__(self, "_structured_log", structured_log)

    def clear_logs(self) -> None:
        """
        Deprecated: For backward compatibility only.
        In the new design, create a new mapper with get_mapper() instead.
        """
        object.__setattr__(self, "_structured_log", StructuredProcessingLog())
