"""
Tests for the CLI module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from metadata_transformer.cli import main


class TestCLI:
    """Test cases for CLI functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_no_input_arguments(self) -> None:
        """Test CLI with neither --input-dir nor --input-file raises error."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create minimal required directories and files
            field_mapping_file = temp_path / "field_mapping.json"
            field_mapping_file.write_text('{"field": "target"}')

            value_mapping_dir = temp_path / "value_mappings"
            value_mapping_dir.mkdir()
            (value_mapping_dir / "test.json").write_text('{"field": {"key": "value"}}')

            schema_file = temp_path / "schema.json"
            schema_file.write_text(
                '[{"name": "target", "type": "text", "required": false}]'
            )

            output_dir = temp_path / "output"

            result = self.runner.invoke(
                main,
                [
                    "--field-mapping-file",
                    str(field_mapping_file),
                    "--value-mapping-dir",
                    str(value_mapping_dir),
                    "--target-schema-file",
                    str(schema_file),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 1
            assert (
                "Either --input-dir or --input-file must be specified" in result.output
            )

    def test_cli_both_input_arguments(self) -> None:
        """Test CLI with both --input-dir and --input-file raises error."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create minimal required directories and files
            field_mapping_file = temp_path / "field_mapping.json"
            field_mapping_file.write_text('{"field": "target"}')

            value_mapping_dir = temp_path / "value_mappings"
            value_mapping_dir.mkdir()
            (value_mapping_dir / "test.json").write_text('{"field": {"key": "value"}}')

            schema_file = temp_path / "schema.json"
            schema_file.write_text(
                '[{"name": "target", "type": "text", "required": false}]'
            )

            input_dir = temp_path / "input"
            input_dir.mkdir()
            input_file = input_dir / "test.json"
            input_file.write_text('[{"metadata": {"field": "value"}}]')

            output_dir = temp_path / "output"

            result = self.runner.invoke(
                main,
                [
                    "--field-mapping-file",
                    str(field_mapping_file),
                    "--value-mapping-dir",
                    str(value_mapping_dir),
                    "--target-schema-file",
                    str(schema_file),
                    "--input-dir",
                    str(input_dir),
                    "--input-file",
                    str(input_file),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 1
            assert (
                "--input-dir and --input-file are mutually exclusive" in result.output
            )

    def test_cli_single_file_processing_success(self) -> None:
        """Test successful single file processing via CLI."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create field mapping
            field_mapping_file = temp_path / "af_mapping.json"
            field_mapping_file.write_text(
                json.dumps(
                    {"legacy_field": "target_field", "another_field": "another_target"}
                )
            )

            # Create value mapping
            value_mapping_dir = temp_path / "value_mappings"
            value_mapping_dir.mkdir()
            value_mapping_file = value_mapping_dir / "assay_type.json"
            value_mapping_file.write_text(
                json.dumps({"assay_type": {"AF": "Auto-fluorescence"}})
            )

            # Create schema
            schema_file = temp_path / "schema.json"
            schema_file.write_text(
                json.dumps(
                    [
                        {
                            "name": "target_field",
                            "description": "Target field",
                            "type": "text",
                            "required": True,
                            "default_value": None,
                        },
                        {
                            "name": "another_target",
                            "description": "Another target field",
                            "type": "text",
                            "required": False,
                            "default_value": "default",
                        },
                    ]
                )
            )

            # Create input file
            input_file = temp_path / "input.json"
            input_file.write_text(
                json.dumps(
                    [
                        {
                            "uuid": "test-uuid",
                            "metadata": {
                                "legacy_field": "test_value",
                                "assay_type": "AF",
                            },
                        }
                    ]
                )
            )

            output_dir = temp_path / "output"

            result = self.runner.invoke(
                main,
                [
                    "--field-mapping-file",
                    str(field_mapping_file),
                    "--value-mapping-dir",
                    str(value_mapping_dir),
                    "--target-schema-file",
                    str(schema_file),
                    "--input-file",
                    str(input_file),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 0
            assert "✅ Metadata transformation completed successfully!" in result.output
            assert "📄 Processed: input.json" in result.output

            # Verify output file was created
            output_file = output_dir / "input.json"
            assert output_file.exists()

            # Verify output content
            with open(output_file, "r") as f:
                output_data = json.load(f)

            assert "modified_metadata" in output_data
            assert "processing_log" in output_data
            assert isinstance(output_data["modified_metadata"], dict)

    def test_cli_bulk_processing_success(self) -> None:
        """Test successful bulk processing via CLI."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create field mapping
            field_mapping_file = temp_path / "mapping.json"
            field_mapping_file.write_text('{"legacy": "target"}')

            # Create value mapping
            value_mapping_dir = temp_path / "value_mappings"
            value_mapping_dir.mkdir()
            (value_mapping_dir / "values.json").write_text('{"target": {"old": "new"}}')

            # Create schema
            schema_file = temp_path / "schema.json"
            schema_file.write_text(
                '[{"name": "target", "type": "text", "required": false}]'
            )

            # Create input directory with multiple files
            input_dir = temp_path / "input"
            input_dir.mkdir()

            for i in range(3):
                input_file = input_dir / f"file{i}.json"
                input_file.write_text(
                    json.dumps([{"uuid": f"uuid-{i}", "metadata": {"legacy": "old"}}])
                )

            output_dir = temp_path / "output"

            result = self.runner.invoke(
                main,
                [
                    "--field-mapping-file",
                    str(field_mapping_file),
                    "--value-mapping-dir",
                    str(value_mapping_dir),
                    "--target-schema-file",
                    str(schema_file),
                    "--input-dir",
                    str(input_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 0
            assert "✅ Metadata transformation completed successfully!" in result.output
            assert "📊 Bulk Processing Summary:" in result.output
            assert "Files processed: 3" in result.output
            assert "Successful: 3" in result.output

            # Verify output files were created
            for i in range(3):
                output_file = output_dir / f"file{i}.json"
                assert output_file.exists()

            # Verify summary file was created
            summary_file = output_dir / "bulk_processing_summary.json"
            assert summary_file.exists()

    def test_cli_bulk_processing_no_files(self) -> None:
        """Test bulk processing with no JSON files in input directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create required directories and files
            field_mapping_file = temp_path / "mapping.json"
            field_mapping_file.write_text('{"field": "target"}')

            value_mapping_dir = temp_path / "value_mappings"
            value_mapping_dir.mkdir()
            (value_mapping_dir / "values.json").write_text(
                '{"field": {"key": "value"}}'
            )

            schema_file = temp_path / "schema.json"
            schema_file.write_text(
                '[{"name": "target", "type": "text", "required": false}]'
            )

            # Create empty input directory
            input_dir = temp_path / "input"
            input_dir.mkdir()

            output_dir = temp_path / "output"

            result = self.runner.invoke(
                main,
                [
                    "--field-mapping-file",
                    str(field_mapping_file),
                    "--value-mapping-dir",
                    str(value_mapping_dir),
                    "--target-schema-file",
                    str(schema_file),
                    "--input-dir",
                    str(input_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 1
            assert "❌ No JSON files found in:" in result.output

    def test_cli_verbose_mode(self) -> None:
        """Test CLI with verbose mode enabled."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create minimal setup
            field_mapping_file = temp_path / "mapping.json"
            field_mapping_file.write_text('{"field": "target"}')

            value_mapping_dir = temp_path / "value_mappings"
            value_mapping_dir.mkdir()
            (value_mapping_dir / "values.json").write_text(
                '{"field": {"key": "value"}}'
            )

            schema_file = temp_path / "schema.json"
            schema_file.write_text(
                '[{"name": "target", "type": "text", "required": false}]'
            )

            input_file = temp_path / "input.json"
            input_file.write_text('[{"metadata": {"field": "key"}}]')

            output_dir = temp_path / "output"

            result = self.runner.invoke(
                main,
                [
                    "--field-mapping-file",
                    str(field_mapping_file),
                    "--value-mapping-dir",
                    str(value_mapping_dir),
                    "--target-schema-file",
                    str(schema_file),
                    "--input-file",
                    str(input_file),
                    "--output-dir",
                    str(output_dir),
                    "--verbose",
                ],
            )

            assert result.exit_code == 0
            assert "Initializing metadata transformer components..." in result.output
            assert "Loading field mappings from:" in result.output
            assert "Loading value mappings from:" in result.output
            assert "Loading target schema from:" in result.output
            assert "Processing single file:" in result.output

    def test_cli_missing_required_arguments(self) -> None:
        """Test CLI with missing required arguments."""
        result = self.runner.invoke(main, ["--help"])

        # Should show help and exit cleanly
        assert result.exit_code == 0
        assert "--field-mapping-file" in result.output
        assert "--value-mapping-dir" in result.output
        assert "--target-schema-file" in result.output
        assert "--input-dir" in result.output
        assert "--input-file" in result.output
        assert "--output-dir" in result.output
