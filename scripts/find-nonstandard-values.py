#!/usr/bin/env python3
"""
Find Non-Standard Values for Data Curator Review

Analyzes processed metadata JSON files to identify values from modified metadata
that are not in the standardized value set. These non-standard values require
review by domain experts and data curators to determine if they should be added
to the standard value set or corrected.

The script uses three detection approaches:
1. Non-standard values: Checks modified_metadata against schema's standardized permissible values
2. Missing required values: Detects null or empty values in required fields per schema
3. Regex violations: Identifies values that don't match regex pattern constraints in schema

Usage:
    python find-nonstandard-values.py <input_dir> <schema_file> <output_file>

Example:
    python find-nonstandard-values.py metadata/rnaseq/output metadata/rnaseq/rnaseq-schema.json nonstandard-values.json

    This will generate:
    - nonstandard-values.json (aggregated JSON)
    - todo/ folder with Excel files grouped by group_name:
      - todo/University of California San Diego TMC (RNAseq).xlsx
      - todo/Stanford TMC (RNAseq).xlsx
      - etc.
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, Any, List, Tuple
import re

# Import TODO Excel generation utilities
try:
    from utils.todo_excel_generator import generate_todo_excel_reports
    EXCEL_UTILS_AVAILABLE = True
except ImportError:
    EXCEL_UTILS_AVAILABLE = False


def load_schema(schema_file: str) -> Tuple[Dict[str, List[Any]], Set[str], Dict[str, str]]:
    """
    Load schema and extract standardized permissible values, required fields, and regex constraints.

    Args:
        schema_file: Path to the schema JSON file

    Returns:
        Tuple containing:
        - Dictionary mapping field names to their standardized permissible values (if any)
        - Set of field names marked as required
        - Dictionary mapping field names to their regex patterns (if any)
    """
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file '{schema_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse schema file: {e}", file=sys.stderr)
        sys.exit(1)

    permissible_values_map = {}
    required_fields_set = set()
    regex_constraints_map = {}

    if isinstance(schema, list):
        for field in schema:
            if isinstance(field, dict) and 'name' in field:
                field_name = field['name']
                permissible_values = field.get('permissible_values')
                if permissible_values is not None:
                    permissible_values_map[field_name] = permissible_values

                # Track required fields
                if field.get('required') is True:
                    required_fields_set.add(field_name)

                # Track regex constraints
                regex_pattern = field.get('regex')
                if regex_pattern is not None and regex_pattern != "":
                    regex_constraints_map[field_name] = regex_pattern

    return permissible_values_map, required_fields_set, regex_constraints_map


def find_non_permissible_values(
    data: Dict,
    permissible_values_map: Dict[str, List[Any]]
) -> Dict[str, Set[str]]:
    """
    Find values in modified_metadata that aren't in the standardized value set.

    Args:
        data: Parsed JSON data from a processed metadata file
        permissible_values_map: Dictionary of field names to standardized permissible values

    Returns:
        Dictionary mapping field names to sets of non-standard values
    """
    non_permissible = defaultdict(set)

    if 'modified_metadata' not in data:
        return non_permissible

    modified_metadata = data['modified_metadata']

    for field_name, value in modified_metadata.items():
        # Skip null values
        if value is None:
            continue

        # Check if field has standardized permissible values in schema
        if field_name not in permissible_values_map:
            continue

        standardized_values = permissible_values_map[field_name]

        # Convert value to string for comparison (handles different types)
        value_str = str(value)

        # Check if value is not in the standardized value set
        # Need to handle both string and non-string standardized values
        is_standard = False
        for sv in standardized_values:
            if str(sv) == value_str or sv == value:
                is_standard = True
                break

        if not is_standard:
            non_permissible[field_name].add(value_str)

    return non_permissible


def find_missing_required_values(
    data: Dict,
    required_fields_set: Set[str]
) -> Dict[str, Set[str]]:
    """
    Find required fields with null or empty values in modified_metadata.

    Args:
        data: Parsed JSON data from a processed metadata file
        required_fields_set: Set of field names marked as required in schema

    Returns:
        Dictionary mapping field names to sets of problematic value indicators
    """
    missing_required = defaultdict(set)

    if 'modified_metadata' not in data:
        return missing_required

    modified_metadata = data['modified_metadata']

    for field_name in required_fields_set:
        # Check if field exists in modified_metadata
        if field_name not in modified_metadata:
            # Field completely missing - this is a problem
            missing_required[field_name].add("MISSING_FIELD")
            continue

        value = modified_metadata[field_name]

        # Check for null
        if value is None:
            missing_required[field_name].add("null")

        # Check for empty string
        elif isinstance(value, str) and value.strip() == "":
            missing_required[field_name].add("")

        # Check for empty list/dict (less common but possible)
        elif isinstance(value, list) and len(value) == 0:
            missing_required[field_name].add("[]")
        elif isinstance(value, dict) and len(value) == 0:
            missing_required[field_name].add("{}")

    return missing_required


def find_regex_violations(
    data: Dict,
    regex_constraints_map: Dict[str, str]
) -> Dict[str, Set[str]]:
    """
    Find values in modified_metadata that don't match their regex constraints.

    Args:
        data: Parsed JSON data from a processed metadata file
        regex_constraints_map: Dictionary of field names to regex patterns from schema

    Returns:
        Dictionary mapping field names to sets of values that violate regex constraints
    """
    regex_violations = defaultdict(set)

    if 'modified_metadata' not in data:
        return regex_violations

    modified_metadata = data['modified_metadata']

    for field_name, regex_pattern in regex_constraints_map.items():
        # Skip if field doesn't exist in modified_metadata
        if field_name not in modified_metadata:
            continue

        value = modified_metadata[field_name]

        # Skip null values (handled by missing_required check)
        if value is None:
            continue

        # Convert value to string for regex matching
        value_str = str(value)

        # Skip empty strings (handled by missing_required check)
        if value_str.strip() == "":
            continue

        # Try to match the regex pattern
        try:
            pattern = re.compile(regex_pattern)
            if not pattern.fullmatch(value_str):
                # Value doesn't match the regex pattern
                regex_violations[field_name].add(value_str)
        except re.error as e:
            # Invalid regex pattern in schema - log but don't crash
            print(f"Warning: Invalid regex pattern for field '{field_name}': {e}", file=sys.stderr)
            continue

    return regex_violations


def merge_results(
    non_permissible: Dict[str, Set[str]],
    missing_required: Dict[str, Set[str]],
    regex_violations: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    """
    Merge results from all three detection approaches.

    Args:
        non_permissible: Values not in the standardized value set
        missing_required: Required fields with null or empty values
        regex_violations: Values that don't match regex constraints

    Returns:
        Merged dictionary with all non-standard values requiring review
    """
    merged = defaultdict(set)

    # Add non-permissible values
    for field_name, values in non_permissible.items():
        merged[field_name].update(values)

    # Add missing required values
    for field_name, values in missing_required.items():
        merged[field_name].update(values)

    # Add regex violations
    for field_name, values in regex_violations.items():
        merged[field_name].update(values)

    return merged


def format_output(nonstandard_values: Dict[str, Set[str]]) -> Dict[str, Any]:
    """
    Format the output: single values as strings, multiple as sorted arrays.

    Args:
        nonstandard_values: Dictionary of field names to sets of non-standard values

    Returns:
        Formatted dictionary ready for JSON output
    """
    result = {}

    for field_name, values in nonstandard_values.items():
        sorted_values = sorted(list(values))
        if len(sorted_values) == 1:
            result[field_name] = sorted_values[0]
        else:
            result[field_name] = sorted_values

    return result


def slugify_group_name(group_name: str, dataset_type: str) -> str:
    """
    Convert group name and dataset type to slug format for filename.

    Args:
        group_name: Group name (e.g., "University of California San Diego TMC")
        dataset_type: Dataset type (e.g., "RNAseq")

    Returns:
        Slug format (e.g., "university-of-california-san-diego-tmc-rnaseq")
    """
    # Convert to lowercase and replace spaces with hyphens
    group_slug = group_name.lower().replace(' ', '-')
    dataset_slug = dataset_type.lower()

    return f"{group_slug}-{dataset_slug}"


def find_nonstandard_values(
    input_dir: str,
    schema_file: str,
    output_file: str
):
    """
    Find non-standard values from modified metadata for curator review.

    Uses three detection approaches:
    1. Non-standard values in modified_metadata vs schema's standardized value set
    2. Missing required values in modified_metadata (null or empty for required fields)
    3. Regex violations in modified_metadata (values not matching regex constraints)

    Generates:
    - JSON file with aggregated non-standard values
    - todo/ folder with Excel files grouped by group_name

    Args:
        input_dir: Directory containing processed JSON files
        schema_file: Path to schema JSON file with standardized permissible values
        output_file: Path to output JSON file for non-standard values
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Load schema with standardized value sets, required fields, and regex constraints
    permissible_values_map, required_fields_set, regex_constraints_map = load_schema(schema_file)

    # Aggregate non-standard values across all files (for JSON output)
    all_nonstandard_values = defaultdict(set)

    # Grouped issues by group_name for Excel export
    # Structure: {group_slug: {'issues': {issue_type: ...}, 'group_name': str, 'dataset_type': str}}
    grouped_issues = defaultdict(lambda: {
        'issues': {
            'non_permissible': defaultdict(lambda: defaultdict(set)),
            'missing_required': defaultdict(lambda: defaultdict(set)),
            'regex_violations': defaultdict(lambda: defaultdict(set))
        },
        'group_name': None,
        'dataset_type': None
    })

    files_processed = 0
    non_standard_count = 0
    missing_required_count = 0
    regex_violation_count = 0

    json_files = list(input_path.glob("*.json"))

    if not json_files:
        print(f"Warning: No JSON files found in '{input_dir}'.", file=sys.stderr)

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract metadata for grouping
            hubmap_id = data.get('hubmap_id', 'UNKNOWN')
            group_name = data.get('group_name', 'Unknown Group')
            dataset_type = data.get('dataset_type', 'Unknown')

            # Create group slug for Excel file naming
            group_slug = slugify_group_name(group_name, dataset_type)

            # Approach 1: Find non-standard values
            non_standard = find_non_permissible_values(data, permissible_values_map)

            # Approach 2: Find missing required values
            missing_required = find_missing_required_values(data, required_fields_set)

            # Approach 3: Find regex violations
            regex_violations = find_regex_violations(data, regex_constraints_map)

            # Merge results for this file (for JSON output)
            file_results = merge_results(non_standard, missing_required, regex_violations)

            # Aggregate to global results (for JSON output)
            for field_name, values in file_results.items():
                all_nonstandard_values[field_name].update(values)

            # Store per-file issues grouped by group_name (for Excel output)
            # Store metadata if not already set
            if grouped_issues[group_slug]['group_name'] is None:
                grouped_issues[group_slug]['group_name'] = group_name
                grouped_issues[group_slug]['dataset_type'] = dataset_type

            # Store issues
            for field_name, values in non_standard.items():
                grouped_issues[group_slug]['issues']['non_permissible'][hubmap_id][field_name].update(values)

            for field_name, values in missing_required.items():
                grouped_issues[group_slug]['issues']['missing_required'][hubmap_id][field_name].update(values)

            for field_name, values in regex_violations.items():
                grouped_issues[group_slug]['issues']['regex_violations'][hubmap_id][field_name].update(values)

            # Track counts
            if non_standard:
                non_standard_count += 1
            if missing_required:
                missing_required_count += 1
            if regex_violations:
                regex_violation_count += 1

            files_processed += 1

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON file '{json_file}': {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Error processing file '{json_file}': {e}", file=sys.stderr)

    # Format output
    result = format_output(all_nonstandard_values)

    # Write JSON output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print(f"Non-standard values saved to: {output_file}")
    print(f"  Files processed: {files_processed}")
    print(f"  Files with non-standard values: {non_standard_count}")
    print(f"  Files with missing required values: {missing_required_count}")
    print(f"  Files with regex violations: {regex_violation_count}")
    total_values = sum(len(v) if isinstance(v, list) else 1 for v in result.values())
    print(f"  Total non-standard values found: {total_values}")

    # Generate TODO Excel reports
    if EXCEL_UTILS_AVAILABLE:
        generate_todo_excel_reports(grouped_issues, output_file, permissible_values_map)
    else:
        print("\nWarning: Excel utilities not available. Skipping Excel report generation.", file=sys.stderr)
        print("Make sure utils/todo_excel_generator.py is in the same directory as this script.", file=sys.stderr)


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Find non-standard values from modified metadata for domain expert and data curator review"
    )
    parser.add_argument(
        "input_dir",
        help="Input directory containing processed JSON files"
    )
    parser.add_argument(
        "schema_file",
        help="Path to schema JSON file with standardized permissible values"
    )
    parser.add_argument(
        "output_file",
        help="Output JSON file path for non-standard values"
    )

    args = parser.parse_args()

    find_nonstandard_values(
        args.input_dir,
        args.schema_file,
        args.output_file
    )


if __name__ == "__main__":
    main()
