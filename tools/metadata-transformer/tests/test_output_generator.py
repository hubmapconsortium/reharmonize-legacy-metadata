"""
Tests for the output_generator module.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from metadata_transformer.exceptions import FileProcessingError
from metadata_transformer.output_generator import OutputGenerator


class TestOutputGenerator:
    """Test cases for OutputGenerator class."""

    def test_init(self) -> None:
        """Test OutputGenerator initialization."""
        generator = OutputGenerator()
        assert isinstance(generator.processing_log, list)
        assert len(generator.processing_log) == 0

    def test_write_output_file(self) -> None:
        """Test writing output file successfully."""
        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = Path("test_input.json")
            output_dir = temp_path / "output"

            output_data = {
                "revised_metadata": [{"field1": "value1", "field2": "value2"}],
                "processing_log": [{"phase": "test", "action": "test_action"}],
            }

            result_path = generator.write_output_file(
                output_data, input_file, output_dir
            )

            # Verify output directory was created
            assert output_dir.exists()
            assert output_dir.is_dir()

            # Verify output file was created with correct name
            expected_filename = "test_input.json"
            expected_path = output_dir / expected_filename
            assert result_path == expected_path
            assert result_path.exists()

            # Verify file contents
            with open(result_path, "r") as f:
                written_data = json.load(f)
            assert written_data == output_data

            # Verify processing log - output generation no longer creates log entries
            assert len(generator.processing_log) == 0

    def test_write_output_file_creates_directory(self) -> None:
        """Test that output directory is created if it doesn't exist."""
        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = Path("test.json")
            output_dir = temp_path / "nonexistent" / "nested" / "output"

            output_data = {"revised_metadata": [], "processing_log": []}

            # Directory shouldn't exist initially
            assert not output_dir.exists()

            generator.write_output_file(output_data, input_file, output_dir)

            # Directory should be created
            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_write_output_file_permission_error(self) -> None:
        """Test write_output_file raises error when can't write file."""
        from unittest.mock import patch

        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "input.json"
            output_dir = temp_path / "output"
            output_data = {"revised_metadata": [], "processing_log": []}

            # Mock the open function to raise a permission error
            with patch(
                "builtins.open", side_effect=PermissionError("Permission denied")
            ):
                with pytest.raises(
                    FileProcessingError, match="Error writing output file"
                ):
                    generator.write_output_file(output_data, input_file, output_dir)

    def test_write_bulk_summary(self) -> None:
        """Test writing bulk processing summary."""
        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            processed_files = [
                {
                    "input_file": "file1.json",
                    "output_file": "file1.json",
                    "status": "success",
                    "objects_processed": 5,
                    "log_entries": 20,
                },
                {
                    "input_file": "file2.json",
                    "output_file": "file2.json",
                    "status": "success",
                    "objects_processed": 3,
                    "log_entries": 15,
                },
                {
                    "input_file": "file3.json",
                    "output_file": None,
                    "status": "failed",
                    "error": "Test error",
                    "objects_processed": 0,
                    "log_entries": 0,
                },
            ]

            result_path = generator.write_bulk_summary(processed_files, temp_path)

            # Verify summary file was created
            expected_path = temp_path / "bulk_processing_summary.json"
            assert result_path == expected_path
            assert result_path.exists()

            # Verify summary contents
            with open(result_path, "r") as f:
                summary_data = json.load(f)

            assert "bulk_processing_summary" in summary_data
            assert "file_processing_details" in summary_data
            assert "processing_log" in summary_data

            summary = summary_data["bulk_processing_summary"]
            assert summary["total_files_processed"] == 3
            assert summary["successful_files"] == 2
            assert summary["failed_files"] == 1
            assert summary["total_metadata_objects_transformed"] == 8  # 5 + 3
            assert summary["output_directory"] == str(temp_path)

            assert summary_data["file_processing_details"] == processed_files

    def test_write_bulk_summary_all_failed(self) -> None:
        """Test writing bulk summary when all files failed."""
        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            processed_files = [
                {
                    "input_file": "file1.json",
                    "status": "failed",
                    "error": "Error 1",
                    "objects_processed": 0,
                },
                {
                    "input_file": "file2.json",
                    "status": "failed",
                    "error": "Error 2",
                    "objects_processed": 0,
                },
            ]

            result_path = generator.write_bulk_summary(processed_files, temp_path)

            with open(result_path, "r") as f:
                summary_data = json.load(f)

            summary = summary_data["bulk_processing_summary"]
            assert summary["total_files_processed"] == 2
            assert summary["successful_files"] == 0
            assert summary["failed_files"] == 2
            assert summary["total_metadata_objects_transformed"] == 0

    def test_write_bulk_summary_empty_list(self) -> None:
        """Test writing bulk summary with empty processed files list."""
        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            processed_files = []

            result_path = generator.write_bulk_summary(processed_files, temp_path)

            with open(result_path, "r") as f:
                summary_data = json.load(f)

            summary = summary_data["bulk_processing_summary"]
            assert summary["total_files_processed"] == 0
            assert summary["successful_files"] == 0
            assert summary["failed_files"] == 0
            assert summary["total_metadata_objects_transformed"] == 0

    def test_get_current_timestamp(self) -> None:
        """Test getting current timestamp returns ISO format string."""
        generator = OutputGenerator()
        timestamp = generator._get_current_timestamp()

        # Should be a string in ISO format
        assert isinstance(timestamp, str)
        # Basic check that it looks like ISO format (contains T and colons)
        assert "T" in timestamp
        assert ":" in timestamp

    def test_get_processing_log(self) -> None:
        """Test getting processing log returns a copy."""
        generator = OutputGenerator()
        test_log = [{"phase": "test", "action": "test_action"}]
        generator.processing_log = test_log

        retrieved_log = generator.get_processing_log()

        assert retrieved_log == test_log
        # Should be a copy, not the same object
        assert retrieved_log is not generator.processing_log

    def test_write_output_file_statistics(self) -> None:
        """Test that output file includes proper statistics in processing log."""
        generator = OutputGenerator()

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = Path("stats_test.json")
            output_dir = temp_path

            output_data = {
                "revised_metadata": [{"field": "value1"}, {"field": "value2"}],
                "processing_log": [
                    {"log": "entry1"},
                    {"log": "entry2"},
                    {"log": "entry3"},
                ],
            }

            generator.write_output_file(output_data, input_file, output_dir)

            # Processing log statistics are now handled by CLI - no log entries
            assert len(generator.processing_log) == 0
