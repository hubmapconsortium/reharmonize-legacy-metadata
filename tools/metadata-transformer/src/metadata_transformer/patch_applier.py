"""
Conditional patch application functionality for applying patches to metadata before field mapping.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from metadata_transformer.exceptions import FieldMappingError
from metadata_transformer.processing_log import StructuredProcessingLog


class Patches:
    """
    Repository holding patches loaded from files.

    This class is responsible for loading and storing patch rules.
    Once loaded, the patches can be used to create multiple PatchApplier
    instances for concurrent or sequential transformations.
    """

    def __init__(self) -> None:
        """Initialize an empty Patches repository."""
        self._patches: List[Dict[str, Any]] = []

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

    def load_patch_file(self, patch_file: Path) -> None:
        """
        Load patches from a single file.

        Args:
            patch_file: Path to a JSON patch file

        Raises:
            FieldMappingError: If file doesn't exist or can't be processed
        """
        if not patch_file.exists():
            raise FieldMappingError(f"Patch file not found: {patch_file}")

        if not patch_file.is_file():
            raise FieldMappingError(f"Path is not a file: {patch_file}")

        self._load_patch_file(patch_file)

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
            self._validate_patch_structure(patch, i, patch_file)

            # Add source file info for debugging
            patch_with_source = patch.copy()
            patch_with_source["_source_file"] = str(patch_file)
            self._patches.append(patch_with_source)

    def _validate_patch_structure(
        self, patch: Dict[str, Any], index: int, file_path: Path
    ) -> None:
        """
        Validate patch structure including nested conditions.

        Args:
            patch: The patch object to validate
            index: The index of the patch in the array
            file_path: The file path for error messages

        Raises:
            FieldMappingError: If patch structure is invalid
        """
        if not isinstance(patch, dict):
            raise FieldMappingError(f"Patch {index} in {file_path} must be an object")

        if "when" not in patch or "then" not in patch:
            raise FieldMappingError(
                f"Patch {index} in {file_path} must have 'when' and 'then' keys"
            )

        if not isinstance(patch["when"], dict):
            raise FieldMappingError(
                f"Patch {index} in {file_path}: 'when' must be an object"
            )

        if not isinstance(patch["then"], dict):
            raise FieldMappingError(
                f"Patch {index} in {file_path}: 'then' must be an object"
            )

        # Validate when clause structure
        self._validate_when_clause(patch["when"], f"Patch {index} in {file_path}")

    def _validate_when_clause(self, when_clause: Dict[str, Any], context: str) -> None:
        """
        Recursively validate when clause structure.

        Args:
            when_clause: The when clause to validate
            context: Context string for error messages

        Raises:
            FieldMappingError: If when clause structure is invalid
        """
        if not when_clause:
            # Empty when clause is allowed (patch always applies)
            return

        for key in when_clause:
            if key not in ["__must__", "__should__"]:
                raise FieldMappingError(
                    f"{context}: 'when' can only contain '__must__' and/or '__should__' keys, found '{key}'"
                )

            clause = when_clause[key]

            # Only accept array format
            if not isinstance(clause, list):
                raise FieldMappingError(
                    f"{context}: '{key}' must be an array, got {type(clause).__name__}"
                )

            # Validate each item in the array
            for i, item in enumerate(clause):
                if not isinstance(item, dict):
                    raise FieldMappingError(
                        f"{context}.{key}[{i}] must be an object, got {type(item).__name__}"
                    )

                # Check if nested structure
                if "__must__" in item or "__should__" in item:
                    # Recursively validate nested structure
                    self._validate_when_clause(item, f"{context}.{key}[{i}]")
                # Otherwise it's a simple field-value dict (no further validation needed)

    def get_applier(self, structured_log: StructuredProcessingLog) -> "PatchApplier":
        """
        Create a PatchApplier instance with the loaded patches and a fresh log.

        This factory method ensures immutability - each transformation gets its own
        applier instance with an isolated processing log.

        Args:
            structured_log: Fresh StructuredProcessingLog for this transformation

        Returns:
            New PatchApplier instance with patches and log
        """
        return PatchApplier(self._patches.copy(), structured_log)

    def get_all_patches(self) -> List[Dict[str, Any]]:
        """
        Get all loaded patches.

        Returns:
            List of all patches
        """
        return self._patches.copy()

    def get_loaded_patches_count(self) -> int:
        """
        Get the number of loaded patches.

        Returns:
            Number of patches loaded
        """
        return len(self._patches)


class PatchApplier:
    """
    Immutable patch applier that applies conditional patches with logging.

    This class is created per transformation and contains both the patch rules
    and a processing log for that specific transformation. It is immutable after
    construction, ensuring thread-safety and preventing accidental state mutations.
    """

    def __init__(
        self,
        patches: Optional[List[Dict[str, Any]]] = None,
        structured_log: Optional[StructuredProcessingLog] = None,
    ) -> None:
        """
        Initialize a PatchApplier with patches and log.

        Note: For the new design pattern, use Patches.get_applier() instead.
        Direct instantiation is supported for backward compatibility.

        Args:
            patches: List of patch rules.
                    If None, creates empty list (for backward compatibility).
            structured_log: Processing log for this transformation.
                          If None, creates new log (for backward compatibility).
        """
        self._patches = patches if patches is not None else []
        self._structured_log = structured_log if structured_log is not None else StructuredProcessingLog()

    def apply_patches(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all loaded patches to the metadata based on their conditions.

        Args:
            metadata: The metadata object to apply patches to

        Returns:
            Modified metadata with applicable patches applied
        """
        patched_metadata = metadata.copy()

        for patch in self._patches:
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
        must_result = True
        should_result = True

        if "__must__" in when_clause:
            must_result = self._evaluate_must(when_clause["__must__"], metadata)

        if "__should__" in when_clause:
            should_result = self._evaluate_should(when_clause["__should__"], metadata)

        # If neither present, patch always applies
        if "__must__" not in when_clause and "__should__" not in when_clause:
            return True

        return must_result and should_result

    def _evaluate_must(
        self, must_clause: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> bool:
        """
        Evaluate '__must__' clause with AND logic.
        All items in the array must evaluate to true.

        Args:
            must_clause: List of condition items
            metadata: The metadata to evaluate against

        Returns:
            True if all conditions match, False otherwise
        """
        if not isinstance(must_clause, list):
            return False

        # Empty array: all() returns True (vacuous truth)
        return all(self._evaluate_item(item, metadata) for item in must_clause)

    def _evaluate_should(
        self, should_clause: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> bool:
        """
        Evaluate '__should__' clause with OR logic.
        At least one item in the array must evaluate to true.

        Args:
            should_clause: List of condition items
            metadata: The metadata to evaluate against

        Returns:
            True if any condition matches, False otherwise
        """
        if not isinstance(should_clause, list):
            return False

        # Empty array: any() returns False
        return any(self._evaluate_item(item, metadata) for item in should_clause)

    def _evaluate_item(self, item: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """
        Evaluate a single item from a __must__ or __should__ array.

        Args:
            item: Either a nested structure with __must__/__should__ keys,
                  or a simple field-value dict
            metadata: The metadata to evaluate against

        Returns:
            True if item conditions match, False otherwise
        """
        # Check if this is a nested logical structure
        if "__must__" in item or "__should__" in item:
            # Recursively evaluate the nested structure
            return self._evaluate_conditions(item, metadata)

        # Simple field-value dict - all fields must match (implicit AND)
        return all(metadata.get(k) == v for k, v in item.items())

    def _log_patch_application(self, patch: Dict[str, Any], source_file: str) -> None:
        """
        Log the application of a patch using structured format.

        Args:
            patch: The patch that was applied
            source_file: The source file the patch came from (not logged)
        """
        # Log each field that was patched
        for field_name, field_value in patch["then"].items():
            self._structured_log.add_applied_patch(
                field_name=field_name, field_value=field_value, conditions=patch["when"]
            )

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for patch operations.

        Returns:
            StructuredProcessingLog object
        """
        return self._structured_log

    def get_all_patches(self) -> List[Dict[str, Any]]:
        """
        Get all patches.

        Returns:
            List of all patches
        """
        return self._patches.copy()

    def get_loaded_patches_count(self) -> int:
        """
        Get the number of loaded patches.

        Returns:
            Number of patches loaded
        """
        return len(self._patches)
