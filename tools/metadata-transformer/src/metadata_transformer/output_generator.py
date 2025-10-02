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

    def get_processing_log(self) -> List[str]:
        """
        Get the processing log for output generation operations.

        Returns:
            List of log entries as strings
        """
        return self.processing_log.copy()
