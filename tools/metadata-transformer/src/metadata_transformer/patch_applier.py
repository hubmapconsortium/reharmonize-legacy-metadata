"""
Conditional patch application functionality for applying patches to metadata before field mapping.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.processing_log import StructuredProcessingLog


class PatchApplier:
    """Handles loading and application of conditional patches to metadata."""

    def __init__(self) -> None:
        """Initialize the PatchApplier."""
        self.patches: List[Dict[str, Any]] = []
        self.structured_log: StructuredProcessingLog = StructuredProcessingLog()

    def load_patches(self, patches_dir: Path) -> None:
        """
        Load all JSON patch files from the specified directory recursively.

        Args:
            patches_dir: Path to directory containing patch JSON files

        Raises:
            FieldMappingError: If directory doesn't exist or files can't be processed
        """
        if not patches_dir.exists():
            raise FieldMappingError(f"Patches directory not found: {patches_dir}")

        if not patches_dir.is_dir():
            raise FieldMappingError(f"Path is not a directory: {patches_dir}")

        # Find all JSON files recursively
        json_files = list(patches_dir.rglob("*.json"))
        if not json_files:
            # No patches is OK - just continue without applying any
            return

        # Sort files for consistent processing order
        json_files.sort()

        for json_file in json_files:
            self._load_patch_file(json_file)

    def _load_patch_file(self, patch_file: Path) -> None:
        """
        Load patches from a single file into the patches list.

        Args:
            patch_file: Path to the JSON patch file

        Raises:
            FieldMappingError: If file can't be read or parsed
        """
        try:
            with open(patch_file, "r", encoding="utf-8") as f:
                patch_data = json.load(f)
        except json.JSONDecodeError as e:
            raise FieldMappingError(f"Invalid JSON in {patch_file}: {e}")
        except Exception as e:
            raise FieldMappingError(f"Error reading {patch_file}: {e}")

        if not isinstance(patch_data, list):
            raise FieldMappingError(
                f"Patch file must contain a JSON array: {patch_file}"
            )

        # Validate and add patches
        for i, patch in enumerate(patch_data):
            if not isinstance(patch, dict):
                raise FieldMappingError(f"Patch {i} in {patch_file} must be an object")

            if "when" not in patch or "then" not in patch:
                raise FieldMappingError(
                    f"Patch {i} in {patch_file} must have 'when' and 'then' keys"
                )

            if not isinstance(patch["when"], dict) or not isinstance(
                patch["then"], dict
            ):
                raise FieldMappingError(
                    f"Patch {i} in {patch_file}: 'when' and 'then' must be objects"
                )

            # Add source file info for debugging
            patch_with_source = patch.copy()
            patch_with_source["_source_file"] = str(patch_file)
            self.patches.append(patch_with_source)

    def apply_patches(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all loaded patches to the metadata based on their conditions.

        Args:
            metadata: The metadata object to apply patches to

        Returns:
            Modified metadata with applicable patches applied
        """
        patched_metadata = metadata.copy()

        for patch in self.patches:
            if self._evaluate_conditions(patch["when"], metadata):
                # Apply the patch
                for field_name, field_value in patch["then"].items():
                    patched_metadata[field_name] = field_value

                # Log the patch application
                source_file = patch.get("_source_file", "unknown")
                self._log_patch_application(patch, source_file)

        return patched_metadata

    def _evaluate_conditions(
        self, when_clause: Dict[str, Any], metadata: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if the when clause conditions match the metadata.

        Args:
            when_clause: The 'when' section of a patch
            metadata: The metadata to evaluate against

        Returns:
            True if conditions are met, False otherwise
        """
        must_conditions = when_clause.get("must", {})
        should_conditions = when_clause.get("should", {})

        # If neither must nor should are present, patch always applies
        if not must_conditions and not should_conditions:
            return True

        # Check must conditions (AND logic - all must be true)
        must_result = True
        if must_conditions:
            must_result = self._evaluate_must_conditions(must_conditions, metadata)

        # Check should conditions (OR logic - any must be true)
        should_result = True
        if should_conditions:
            should_result = self._evaluate_should_conditions(
                should_conditions, metadata
            )

        # Both groups must pass if present
        return must_result and should_result

    def _evaluate_must_conditions(
        self, must_conditions: Dict[str, Any], metadata: Dict[str, Any]
    ) -> bool:
        """
        Evaluate 'must' conditions using AND logic.

        Args:
            must_conditions: Dictionary of field-value pairs that must all match
            metadata: The metadata to evaluate against

        Returns:
            True if all conditions match, False otherwise
        """
        for field_name, expected_value in must_conditions.items():
            actual_value = metadata.get(field_name)
            if actual_value != expected_value:
                return False
        return True

    def _evaluate_should_conditions(
        self, should_conditions: Dict[str, Any], metadata: Dict[str, Any]
    ) -> bool:
        """
        Evaluate 'should' conditions using OR logic.

        Args:
            should_conditions: Dictionary of field-value pairs where any must match
            metadata: The metadata to evaluate against

        Returns:
            True if any condition matches, False otherwise
        """
        for field_name, expected_value in should_conditions.items():
            actual_value = metadata.get(field_name)
            if actual_value == expected_value:
                return True
        return False

    def _log_patch_application(self, patch: Dict[str, Any], source_file: str) -> None:
        """
        Log the application of a patch using structured format.

        Args:
            patch: The patch that was applied
            source_file: The source file the patch came from (not logged)
        """
        # Log each field that was patched
        for field_name, field_value in patch["then"].items():
            self.structured_log.add_applied_patch(
                field_name=field_name, field_value=field_value, conditions=patch["when"]
            )

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for patch operations.

        Returns:
            StructuredProcessingLog object
        """
        return self.structured_log

    def clear_logs(self) -> None:
        """Clear structured processing log."""
        self.structured_log = StructuredProcessingLog()

    def get_loaded_patches_count(self) -> int:
        """
        Get the number of loaded patches.

        Returns:
            Number of patches loaded
        """
        return len(self.patches)
