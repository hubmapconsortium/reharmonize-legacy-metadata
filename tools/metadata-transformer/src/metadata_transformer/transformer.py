"""
Core metadata transformation logic implementing the 4-phase transformation process.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from metadata_transformer.exceptions import FileProcessingError
from metadata_transformer.field_mapper import FieldMapper
from metadata_transformer.patch_applier import PatchApplier
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.schema_loader import SchemaLoader
from metadata_transformer.value_mapper import ValueMapper


class MetadataTransformer:
    """Core metadata transformation engine."""

    def __init__(
        self,
        field_mapper: FieldMapper,
        value_mapper: ValueMapper,
        schema_loader: SchemaLoader,
        patch_applier: PatchApplier,
    ) -> None:
        """
        Initialize the MetadataTransformer.

        Args:
            field_mapper: Configured FieldMapper instance
            value_mapper: Configured ValueMapper instance
            schema_loader: Configured SchemaLoader instance
            patch_applier: Configured PatchApplier instance
        """
        self.field_mapper = field_mapper
        self.value_mapper = value_mapper
        self.schema_loader = schema_loader
        self.patch_applier = patch_applier
        self.structured_log: StructuredProcessingLog = StructuredProcessingLog()

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
        # Clear all processing logs to ensure clean state for each file
        self.structured_log = StructuredProcessingLog()

        # Clear component logs if they exist (handles both real and mock objects)
        if hasattr(self.field_mapper, "clear_logs"):
            self.field_mapper.clear_logs()

        if hasattr(self.value_mapper, "clear_logs"):
            self.value_mapper.clear_logs()

        if hasattr(self.patch_applier, "clear_logs"):
            self.patch_applier.clear_logs()

        # File processing info moved to stdout - handled by CLI

        # Load legacy metadata
        legacy_data = self._load_legacy_metadata(input_file)

        # Store original data structure
        original_data = self._load_original_data(input_file)

        # Process each metadata object in the file
        transformed_objects = []
        for i, legacy_object in enumerate(legacy_data):
            try:
                transformed_object = self._transform_single_object(legacy_object, i)
                transformed_objects.append(transformed_object)
            except Exception as e:
                # Error handling moved to stdout - handled by CLI
                raise FileProcessingError(
                    f"Failed to transform object {i} in {input_file}: {e}"
                )

        # File processing completion info moved to stdout - handled by CLI

        # Combine structured logs from all components
        combined_structured_log = StructuredProcessingLog()
        if hasattr(self.patch_applier, "get_structured_log"):
            patch_log = self.patch_applier.get_structured_log()
            if isinstance(patch_log, StructuredProcessingLog):
                combined_structured_log.merge_with(patch_log)
        if hasattr(self.field_mapper, "get_structured_log"):
            field_log = self.field_mapper.get_structured_log()
            if isinstance(field_log, StructuredProcessingLog):
                combined_structured_log.merge_with(field_log)
        if hasattr(self.value_mapper, "get_structured_log"):
            value_log = self.value_mapper.get_structured_log()
            if isinstance(value_log, StructuredProcessingLog):
                combined_structured_log.merge_with(value_log)
        combined_structured_log.merge_with(self.structured_log)

        # Append modified_metadata and processing_log to original structure
        # Always return single object format
        if isinstance(original_data, list):
            # For array input, use the first object as base
            result = original_data[0].copy() if original_data else {}
        else:
            # For single object input, use the original object as base
            result = original_data.copy()

        result["modified_metadata"] = (
            transformed_objects[0] if transformed_objects else {}
        )
        result["processing_log"] = combined_structured_log.to_dict()

        return result

    def _load_legacy_metadata(self, input_file: Path) -> List[Dict[str, Any]]:
        """
        Load legacy metadata from JSON file.

        Args:
            input_file: Path to the input file

        Returns:
            List of legacy metadata objects

        Raises:
            FileProcessingError: If file can't be loaded
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

        if isinstance(data, dict):
            # Single object, wrap in list
            data = [data]
        elif not isinstance(data, list):
            raise FileProcessingError(
                f"Input file must contain JSON array or object: {input_file}"
            )

        # File loading info moved to stdout - handled by CLI

        return data

    def _load_original_data(
        self, input_file: Path
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Load the original data structure from JSON file to preserve format.

        Args:
            input_file: Path to the input file

        Returns:
            Original data structure (either dict or list)

        Raises:
            FileProcessingError: If file can't be loaded
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

        # Ensure we return the expected type - validation happens in transform_metadata_file
        return data  # type: ignore

    def _transform_single_object(
        self, legacy_object: Dict[str, Any], object_index: int
    ) -> Dict[str, Any]:
        """
        Transform a single legacy metadata object through the 4-phase process.

        Args:
            legacy_object: The legacy metadata object
            object_index: Index of the object in the input file

        Returns:
            Transformed metadata object
        """
        object_id = legacy_object.get("uuid", f"object_{object_index}")

        # Object transformation start - no logging needed

        # Navigate to metadata key
        metadata_section = legacy_object.get("metadata", {})
        if not metadata_section:
            # Metadata key warnings moved to stdout - handled by CLI
            metadata_section = {}

        # Phase 0: Conditional Patching
        patched_metadata = self._phase0_conditional_patching(
            metadata_section, object_id
        )

        # Phase 1: Field Mapping
        field_mapped_metadata = self._phase1_field_mapping(patched_metadata, object_id)

        # Phase 2: Value Mapping
        value_mapped_metadata = self._phase2_value_mapping(
            field_mapped_metadata, object_id
        )

        # Phase 3: Schema Compliance
        schema_compliant_metadata = self._phase3_schema_compliance(
            value_mapped_metadata, object_id
        )

        # Phase 4 is handled by output generator

        # Object transformation complete - no logging needed

        return schema_compliant_metadata

    def _phase0_conditional_patching(
        self, metadata: Dict[str, Any], object_id: str
    ) -> Dict[str, Any]:
        """
        Phase 0: Apply conditional patches to metadata before field mapping.

        Args:
            metadata: Legacy metadata dictionary
            object_id: Identifier for the object being processed

        Returns:
            Metadata with applicable patches applied
        """
        # Phase start - no logging needed

        patched_metadata = self.patch_applier.apply_patches(metadata)

        # Phase complete - no logging needed

        return patched_metadata

    def _phase1_field_mapping(
        self, metadata: Dict[str, Any], object_id: str
    ) -> Dict[str, Any]:
        """
        Phase 1: Apply field name mappings to transform legacy field names.

        Args:
            metadata: Legacy metadata dictionary
            object_id: Identifier for the object being processed

        Returns:
            Metadata with mapped field names
        """
        # Phase start - no logging needed

        mapped_metadata: Dict[str, Any] = {}
        unmapped_fields = []

        for legacy_field, value in metadata.items():
            target_field = self.field_mapper.map_field(legacy_field)

            if target_field is not None:
                if target_field in mapped_metadata:
                    # Multiple legacy fields map to same target - this is ambiguous
                    # Ambiguous mapping - keep existing value, don't log
                    pass
                else:
                    mapped_metadata[target_field] = value
                    self.field_mapper.log_field_mapping(legacy_field, target_field)
            else:
                # No mapping found - keep original field name for now
                mapped_metadata[legacy_field] = value
                unmapped_fields.append(legacy_field)

        # Unmapped fields don't need logging per requirements

        # Phase complete - no logging needed

        return mapped_metadata

    def _phase2_value_mapping(
        self, metadata: Dict[str, Any], object_id: str
    ) -> Dict[str, Any]:
        """
        Phase 2: Apply value mappings to transform field values.

        Args:
            metadata: Metadata with field names already mapped
            object_id: Identifier for the object being processed

        Returns:
            Metadata with mapped values
        """
        # Phase start - no logging needed

        value_mapped_metadata = {}

        for field_name, value in metadata.items():
            mapped_value = self.value_mapper.map_value(field_name, value)
            value_mapped_metadata[field_name] = mapped_value

            # Value mapping is already logged in ValueMapper

        # Phase complete - no logging needed

        return value_mapped_metadata

    def _phase3_schema_compliance(
        self, metadata: Dict[str, Any], object_id: str
    ) -> Dict[str, Any]:
        """
        Phase 3: Ensure metadata complies with target schema.

        Args:
            metadata: Metadata with field and value mappings applied
            object_id: Identifier for the object being processed

        Returns:
            Schema-compliant metadata
        """
        # Phase start - no logging needed

        schema_fields = self.schema_loader.get_schema_fields()
        compliant_metadata = {}
        obsolete_fields = []

        # Add all schema fields with appropriate values
        for schema_field in schema_fields:
            if schema_field in metadata:
                # Use mapped value
                compliant_metadata[schema_field] = metadata[schema_field]
            else:
                # Use default value or null
                default_value = self.schema_loader.get_default_value(schema_field)
                compliant_metadata[schema_field] = default_value

                # Missing required fields don't need logging per requirements

        # Identify obsolete fields that don't map to schema
        for field_name in metadata:
            if field_name not in schema_fields:
                obsolete_fields.append(
                    {"field": field_name, "value": metadata[field_name]}
                )

        # Log obsolete fields using structured format
        for obsolete_field in obsolete_fields:
            field_name = obsolete_field["field"]
            field_value = obsolete_field["value"]
            self.structured_log.add_unmapped_field_with_value(field_name, field_value)

        # Phase complete - no logging needed

        return compliant_metadata

    def get_structured_log(self) -> StructuredProcessingLog:
        """
        Get the structured processing log for transformation operations.

        Returns:
            StructuredProcessingLog object
        """
        return self.structured_log
