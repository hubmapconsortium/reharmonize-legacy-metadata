"""
Conditional patch application functionality.
"""

from typing import Any, Dict, List


class PatchApplier:
    """
    Immutable patch applier that applies conditional patches.

    This class is created per transformation and contains the patch rules.
    It is immutable after construction, ensuring thread-safety and preventing
    accidental state mutations.
    """

    def __init__(self, patches: List[Dict[str, Any]]) -> None:
        """
        Initialize a PatchApplier with patches.

        Args:
            patches: List of patch rules.
        """
        self._patches = patches

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
