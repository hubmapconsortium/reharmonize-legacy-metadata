"""
Output generation functionality for writing transformed metadata to files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from metadata_transformer.exceptions import FileProcessingError


class OutputGenerator:
    """Handles generation and writing of output files."""

    def __init__(self) -> None:
        """Initialize the OutputGenerator."""
        self.processing_log: List[str] = []

    def write_output_file(
        self, output_data: Dict[str, Any], input_file: Path, output_dir: Path
    ) -> Path:
        """
        Write transformed metadata to output file.

        Args:
            output_data: Dictionary containing migrated_metadata and processing_log
            input_file: Original input file path (used for naming output file)
            output_dir: Directory where output file should be written

        Returns:
            Path to the written output file

        Raises:
            FileProcessingError: If output file can't be written
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename based on input filename
        input_stem = input_file.stem
        output_filename = f"{input_stem}.json"
        output_file = output_dir / output_filename

        # Output generation info moved to stdout - handled by CLI

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            error_msg = f"Error writing output file {output_file}: {e}"
            # Error handling moved to stdout - handled by CLI
            raise FileProcessingError(error_msg)

        # Statistics calculation removed - not currently used
        # If needed in the future, can be retrieved from output_data and output_file.stat()

        return output_file

    def write_bulk_summary(
        self, processed_files: List[Dict[str, Any]], output_dir: Path
    ) -> Path:
        """
        Write a summary file for bulk processing operations.

        Args:
            processed_files: List of file processing results
            output_dir: Directory where summary should be written

        Returns:
            Path to the written summary file

        Raises:
            FileProcessingError: If summary file can't be written
        """
        summary_file = output_dir / "bulk_processing_summary.json"

        # Calculate summary statistics
        total_files = len(processed_files)
        successful_files = len(
            [f for f in processed_files if f.get("status") == "success"]
        )
        failed_files = total_files - successful_files

        total_objects = sum(
            f.get("objects_processed", 0)
            for f in processed_files
            if f.get("status") == "success"
        )

        summary_data = {
            "bulk_processing_summary": {
                "timestamp": self._get_current_timestamp(),
                "total_files_processed": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "total_metadata_objects_transformed": total_objects,
                "output_directory": str(output_dir),
            },
            "file_processing_details": processed_files,
            "processing_log": self.processing_log,
        }

        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise FileProcessingError(f"Error writing summary file {summary_file}: {e}")

        # Bulk summary info moved to stdout - handled by CLI

        return summary_file

    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp as ISO format string.

        Returns:
            Current timestamp string
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def get_processing_log(self) -> List[str]:
        """
        Get the processing log for output generation operations.

        Returns:
            List of log entries as strings
        """
        return self.processing_log.copy()
