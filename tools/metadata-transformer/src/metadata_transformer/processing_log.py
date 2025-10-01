"""
Structured processing log models for metadata transformation operations.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Dict, List, Optional


@dataclass
class UnmappedValueEntry:
    """Represents a value that couldn't be mapped automatically."""

    field: str
    value: Any
    permissible_values: List[str] = dataclass_field(default_factory=list)


@dataclass
class AppliedPatchEntry:
    """Represents a patch that was applied to the metadata."""

    field: str
    value: Any
    conditions: Dict[str, Any] = dataclass_field(default_factory=dict)


@dataclass
class StructuredProcessingLog:
    """Structured processing log for metadata transformation operations."""

    field_mappings: Dict[str, str] = dataclass_field(default_factory=dict)
    ambiguous_mappings: List[UnmappedValueEntry] = dataclass_field(default_factory=list)
    value_mappings: Dict[str, Dict[str, Any]] = dataclass_field(default_factory=dict)
    metadata_patches: List[AppliedPatchEntry] = dataclass_field(default_factory=list)
    excluded_data: Dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization."""
        return {
            "field_mappings": self.field_mappings,
            "value_mappings": self.value_mappings,
            "ambiguous_mappings": [
                {
                    "field": entry.field,
                    "value": entry.value,
                    "permissible_values": entry.permissible_values,
                }
                for entry in self.ambiguous_mappings
            ],
            "excluded_data": self.excluded_data,
            "metadata_patches": [
                {
                    "field": entry.field,
                    "value": entry.value,
                    "conditions": entry.conditions,
                }
                for entry in self.metadata_patches
            ],
        }

    def add_unmapped_field_with_value(self, field_name: str, value: Any) -> None:
        """Add a field that couldn't be mapped along with its value."""
        self.excluded_data[field_name] = value

    def add_mapped_field(self, legacy_field: str, target_field: str) -> None:
        """Add a successful field mapping."""
        self.field_mappings[legacy_field] = target_field

    def add_unmapped_value(
        self,
        field_name: str,
        value: Any,
        permissible_values: Optional[List[str]] = None,
    ) -> None:
        """Add a value that couldn't be mapped automatically."""
        if permissible_values is None:
            permissible_values = []

        entry = UnmappedValueEntry(
            field=field_name,
            value=value,
            permissible_values=permissible_values,
        )
        self.ambiguous_mappings.append(entry)

    def add_mapped_value(
        self, legacy_value: Any, target_value: Any, origin_field: str
    ) -> None:
        """Add a successful value mapping."""
        legacy_value_str = str(legacy_value)

        # Initialize field dictionary if it doesn't exist
        if origin_field not in self.value_mappings:
            self.value_mappings[origin_field] = {}

        # Add the value mapping under the field, preserving None values
        self.value_mappings[origin_field][legacy_value_str] = target_value

    def add_applied_patch(
        self, field_name: str, field_value: Any, conditions: Dict[str, Any]
    ) -> None:
        """Add a patch that was applied to the metadata."""
        entry = AppliedPatchEntry(
            field=field_name, value=field_value, conditions=conditions
        )
        self.metadata_patches.append(entry)

    def merge_with(self, other: "StructuredProcessingLog") -> None:
        """Merge another log into this one."""
        # Merge field mappings
        self.field_mappings.update(other.field_mappings)

        # Merge ambiguous mappings
        self.ambiguous_mappings.extend(other.ambiguous_mappings)

        # Merge value mappings
        self.value_mappings.update(other.value_mappings)

        # Merge metadata patches
        self.metadata_patches.extend(other.metadata_patches)

        # Merge excluded data
        self.excluded_data.update(other.excluded_data)
