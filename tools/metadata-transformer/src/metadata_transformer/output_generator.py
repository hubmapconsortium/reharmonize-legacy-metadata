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
        Write transformed metadata to output file with compact json_patch formatting.

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
                # Build JSON output with custom formatting per key
                json_output = self._format_json_with_custom_arrays(output_data)
                f.write(json_output)
        except Exception as e:
            error_msg = f"Error writing output file {output_file}: {e}"
            # Error handling moved to stdout - handled by CLI
            raise FileProcessingError(error_msg)

        # Statistics calculation removed - not currently used
        # If needed in the future, can be retrieved from output_data and output_file.stat()

        return output_file

    def _format_json_with_custom_arrays(self, data: Dict[str, Any]) -> str:
        """
        Format JSON with custom formatting for specific array keys.

        This method formats most of the JSON normally, but applies compact
        one-item-per-line formatting to specified array keys like 'json_patch'.

        Args:
            data: Dictionary to format as JSON

        Returns:
            Formatted JSON string
        """
        # Keys that should have compact array formatting (one item per line)
        compact_array_keys = {'json_patch'}

        lines = ['{']

        items = list(data.items())
        for i, (key, value) in enumerate(items):
            is_last = (i == len(items) - 1)
            comma = '' if is_last else ','

            if key in compact_array_keys and isinstance(value, list):
                # Format array compactly (one item per line)
                lines.append(f'  "{key}": [')
                for j, item in enumerate(value):
                    item_comma = '' if j == len(value) - 1 else ','
                    item_json = json.dumps(item, ensure_ascii=False, separators=(', ', ': '))
                    lines.append(f'    {item_json}{item_comma}')
                lines.append(f'  ]{comma}')
            else:
                # Format normally with standard pretty-printing
                value_json = json.dumps(value, indent=2, ensure_ascii=False)
                # Indent the value appropriately
                indented_value = '\n'.join(
                    '  ' + line if line else line
                    for line in value_json.split('\n')
                )
                lines.append(f'  "{key}": {indented_value.lstrip()}{comma}')

        lines.append('}')
        return '\n'.join(lines)

    def get_processing_log(self) -> List[str]:
        """
        Get the processing log for output generation operations.

        Returns:
            List of log entries as strings
        """
        return self.processing_log.copy()
