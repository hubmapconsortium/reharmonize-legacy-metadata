#!/usr/bin/env python3
"""
Regex Pattern Hints for Non-Technical Users

This module contains human-readable descriptions of regex patterns used in schemas.
These hints help data curators understand what format is expected for fields with
regex validation.

The hints are based on:
1. The regex pattern itself
2. The field description from the schema
3. Example values provided in the schema

Format: {field_name: "Human-readable description"}
"""

# Mapping of field names to human-readable regex pattern descriptions
REGEX_HINTS = {
    "parent_sample_id": (
        "Must be a HubMAP or SenNet sample ID in the format: "
        "HBM###.XXXX.### or SNT###.XXXX.### where # is a digit and X is an uppercase letter. "
        "Multiple IDs can be provided as a comma-separated list. "
        "Example: HBM386.ZGKG.235 or HBM386.ZGKG.235, HBM672.MKPK.442"
    ),

    "contributors_path": (
        "Must be a path to a TSV file (tab-separated values). "
        "The path can start with './' or be just a filename. "
        "The file extension must be '.tsv'. "
        "Example: ./contributors.tsv or contributors.tsv"
    ),

    "data_path": (
        "Must be a valid file or directory path. "
        "Can start with '.' or './' or be a simple name starting with alphanumeric characters. "
        "Example: ./TEST001-RK or TEST001-RK or ."
    ),
}


def get_regex_hint(field_name: str) -> str:
    """
    Get the human-readable regex hint for a field.

    Args:
        field_name: Name of the field

    Returns:
        Human-readable description of the regex pattern, or empty string if not found
    """
    return REGEX_HINTS.get(field_name, "")
