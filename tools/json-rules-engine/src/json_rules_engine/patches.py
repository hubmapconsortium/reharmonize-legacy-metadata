"""
Patch loading and validation functionality.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from json_rules_engine.exceptions import PatchError

if TYPE_CHECKING:
    from json_rules_engine.applier import PatchApplier


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

    def load_patch_dir(self, patches_dir: Path) -> None:
        """
        Load all JSON patch files from the specified directory recursively.

        Args:
            patches_dir: Path to directory containing patch JSON files

        Raises:
            PatchError: If directory doesn't exist or files can't be processed
        """
        if not patches_dir.exists():
            raise PatchError(f"Patches directory not found: {patches_dir}")

        if not patches_dir.is_dir():
            raise PatchError(f"Path is not a directory: {patches_dir}")

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
            PatchError: If file doesn't exist or can't be processed
        """
        if not patch_file.exists():
            raise PatchError(f"Patch file not found: {patch_file}")

        if not patch_file.is_file():
            raise PatchError(f"Path is not a file: {patch_file}")

        self._load_patch_file(patch_file)

    def _load_patch_file(self, patch_file: Path) -> None:
        """
        Load patches from a single file into the patches list.

        Args:
            patch_file: Path to the JSON patch file

        Raises:
            PatchError: If file can't be read or parsed
        """
        try:
            with open(patch_file, "r", encoding="utf-8") as f:
                patch_data = json.load(f)
        except json.JSONDecodeError as e:
            raise PatchError(f"Invalid JSON in {patch_file}: {e}")
        except Exception as e:
            raise PatchError(f"Error reading {patch_file}: {e}")

        if not isinstance(patch_data, list):
            raise PatchError(f"Patch file must contain a JSON array: {patch_file}")

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
            PatchError: If patch structure is invalid
        """
        if not isinstance(patch, dict):
            raise PatchError(f"Patch {index} in {file_path} must be an object")

        if "when" not in patch or "then" not in patch:
            raise PatchError(
                f"Patch {index} in {file_path} must have 'when' and 'then' keys"
            )

        if not isinstance(patch["when"], dict):
            raise PatchError(f"Patch {index} in {file_path}: 'when' must be an object")

        if not isinstance(patch["then"], dict):
            raise PatchError(f"Patch {index} in {file_path}: 'then' must be an object")

        # Validate when clause structure
        self._validate_when_clause(patch["when"], f"Patch {index} in {file_path}")

    def _validate_when_clause(self, when_clause: Dict[str, Any], context: str) -> None:
        """
        Recursively validate when clause structure.

        Args:
            when_clause: The when clause to validate
            context: Context string for error messages

        Raises:
            PatchError: If when clause structure is invalid
        """
        if not when_clause:
            # Empty when clause is allowed (patch always applies)
            return

        for key in when_clause:
            if key not in ["__must__", "__should__"]:
                raise PatchError(
                    f"{context}: 'when' can only contain '__must__' and/or "
                    f"'__should__' keys, found '{key}'"
                )

            clause = when_clause[key]

            # Only accept array format
            if not isinstance(clause, list):
                raise PatchError(
                    f"{context}: '{key}' must be an array, got {type(clause).__name__}"
                )

            # Validate each item in the array
            for i, item in enumerate(clause):
                if not isinstance(item, dict):
                    raise PatchError(
                        f"{context}.{key}[{i}] must be an object, "
                        f"got {type(item).__name__}"
                    )

                # Check if nested structure
                if "__must__" in item or "__should__" in item:
                    # Recursively validate nested structure
                    self._validate_when_clause(item, f"{context}.{key}[{i}]")
                # Otherwise it's a simple field-value dict
                # (no further validation needed)

    def get_applier(self) -> "PatchApplier":
        """
        Create a PatchApplier instance with the loaded patches.

        This factory method ensures immutability - each transformation gets its own
        applier instance with an isolated copy of patches.

        Returns:
            New PatchApplier instance with patches
        """
        # Import here to avoid circular dependency
        from json_rules_engine.applier import PatchApplier

        return PatchApplier(self._patches.copy())

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
