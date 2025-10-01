#!/usr/bin/env python3
"""
Generate Target Schema for Metadata Transformation

Fetches a YAML schema from a remote URL or local file and converts it to simplified
JSON format for use in metadata transformation validation.

Usage:
    python generate-target-schema.py <yaml_source> <output_json_file>

Examples:
    # From remote URL:
    python generate-target-schema.py \
      https://raw.githubusercontent.com/hubmapconsortium/dataset-metadata-spreadsheet/refs/heads/main/rnaseq/latest/rnaseq.yml \
      schemas/rnaseq.json

    # From local file:
    python generate-target-schema.py \
      local/schema.yml \
      schemas/output.json
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required but not installed.")
    print("Install it with: pip install PyYAML")
    sys.exit(1)


def is_url(source: str) -> bool:
    """
    Check if source is a URL or file path.

    Args:
        source (str): Source string to check

    Returns:
        bool: True if source is a URL, False if it's a file path
    """
    return source.startswith('http://') or source.startswith('https://')


def fetch_yaml_from_source(source: str) -> dict:
    """
    Fetch and parse YAML from URL or local file.

    Args:
        source (str): URL or file path to YAML file

    Returns:
        dict: Parsed YAML data

    Raises:
        HTTPError, URLError: For URL fetch errors
        FileNotFoundError: If local file not found
        yaml.YAMLError: For YAML parsing errors
    """
    if is_url(source):
        # Fetch from remote URL
        print(f"Fetching YAML from URL: {source}")
        try:
            response = urlopen(source)
            yaml_content = response.read()
        except HTTPError as e:
            print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
            sys.exit(1)
        except URLError as e:
            print(f"Error: Failed to reach server - {e.reason}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from local file
        print(f"Reading YAML from file: {source}")
        try:
            with open(source, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found - {source}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Parse YAML
    try:
        yaml_data = yaml.safe_load(yaml_content)
        return yaml_data
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML - {e}", file=sys.stderr)
        sys.exit(1)


def transform_yaml_to_json_schema(yaml_data: dict) -> list:
    """
    Transform YAML schema to simplified JSON format.

    Args:
        yaml_data (dict): Parsed YAML data

    Returns:
        list: List of transformed field objects
    """
    # Validate YAML structure
    if not isinstance(yaml_data, dict):
        print("Error: YAML does not contain a dictionary", file=sys.stderr)
        sys.exit(1)

    if 'children' not in yaml_data:
        print("Error: YAML does not have expected 'children' structure", file=sys.stderr)
        sys.exit(1)

    if not isinstance(yaml_data['children'], list):
        print("Error: 'children' in YAML is not a list", file=sys.stderr)
        sys.exit(1)

    # Extract schema name for logging
    schema_name = yaml_data.get('name', 'Unknown')
    print(f"Transforming '{schema_name}' schema with {len(yaml_data['children'])} fields...")

    # Transform each field
    json_output = []
    for field in yaml_data['children']:
        if not isinstance(field, dict):
            print(f"Warning: Skipping non-dictionary field: {field}")
            continue

        transformed_field = transform_field(field)
        if transformed_field:
            json_output.append(transformed_field)

    return json_output


def transform_field(field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transform a single field from YAML format to JSON format.

    Args:
        field (Dict): Single field from YAML children array

    Returns:
        Dict: Transformed field in JSON format, or None if invalid
    """
    # Extract name (try 'name' first, then 'key')
    name = field.get('name') or field.get('key')
    if not name:
        print(f"Warning: Field missing name/key: {field}")
        return None

    # Extract description
    description = field.get('description', '')

    # Extract field type
    field_type = field.get('type', '')
    json_type = map_field_type(field_type)

    # Extract required flag from configuration
    configuration = field.get('configuration', {})
    required = configuration.get('required', False)

    # Extract regex
    regex = field.get('regex')

    # Extract default value
    default_value = extract_default_value(field, field_type)

    # Extract permissible values
    permissible_values = extract_permissible_values(field, field_type)

    return {
        "name": name,
        "description": description,
        "type": json_type,
        "required": required,
        "regex": regex,
        "default_value": default_value,
        "permissible_values": permissible_values
    }


def map_field_type(yaml_type: str) -> str:
    """
    Map YAML field type to simplified JSON field type.

    Args:
        yaml_type (str): YAML field type

    Returns:
        str: Corresponding JSON field type
    """
    type_mapping = {
        'text-field': 'text',
        'link-field': 'text',
        'controlled-term-field': 'categorical',
        'numeric-field': 'number',
        'radio-field': 'categorical',
        'checkbox-field': 'categorical',
        'date-field': 'text',
        'datetime-field': 'text',
        'email-field': 'text',
        'url-field': 'text',
    }

    return type_mapping.get(yaml_type, 'text')  # Default to 'text' for unknown types


def extract_default_value(field: Dict[str, Any], field_type: str) -> Any:
    """
    Extract default value from field, handling different field types appropriately.

    Args:
        field (Dict): Field dictionary from YAML
        field_type (str): YAML field type

    Returns:
        Any: Default value or None
    """
    default = field.get('default')
    if default is None:
        return None

    # Handle string defaults (simple values)
    if isinstance(default, str):
        return default

    # Handle dictionary defaults
    if isinstance(default, dict):
        # For controlled terms, prefer label over value
        if field_type == 'controlled-term-field':
            return default.get('label') or default.get('value')
        # For other types, use value directly
        return default.get('value')

    # For any other type, return as-is
    return default


def extract_permissible_values(field: Dict[str, Any], field_type: str) -> Optional[List[Any]]:
    """
    Extract permissible values from categorical field types.

    Args:
        field (Dict): Field dictionary from YAML
        field_type (str): YAML field type

    Returns:
        List[Any]: List of permissible values, or None for non-categorical fields
    """
    categorical_types = ['controlled-term-field', 'radio-field', 'checkbox-field']
    if field_type not in categorical_types:
        return None

    values = field.get('values', [])
    if not values:
        return None

    permissible_values = []
    for value in values:
        if isinstance(value, dict):
            label = value.get('label')
            if label is None:
                label = value.get('termLabel')
            if label is not None:
                # Convert numeric string labels to their proper type
                if isinstance(label, str) and label.isdigit():
                    permissible_values.append(int(label))
                elif isinstance(label, int):
                    permissible_values.append(label)
                else:
                    permissible_values.append(label)
        elif isinstance(value, (str, int, float)):
            # Handle simple scalar values
            permissible_values.append(value)

    return permissible_values if permissible_values else None


def main():
    """Main execution with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Generate target schema from YAML file or URL"
    )
    parser.add_argument(
        "source",
        help="YAML schema source (URL or file path)"
    )
    parser.add_argument(
        "output_file",
        help="Output JSON file path"
    )

    args = parser.parse_args()

    # Fetch and parse YAML
    yaml_data = fetch_yaml_from_source(args.source)

    # Transform to JSON schema
    json_schema = transform_yaml_to_json_schema(yaml_data)

    # Ensure output directory exists
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_schema, f, indent=2, ensure_ascii=False)

        print(f"Generated target schema: {output_path}")
        print(f"  Total fields: {len(json_schema)}")

    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
