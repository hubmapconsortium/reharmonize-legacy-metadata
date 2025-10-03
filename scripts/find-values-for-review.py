#!/usr/bin/env python3
"""
Find Legacy Values Requiring Domain Expert Review

Analyzes processed metadata JSON files to identify legacy values that could not
be mapped to standard values. These unmapped values require domain expert review
to determine if they should be added to the standard value set or handled differently.

The script examines the processing_log/value_mappings section of each JSON file
and collects all field-value pairs where the legacy value is mapped to null,
indicating no suitable standard value was found.

Usage:
    python find-values-for-review.py <input_dir> <output_file>

Example:
    python find-values-for-review.py metadata/lcms/output values-for-review.json
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict


def find_values_for_review(input_dir, output_file):
    """
    Find legacy values requiring domain expert review from all JSON files.

    Processes each JSON file in the input directory, examining the
    processing_log/value_mappings section. For each field where a legacy value
    could not be mapped to a standard value (mapped to null), records that
    field-value pair as requiring expert review.

    If the same field has multiple unmapped values across different files,
    they are collected into an array (without duplicates).

    Args:
        input_dir (str): Directory containing processed JSON files
        output_file (str): Path to output JSON file for values requiring review
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    unmapped_values = defaultdict(set)
    files_processed = 0

    json_files = list(input_path.glob("*.json"))

    if not json_files:
        print(f"Warning: No JSON files found in '{input_dir}'.", file=sys.stderr)

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'processing_log' not in data:
                continue

            if 'value_mappings' not in data['processing_log']:
                continue

            value_mappings = data['processing_log']['value_mappings']

            for field_name, mappings in value_mappings.items():
                if not isinstance(mappings, dict):
                    continue

                for legacy_value, standard_value in mappings.items():
                    if standard_value is None:
                        unmapped_values[field_name].add(legacy_value)

            files_processed += 1

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON file '{json_file}': {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Error processing file '{json_file}': {e}", file=sys.stderr)

    result = {}
    for field_name, values in unmapped_values.items():
        sorted_values = sorted(list(values))
        if len(sorted_values) == 1:
            result[field_name] = sorted_values[0]
        else:
            result[field_name] = sorted_values

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Values for review saved to: {output_file}")
    print(f"  Files processed: {files_processed}")
    print(f"  Fields with unmapped values: {len(result)}")
    total_values = sum(len(v) if isinstance(v, list) else 1 for v in result.values())
    print(f"  Total values requiring review: {total_values}")


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Find legacy values requiring domain expert review - identifies unmapped values that need standardization decisions"
    )
    parser.add_argument(
        "input_dir",
        help="Input directory containing processed JSON files"
    )
    parser.add_argument(
        "output_file",
        help="Output JSON file path for values requiring review"
    )

    args = parser.parse_args()
    find_values_for_review(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()
