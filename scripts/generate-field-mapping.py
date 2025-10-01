#!/usr/bin/env python3
"""
Generate Field Mapping for Metadata Transformation

Reads a CSV file and generates JSON field mappings where:
- Column 1 contains target field names (new schema)
- Columns 2+ contain legacy field names (old schemas)

Creates mappings from legacy field names to target field names.
Only creates mappings when both target and legacy fields are non-empty.

Usage:
    python generate-field-mapping.py <input_file> <output_file>

Example:
    python generate-field-mapping.py rnaseq.csv mappings/field-mapping/rnaseq.json
"""

import csv
import json
import argparse
import sys
from pathlib import Path


def generate_field_mapping(input_file, output_file):
    """
    Generate field mapping JSON from CSV file.

    The CSV structure should have:
    - Row 1: Header row (schema version names)
    - Row 2+: Data rows
      - Column 1: Target field name (new schema)
      - Columns 2+: Legacy field names (old schemas)

    Creates a mapping where legacy field names (keys) map to target field names (values).
    Only creates mappings when BOTH target and legacy fields are non-empty.
    If the same legacy field appears multiple times, the latest mapping is kept.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output JSON file
    """

    merged_mappings = {}

    # Read CSV file
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate CSV structure
    if len(rows) < 2:
        print("Error: CSV file must have at least 2 rows (header + data).", file=sys.stderr)
        sys.exit(1)

    if len(rows[0]) < 2:
        print("Error: CSV file must have at least 2 columns.", file=sys.stderr)
        sys.exit(1)

    # Process data rows (skip header row at index 0)
    for row_idx in range(1, len(rows)):
        row = rows[row_idx]

        # Get target field from column 1 (index 0)
        target_field = row[0].strip() if len(row) > 0 else ""

        # Skip this row if target field is empty
        if not target_field:
            continue

        # Process each legacy field column (columns 2+, indices 1+)
        for col_idx in range(1, len(row)):
            # Get legacy field name
            legacy_field = row[col_idx].strip() if col_idx < len(row) else ""

            # Only create mapping if both target and legacy fields are non-empty
            if legacy_field and target_field:
                # Add or update mapping (later values overwrite earlier ones)
                merged_mappings[legacy_field] = target_field

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_mappings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print(f"Generated field mapping: {output_file}")
    print(f"  Total mappings: {len(merged_mappings)}")


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Generate JSON field mapping from CSV file with target fields (column 1) and legacy fields (columns 2+)"
    )
    parser.add_argument(
        "input_file",
        help="Input CSV file path (column 1: target fields, columns 2+: legacy fields)"
    )
    parser.add_argument(
        "output_file",
        help="Output JSON file path (legacy field -> target field mappings)"
    )

    args = parser.parse_args()
    generate_field_mapping(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
