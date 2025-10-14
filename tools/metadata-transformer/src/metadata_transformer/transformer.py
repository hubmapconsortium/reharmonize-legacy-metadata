"""
Core metadata transformation logic implementing the 4-phase transformation process.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from pyjsonpatch import generate_patch

from metadata_transformer.exceptions import FileProcessingError
from metadata_transformer.field_mapper import FieldMappings
from metadata_transformer.patch_applier import Patches
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.schema_applier import Schema
from metadata_transformer.value_mapper import ValueMappings


class MetadataTransformer:
    """Core metadata transformation engine."""

    def __init__(
        self,
        field_mappings: FieldMappings,
        value_mappings: ValueMappings,
        schema: Schema,
        patches: Patches,
    ) -> None:
        """
        Initialize the MetadataTransformer.

        Args:
            field_mappings: FieldMappings instance
            value_mappings: ValueMappings instance
            schema: Schema instance
            patches: Patches instance
        """
        self.field_mappings = field_mappings
        self.value_mappings = value_mappings
        self.schema = schema
        self.patches = patches

    def transform_metadata_file(self, input_file: Path) -> Dict[str, Any]:
        """
        Transform a single legacy metadata file through the 4-phase process.

        Args:
            input_file: Path to the legacy metadata JSON file

        Returns:
            Dictionary containing migrated_metadata and processing_log

        Raises:
            FileProcessingError: If file can't be processed
        """
        # File processing info moved to stdout - handled by CLI

        # Load legacy metadata from file
        loaded_object = self._load_metadata(input_file)

        # Extract original metadata for transformation and JSON patch generation
        legacy_metadata = loaded_object.get("metadata", {})

        # Transform the metadata
        try:
            transformed_metadata, json_patches, transformation_log = self._transform_metadata(legacy_metadata)
        except Exception as e:
            # Error handling moved to stdout - handled by CLI
            raise FileProcessingError(
                f"Failed to transform metadata in {input_file}: {e}"
            )

        # File processing completion info moved to stdout - handled by CLI

        # Build output result using original data as base
        output = loaded_object.copy()

        # Sort JSON patches for consistency
        sorted_json_patches = self._sort_patches(json_patches)

        output["modified_metadata"] = transformed_metadata
        output["json_patch"] = sorted_json_patches
        output["processing_log"] = transformation_log.to_dict()

        return output

    def _load_metadata(self, input_file: Path) -> Dict[str, Any]:
        """
        Load metadata from JSON file.

        Args:
            input_file: Path to the input file

        Returns:
            Metadata dictionary

        Raises:
            FileProcessingError: If file can't be loaded or is invalid
        """
        if not input_file.exists():
            raise FileProcessingError(f"Input file not found: {input_file}")

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise FileProcessingError(f"Invalid JSON in {input_file}: {e}")
        except Exception as e:
            raise FileProcessingError(f"Error reading {input_file}: {e}")

        # Validate data structure - must be a dictionary
        if not isinstance(data, dict):
            raise FileProcessingError(
                f"Input file must contain JSON object: {input_file}"
            )

        return data

    def _transform_metadata(self, legacy_metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]], StructuredProcessingLog]:
        """
        Transform metadata through the 4-phase process.

        Args:
            legacy_metadata: Legacy metadata dictionary

        Returns:
            Tuple of (transformed metadata dictionary, list of JSON patch operations, merged processing log)
        """
        all_patches = []

        # Phase 0: Conditional Patching
        patched_metadata, patch_applier_log = self._phase0_conditional_patching(legacy_metadata)
        phase0_patch = generate_patch(legacy_metadata, patched_metadata)
        all_patches.extend(phase0_patch)

        # Phase 1: Field Mapping
        field_mapped_metadata, field_mapping_log = self._phase1_field_mapping(patched_metadata)
        phase1_patch = generate_patch(patched_metadata, field_mapped_metadata)
        all_patches.extend(phase1_patch)

        # Phase 2: Value Mapping
        value_mapped_metadata, value_mapping_log = self._phase2_value_mapping(field_mapped_metadata)
        phase2_patch = generate_patch(field_mapped_metadata, value_mapped_metadata)
        all_patches.extend(phase2_patch)

        # Phase 3: Schema Compliance
        schema_compliant_metadata, schema_compliance_log = self._phase3_schema_compliance(value_mapped_metadata)
        phase3_patch = generate_patch(value_mapped_metadata, schema_compliant_metadata)
        all_patches.extend(phase3_patch)

        # Merge logs from all phases
        combined_log = StructuredProcessingLog()
        combined_log.merge_with(patch_applier_log)
        combined_log.merge_with(field_mapping_log)
        combined_log.merge_with(value_mapping_log)
        combined_log.merge_with(schema_compliance_log)

        return schema_compliant_metadata, all_patches, combined_log

    def _phase0_conditional_patching(self, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], StructuredProcessingLog]:
        """
        Phase 0: Apply conditional patches to metadata before field mapping.

        Args:
            metadata: Legacy metadata dictionary

        Returns:
            Metadata with applicable patches applied and the processing log
        """
        patch_applier_log = StructuredProcessingLog()
        patch_applier = self.patches.get_applier(patch_applier_log)

        patched_metadata = patch_applier.apply_patches(metadata)

        return patched_metadata, patch_applier_log

    def _phase1_field_mapping(self, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], StructuredProcessingLog]:
        """
        Phase 1: Apply field name mappings to transform legacy field names.

        Args:
            metadata: Legacy metadata dictionary

        Returns:
            Metadata with mapped field names and the processing log
        """
        field_mapping_log = StructuredProcessingLog()
        field_mapper = self.field_mappings.get_mapper(field_mapping_log)

        mapped_metadata: Dict[str, Any] = {}

        for legacy_field, value in metadata.items():
            target_field = field_mapper.map_field(legacy_field)

            if target_field is not None:
                if target_field in mapped_metadata:
                    # Multiple legacy fields map to same target - keep existing value
                    pass
                else:
                    mapped_metadata[target_field] = value
                    if legacy_field != target_field: # Only log when legacy_field maps to a different field
                        field_mapper.log_field_mapping(legacy_field, target_field)
            else:
                # No mapping found - keep original field name
                mapped_metadata[legacy_field] = value

        return mapped_metadata, field_mapping_log

    def _phase2_value_mapping(self, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], StructuredProcessingLog]:
        """
        Phase 2: Apply value mappings to transform field values.

        Args:
            metadata: Metadata with field names already mapped

        Returns:
            Metadata with mapped values and the processing log
        """
        value_mapping_log = StructuredProcessingLog()
        value_mapper = self.value_mappings.get_mapper(value_mapping_log)

        value_mapped_metadata = {}

        for field_name, value in metadata.items():
            mapped_value = value_mapper.map_value(field_name, value)
            value_mapped_metadata[field_name] = mapped_value

        return value_mapped_metadata, value_mapping_log

    def _phase3_schema_compliance(self, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], StructuredProcessingLog]:
        """
        Phase 3: Ensure metadata complies with target schema.

        Args:
            metadata: Metadata with field and value mappings applied

        Returns:
            Schema-compliant metadata and the processing log
        """
        schema_applier_log = StructuredProcessingLog()
        schema_applier = self.schema.get_applier(schema_applier_log)

        compliant_metadata = schema_applier.apply_schema(metadata)

        return compliant_metadata, schema_applier_log

    def _sort_patches(self, patches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort JSON Patch operations for consistency.

        Sorts by operation type, path, from field (for move ops), and full JSON.
        This ensures deterministic ordering for the patch operations.

        Args:
            patches: List of JSON Patch operations

        Returns:
            Sorted list of JSON Patch operations
        """
        return sorted(
            patches,
            key=lambda x: (
                x.get('op', ''),
                x.get('path', ''),
                x.get('from', ''),  # Include 'from' field for move operations
                json.dumps(x, sort_keys=True)
            )
        )

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for transformation operations.

        Returns:
            StructuredProcessingLog object
        """
        return self.structured_log
