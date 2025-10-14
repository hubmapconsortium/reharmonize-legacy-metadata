"""
Tests for the transformer module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest
from json_rules_engine import PatchApplier, Patches

from metadata_transformer.exceptions import FileProcessingError
from metadata_transformer.field_mapper import FieldMapper, FieldMappings
from metadata_transformer.processing_log import StructuredProcessingLog
from metadata_transformer.processing_log_provider import ProcessingLogProvider
from metadata_transformer.schema_applier import Schema, SchemaApplier
from metadata_transformer.transformer import MetadataTransformer
from metadata_transformer.value_mapper import ValueMapper, ValueMappings


class TestMetadataTransformer:
    """Test cases for MetadataTransformer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Create mock components
        self.field_mapper = Mock(spec=FieldMapper)
        self.value_mapper = Mock(spec=ValueMapper)
        self.field_mappings = Mock(spec=FieldMappings)
        self.value_mappings = Mock(spec=ValueMappings)
        self.schema = Mock(spec=Schema)
        self.schema_applier = Mock(spec=SchemaApplier)
        self.patch_applier = Mock(spec=PatchApplier)
        self.patches = Mock(spec=Patches)

        # Set up default return values for processing logs
        self.field_mapper.get_processing_log.return_value = StructuredProcessingLog()
        self.value_mapper.get_processing_log.return_value = StructuredProcessingLog()
        self.schema_applier.get_processing_log.return_value = StructuredProcessingLog()

        # Set up factory methods to return the mock mappers
        self.field_mappings.get_mapper.return_value = self.field_mapper
        self.value_mappings.get_mapper.return_value = self.value_mapper
        self.schema.get_applier.return_value = self.schema_applier

        # Set up patch_applier to return metadata unchanged by default
        self.patch_applier.apply_patches.side_effect = lambda x: x

        # Set up schema_applier with a more realistic default behavior
        def default_schema_applier(metadata):
            # Get schema fields from schema mock
            schema_fields = self.schema.get_schema_fields.return_value
            result = {}
            for field in schema_fields:
                if field in metadata:
                    result[field] = metadata[field]
                else:
                    result[field] = self.schema.get_default_value.return_value
            return result

        self.schema_applier.apply_schema.side_effect = default_schema_applier

        # Set up patches factory to return the mock applier
        self.patches.get_applier.return_value = self.patch_applier

        # Create log provider
        self.log_provider = ProcessingLogProvider()

        self.transformer = MetadataTransformer(
            self.patches,
            self.field_mappings,
            self.value_mappings,
            self.schema,
            self.log_provider,
        )

    def test_init(self) -> None:
        """Test MetadataTransformer initialization."""
        assert self.transformer.log_provider is self.log_provider
        assert self.transformer.field_mappings is self.field_mappings
        assert self.transformer.value_mappings is self.value_mappings
        assert self.transformer.schema is self.schema
        assert self.transformer.patches is self.patches

    def test_transform_metadata_file_nonexistent(self) -> None:
        """Test transforming non-existent file raises error."""
        nonexistent_file = Path("/nonexistent/file.json")

        with pytest.raises(FileProcessingError, match="Input file not found"):
            self.transformer.transform_metadata_file(nonexistent_file)

    def test_transform_metadata_file_invalid_json(self) -> None:
        """Test transforming file with invalid JSON raises error."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_file = temp_path / "invalid.json"
            invalid_file.write_text("{ invalid json }")

            with pytest.raises(FileProcessingError, match="Invalid JSON"):
                self.transformer.transform_metadata_file(invalid_file)

    def test_transform_metadata_file_invalid_structure(self) -> None:
        """Test transforming file with invalid structure raises error."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_file = temp_path / "invalid_structure.json"
            invalid_file.write_text('"not an object"')

            with pytest.raises(FileProcessingError, match="must contain JSON object"):
                self.transformer.transform_metadata_file(invalid_file)

    def test_transform_metadata_file_single_object(self) -> None:
        """Test transforming file with single metadata object."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "single_object.json"

            # Create test metadata object
            metadata_obj = {
                "uuid": "test-uuid-123",
                "metadata": {
                    "legacy_field1": "legacy_value1",
                    "legacy_field2": "legacy_value2",
                },
            }
            metadata_file.write_text(json.dumps(metadata_obj))

            # Set up mock behaviors
            self.field_mapper.map_field.side_effect = lambda x: {
                "legacy_field1": "target_field1",
                "legacy_field2": "target_field2",
            }.get(x)

            self.value_mapper.map_value.side_effect = lambda f, v: {
                ("target_field1", "legacy_value1"): "mapped_value1",
                ("target_field2", "legacy_value2"): "mapped_value2",
            }.get((f, v), v)

            self.schema.get_schema_fields.return_value = {
                "target_field1": {"required": True},
                "target_field2": {"required": False},
                "target_field3": {"required": False},
            }
            self.schema.get_default_value.return_value = None
            self.schema.is_field_required.return_value = False

            result = self.transformer.transform_metadata_file(metadata_file)

            # Verify result structure
            assert "modified_metadata" in result
            assert "processing_log" in result
            assert isinstance(result["modified_metadata"], dict)

            transformed_obj = result["modified_metadata"]
            assert transformed_obj["target_field1"] == "mapped_value1"
            assert transformed_obj["target_field2"] == "mapped_value2"
            assert transformed_obj["target_field3"] is None  # Default value

    def test_transform_metadata_file_array_rejected(self) -> None:
        """Test that transforming file with array is rejected."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "array_objects.json"

            # Create test metadata array
            metadata_array = [
                {"uuid": "test-uuid-1", "metadata": {"legacy_field": "value1"}},
                {"uuid": "test-uuid-2", "metadata": {"legacy_field": "value2"}},
            ]
            metadata_file.write_text(json.dumps(metadata_array))

            # Arrays are no longer supported
            with pytest.raises(FileProcessingError, match="must contain JSON object"):
                self.transformer.transform_metadata_file(metadata_file)

    def test_phase1_field_mapping(self) -> None:
        """Test Phase 1 field mapping functionality."""
        metadata = {
            "mapped_field": "value1",
            "unmapped_field": "value2",
            "conflicting_field": "value3",
        }

        # Set up field mapper mock
        self.field_mapper.map_field.side_effect = lambda x: {
            "mapped_field": "target_field",
            "conflicting_field": "target_field",  # Same target - creates conflict
        }.get(x)

        result, log = self.transformer._phase1_field_mapping(metadata)

        # Should map the first occurrence and skip the conflicting one
        assert "target_field" in result
        assert result["target_field"] == "value1"  # First mapping wins
        assert "unmapped_field" in result  # Unmapped fields kept

        # Check that log is returned
        assert isinstance(log, StructuredProcessingLog)

    def test_phase2_value_mapping(self) -> None:
        """Test Phase 2 value mapping functionality."""
        metadata = {
            "field1": "legacy_value1",
            "field2": "legacy_value2",
            "field3": "unmapped_value",
        }

        # Set up value mapper mock
        self.value_mapper.map_value.side_effect = lambda f, v: {
            ("field1", "legacy_value1"): "mapped_value1",
            ("field2", "legacy_value2"): "mapped_value2",
        }.get((f, v), v)

        result, log = self.transformer._phase2_value_mapping(metadata)

        assert result["field1"] == "mapped_value1"
        assert result["field2"] == "mapped_value2"
        assert result["field3"] == "unmapped_value"  # Original value preserved

        # Check that log is returned
        assert isinstance(log, StructuredProcessingLog)

    def test_phase3_schema_compliance(self) -> None:
        """Test Phase 3 schema compliance functionality."""
        metadata = {
            "schema_field1": "value1",
            "schema_field2": "value2",
            "obsolete_field": "obsolete_value",
        }

        # Override the default side_effect for this specific test
        expected_result = {
            "schema_field1": "value1",
            "schema_field2": "value2",
            "schema_field3": "default_value",
        }
        self.schema_applier.apply_schema.side_effect = None
        self.schema_applier.apply_schema.return_value = expected_result

        result, log = self.transformer._phase3_schema_compliance(metadata)

        # Should include all schema fields
        assert result["schema_field1"] == "value1"
        assert result["schema_field2"] == "value2"
        assert result["schema_field3"] == "default_value"

        # Should not include obsolete field
        assert "obsolete_field" not in result

        # Check that log is returned
        assert isinstance(log, StructuredProcessingLog)

    def test_transform_metadata_empty(self) -> None:
        """Test transforming empty metadata."""
        metadata = {}

        # Set up minimal mocks
        self.schema.get_schema_fields.return_value = {}

        result, combined_log = self.transformer._transform_metadata(metadata)

        # Should return empty dict since no metadata and no schema fields
        assert isinstance(result, dict)
        assert isinstance(combined_log, StructuredProcessingLog)

    def test_get_structured_log(self) -> None:
        """Test getting structured processing log."""
        # This test is no longer relevant as structured_log is removed
        # The transformer now uses immutable pattern with logs per transformation
        pass

    def test_json_patch_in_output(self) -> None:
        """Test that json_patch key exists in transformation output."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "test_patch.json"

            # Create test metadata object
            metadata_obj = {
                "uuid": "test-uuid-123",
                "metadata": {
                    "legacy_field1": "value1",
                    "legacy_field2": "value2",
                },
            }
            metadata_file.write_text(json.dumps(metadata_obj))

            # Set up mock behaviors
            self.field_mapper.map_field.side_effect = lambda x: {
                "legacy_field1": "target_field1",
                "legacy_field2": "target_field2",
            }.get(x)

            self.value_mapper.map_value.side_effect = lambda f, v: v

            self.schema.get_schema_fields.return_value = {
                "target_field1": {"required": True},
                "target_field2": {"required": False},
            }
            self.schema.get_default_value.return_value = None

            result = self.transformer.transform_metadata_file(metadata_file)

            # Verify json_patch key exists
            assert "json_patch" in result
            assert isinstance(result["json_patch"], list)

    def test_json_patch_format(self) -> None:
        """Test that json_patch contains valid RFC 6902 operations."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "test_patch_format.json"

            # Create test metadata with changes
            metadata_obj = {
                "uuid": "test-uuid-456",
                "metadata": {
                    "old_field": "old_value",
                    "change_field": "original_value",
                },
            }
            metadata_file.write_text(json.dumps(metadata_obj))

            # Set up transformations
            self.field_mapper.map_field.side_effect = lambda x: {
                "old_field": "new_field",
                "change_field": "change_field",
            }.get(x)

            self.value_mapper.map_value.side_effect = lambda f, v: {
                ("change_field", "original_value"): "modified_value",
            }.get((f, v), v)

            self.schema.get_schema_fields.return_value = {
                "new_field": {},
                "change_field": {},
            }
            self.schema.get_default_value.return_value = None

            result = self.transformer.transform_metadata_file(metadata_file)

            # Verify patch operations have required fields
            json_patch = result["json_patch"]
            for operation in json_patch:
                assert "op" in operation
                assert "path" in operation
                assert operation["op"] in [
                    "add",
                    "remove",
                    "replace",
                    "move",
                    "copy",
                    "test",
                ]

    def test_json_patch_applies_correctly(self) -> None:
        """Test that applying the json_patch produces modified_metadata."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "test_patch_apply.json"

            # Create test metadata
            metadata_obj = {
                "uuid": "test-uuid-789",
                "metadata": {
                    "field1": "value1",
                    "field2": "value2",
                },
            }
            metadata_file.write_text(json.dumps(metadata_obj))

            # Simple pass-through mapping
            self.field_mapper.map_field.side_effect = lambda x: x
            self.value_mapper.map_value.side_effect = lambda f, v: f"mapped_{v}"

            self.schema.get_schema_fields.return_value = {
                "field1": {},
                "field2": {},
            }
            self.schema.get_default_value.return_value = None

            result = self.transformer.transform_metadata_file(metadata_file)

            # Apply the patch to original metadata
            import jsonpatch

            original_metadata = metadata_obj["metadata"]
            json_patch = result["json_patch"]
            patched_metadata = jsonpatch.apply_patch(original_metadata, json_patch)

            # Should match modified_metadata
            assert patched_metadata == result["modified_metadata"]

    def test_json_patch_order_in_output(self) -> None:
        """Test that json_patch appears before processing_log in output."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "test_patch_order.json"

            metadata_obj = {
                "uuid": "test-uuid-order",
                "metadata": {"field": "value"},
            }
            metadata_file.write_text(json.dumps(metadata_obj))

            self.field_mapper.map_field.side_effect = lambda x: x
            self.value_mapper.map_value.side_effect = lambda f, v: v
            self.schema.get_schema_fields.return_value = {"field": {}}
            self.schema.get_default_value.return_value = None

            result = self.transformer.transform_metadata_file(metadata_file)

            # Get keys in order
            keys = list(result.keys())

            # json_patch should come before processing_log
            json_patch_idx = keys.index("json_patch")
            processing_log_idx = keys.index("processing_log")

            assert json_patch_idx < processing_log_idx

    def test_json_patch_empty_metadata(self) -> None:
        """Test json_patch generation with empty metadata."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_file = temp_path / "test_empty.json"

            # Empty metadata
            metadata_obj = {"uuid": "test-uuid-empty", "metadata": {}}
            metadata_file.write_text(json.dumps(metadata_obj))

            self.field_mapper.map_field.side_effect = lambda x: x
            self.value_mapper.map_value.side_effect = lambda f, v: v
            self.schema.get_schema_fields.return_value = {}
            self.schema.get_default_value.return_value = None

            result = self.transformer.transform_metadata_file(metadata_file)

            # Should have json_patch key even if empty
            assert "json_patch" in result
            assert isinstance(result["json_patch"], list)
