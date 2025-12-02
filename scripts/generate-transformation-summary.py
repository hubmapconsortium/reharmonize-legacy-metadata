#!/usr/bin/env python3
"""
Generate Transformation Summary HTML Report

Creates an HTML page summarizing metadata transformations for a specific assay type.
The report includes:
1. Field mappings table (from CSV, preserving matrix format)
2. Value mappings table (aggregated from output files, deduplicated)
3. Patches list (human-readable narration using templates)

Usage:
    python generate-transformation-summary.py \
        --field-mapping-csv <csv_file> \
        --output-dir <output_directory> \
        --patch-file <patches.json> \
        --title <assay_type> \
        --output-file <output.html>

Example:
    python generate-transformation-summary.py \
        --field-mapping-csv metadata/rnaseq/rnaseq-field-mappings.csv \
        --output-dir metadata/rnaseq/output \
        --patch-file metadata/rnaseq/rnaseq-patches.json \
        --title "RNAseq" \
        --output-file metadata/rnaseq/transformation-summary.html
"""

import csv
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

try:
    from jinja2 import Template
except ImportError:
    print("Error: Jinja2 is required. Install with: pip install jinja2", file=sys.stderr)
    sys.exit(1)


# Human-readable labels for field names
# Used for both conditions and actions in patch narration
FIELD_LABELS = {
    # Condition fields (used in 'when' clause)
    "acquisition_instrument_model": "acquisition instrument model",
    "acquisition_instrument_vendor": "acquisition instrument vendor",
    "assay_type": "assay type",
    "barcode_size": "barcode size",
    "cell_barcode_offset": "cell barcode offset",
    "cell_barcode_size": "cell barcode size",
    "execution_datetime": "execution datetime",
    "lc_instrument_model": "LC instrument model",
    "library_construction_protocols_io_doi": "library construction protocol",
    "library_preparation_kit": "library prep kit",
    "preparation_instrument_model": "preparation instrument model",
    "preparation_instrument_vendor": "preparation instrument vendor",
    "protocols_io_doi": "protocol DOI",
    "rnaseq_assay_method": "RNAseq assay method",
    "sequencing_read_format": "read format",
    "sequencing_reagent_kit": "reagent kit",
    "transposition_kit_number": "transposition kit number",
    "transposition_method": "transposition method",
    # Action fields (used in 'then' clause)
    "assay_input_entity": "input entity",
    "barcode_read": "barcode read",
    "barcode_offset": "barcode offset",
    "umi_read": "UMI read",
    "umi_size": "UMI size",
    "umi_offset": "UMI offset",
    "preparation_instrument_kit": "preparation instrument kit",
    "sample_indexing_kit": "sample indexing kit",
    "sample_indexing_set": "sample indexing set",
    "metadata_schema_id": "metadata schema ID",
}

# Threshold for using bullet-point format (Option C) vs inline format (Option B)
COMPLEX_PATCH_THRESHOLD = 4  # If 4+ actions, use bullet points

# Human-readable labels for schema version headers in field mappings table
HEADER_LABELS = {
    # Special
    "CEDAR Field": "CEDAR Field",
    # CEDAR target schemas (format: "AssayType (vX.X.X-CEDAR)")
    "cedar-10x-multiome-v1.0.0": "10x Multiome (v1.0.0-CEDAR)",
    "cedar-10x-multiome-v2.0.0": "10x Multiome (v2.0.0-CEDAR)",
    "cedar-af-v2.0.0": "Autofluorescence (v2.0.0-CEDAR)",
    "cedar-af-v2.1.0": "Autofluorescence (v2.1.0-CEDAR)",
    "cedar-atacseq-v5.0.0": "ATACseq (v5.0.0-CEDAR)",
    "cedar-celldive-v2.2.0": "Cell DIVE (v2.2.0-CEDAR)",
    "cedar-codex-v2.0.0": "CODEX (v2.0.0-CEDAR)",
    "cedar-desi-v2.0.0": "DESI (v2.0.0-CEDAR)",
    "cedar-histology-v2.0.0": "Histology (v2.0.0-CEDAR)",
    "cedar-histology-v2.1.0": "Histology (v2.1.0-CEDAR)",
    "cedar-histology-v2.2.0": "Histology (v2.2.0-CEDAR)",
    "cedar-imc-2d-v2.0.0": "IMC 2D (v2.0.0-CEDAR)",
    "cedar-lightsheet-v3.0.0": "Light Sheet (v3.0.0-CEDAR)",
    "cedar-lightsheet-v3.1.0": "Light Sheet (v3.1.0-CEDAR)",
    "cedar-maldi-v1.0.0": "MALDI (v1.0.0-CEDAR)",
    "cedar-maldi-v2.0.0": "MALDI (v2.0.0-CEDAR)",
    "cedar-mibi-v2.0.0": "MIBI (v2.0.0-CEDAR)",
    "cedar-music-v1.0.0": "MUSIC (v1.0.0-CEDAR)",
    "cedar-music-v2.0.0": "MUSIC (v2.0.0-CEDAR)",
    "cedar-rnaseq-v4.0.0": "RNAseq (v4.0.0-CEDAR)",
    "cedar-rnaseq-v5.0.0": "RNAseq (v5.0.0-CEDAR)",
    "cedar-visium-no-probes-v1.0.0": "Visium No Probes (v1.0.0-CEDAR)",
    "cedar-visium-no-probes-v3.0.0": "Visium No Probes (v3.0.0-CEDAR)",
    "cedar-lcms-v2.0.0": "LC-MS (v2.0.0-CEDAR)",
    # Legacy RNAseq schemas
    "bulkrnaseq-v0": "Bulk RNAseq (v0)",
    "bulkrnaseq-v1": "Bulk RNAseq (v1)",
    "scrnaseq-v0": "scRNAseq (v0)",
    "scrnaseq-v1": "scRNAseq (v1)",
    "scrnaseq-v2": "scRNAseq (v2)",
    "scrnaseq-v3": "scRNAseq (v3)",
    # Legacy ATACseq schemas
    "bulkatacseq-v0": "Bulk ATACseq (v0)",
    "bulkatacseq-v1": "Bulk ATACseq (v1)",
    "scatacseq-v0": "scATACseq (v0)",
    "scatacseq-v1": "scATACseq (v1)",
    # Legacy imaging schemas
    "af-v0": "Autofluorescence (v0)",
    "af-v1": "Autofluorescence (v1)",
    "celldive-v0": "Cell DIVE (v0)",
    "celldive-v1": "Cell DIVE (v1)",
    "codex-v0": "CODEX (v0)",
    "codex-v1": "CODEX (v1)",
    "imc-v0": "IMC (v0)",
    "imc-v1": "IMC (v1)",
    "lightsheet-v0": "Light Sheet (v0)",
    "lightsheet-v1": "Light Sheet (v1)",
    "lightsheet-v2": "Light Sheet (v2)",
    "mibi-v1": "MIBI (v1)",
    "stained-v0": "Histology (v0)",
    "stained-v1": "Histology (v1)",
    # Legacy mass spec imaging schemas
    "ims-desi-v0": "IMS DESI (v0)",
    "ims-desi-v1": "IMS DESI (v1)",
    "ims-desi-v2": "IMS DESI (v2)",
    "ims-maldi-v0": "IMS MALDI (v0)",
    "ims-maldi-v1": "IMS MALDI (v1)",
    "ims-maldi-v2": "IMS MALDI (v2)",
    # Legacy LC-MS schemas
    "lcms-v0": "LC-MS (v0)",
    "lcms-v1": "LC-MS (v1)",
    "lcms-v2": "LC-MS (v2)",
    "lcms-v3": "LC-MS (v3)",
}


def get_header_label(header: str) -> str:
    """Get human-readable label for a schema version header."""
    return HEADER_LABELS.get(header, header)


# HTML template with HuBMAP color scheme
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Metadata Transformation Summary</title>
    <style>
        :root {
            --hubmap-primary: #444A65;
            --hubmap-light: #e8e9ed;
            --hubmap-dark: #363b52;
            --gray-light: #f5f5f5;
            --gray-border: #ddd;
            --text-dark: #333;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-dark);
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }

        h1 {
            color: var(--hubmap-primary);
            border-bottom: 3px solid var(--hubmap-primary);
            padding-bottom: 10px;
            margin-bottom: 30px;
        }

        h2 {
            color: var(--hubmap-dark);
            margin-top: 40px;
            margin-bottom: 20px;
        }

        .section {
            margin-bottom: 50px;
        }

        .table-container {
            overflow-x: auto;
            overflow-y: auto;
            max-height: 750px;
            margin-bottom: 20px;
        }

        .table-container th {
            position: sticky;
            top: 0;
            z-index: 1;
        }

        .table-container table {
            border-collapse: separate;
            border-spacing: 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th {
            background-color: var(--hubmap-primary);
            color: white;
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            border: 1px solid var(--hubmap-dark);
            white-space: nowrap;
        }

        td {
            padding: 10px;
            border: 1px solid var(--gray-border);
            vertical-align: top;
        }

        tr:nth-child(even) {
            background-color: var(--gray-light);
        }

        tr:hover {
            background-color: var(--hubmap-light);
        }

        /* Field mappings table */
        .field-mappings-container {
            max-height: 750px;
            overflow: auto;
            border: 1px solid var(--gray-border);
            border-radius: 4px;
        }

        .field-mappings-container table {
            border-collapse: separate;
            border-spacing: 0;
            min-width: max-content;
        }

        .field-mappings-container th,
        .field-mappings-container td {
            min-width: 150px;
        }

        .field-mappings-container th {
            position: sticky;
            top: 0;
            z-index: 1;
        }

        .field-mappings-container .target-header {
            position: sticky;
            right: 0;
            top: 0;
            z-index: 2;
            background-color: var(--hubmap-dark);
            box-shadow: -4px 0 8px rgba(0,0,0,0.15);
        }

        .field-mappings-container .target-cell {
            position: sticky;
            right: 0;
            background-color: #e8e9ed;
            font-weight: 500;
            box-shadow: -4px 0 8px rgba(0,0,0,0.1);
        }

        .field-mappings-container tr:nth-child(even) .target-cell {
            background-color: #d8dae0;
        }

        .field-mappings-container tr:hover .target-cell {
            background-color: #c8cad0;
        }

        .empty-cell {
            color: #999;
            font-style: italic;
        }

        .patch-list {
            list-style-type: none;
            padding: 0;
            max-height: 750px;
            overflow-y: auto;
        }

        .patch-item {
            background-color: var(--gray-light);
            border-left: 4px solid var(--hubmap-primary);
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
        }

        .patch-item:hover {
            background-color: var(--hubmap-light);
        }

        .patch-number {
            color: var(--hubmap-primary);
            font-weight: bold;
            margin-right: 10px;
        }

        .patch-action {
            color: var(--hubmap-dark);
            font-weight: 500;
        }

        .patch-context {
            font-weight: 500;
            color: var(--text-dark);
        }

        .patch-actions-list {
            margin: 10px 0 0 20px;
            padding-left: 0;
            list-style-type: disc;
        }

        .patch-actions-list li {
            margin-bottom: 5px;
        }

        code {
            background-color: var(--hubmap-light);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "SF Mono", Monaco, "Cascadia Code", monospace;
            font-size: 13px;
        }

        .summary-stats {
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }

        .stat-box {
            background-color: var(--hubmap-light);
            border: 1px solid var(--hubmap-primary);
            border-radius: 8px;
            padding: 15px 25px;
            text-align: center;
            text-decoration: none;
            display: block;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .stat-box:hover {
            background-color: var(--hubmap-primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        .stat-box:hover .stat-number,
        .stat-box:hover .stat-label {
            color: white;
        }

        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: var(--hubmap-primary);
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-dark);
        }

        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid var(--gray-border);
            font-size: 12px;
            color: #666;
            text-align: center;
        }

        .intro {
            margin-bottom: 20px;
            font-size: 15px;
            line-height: 1.7;
        }
    </style>
</head>
<body>
    <h1>{{ title }} - Metadata Transformation Summary</h1>

    <div class="summary-stats">
        <a href="#field-mappings" class="stat-box">
            <div class="stat-number">{{ field_mappings | length }}</div>
            <div class="stat-label">Field Mappings</div>
        </a>
        <a href="#value-mappings" class="stat-box">
            <div class="stat-number">{{ value_mappings | length }}</div>
            <div class="stat-label">Value Mappings</div>
        </a>
        <a href="#patches" class="stat-box">
            <div class="stat-number">{{ patches | length }}</div>
            <div class="stat-label">Conditional Patches</div>
        </a>
    </div>

    <div class="intro">
        <p>This report documents the transformation rules applied to convert legacy {{ title }} metadata into the current standardized schema. It provides transparency into how field names are mapped between schema versions, how values are standardized for consistency, and what conditional rules are applied to derive or correct metadata fields. Use this summary to understand the data lineage and transformation logic applied during the reharmonization process.</p>
    </div>

    <div class="section" id="field-mappings">
        <h2>1. Field Mappings</h2>
        <p>Maps legacy field names to target schema field names across different schema versions.</p>
        <div class="field-mappings-container">
            <table>
                <thead>
                    <tr>
                        {% for header in field_mapping_headers[1:] %}
                        <th>{{ header }}</th>
                        {% endfor %}
                        <th class="target-header">{{ field_mapping_headers[0] }}</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in field_mappings %}
                    <tr>
                        {% for cell in row[1:] %}
                        <td>{% if cell %}<code>{{ cell }}</code>{% else %}<span class="empty-cell">-</span>{% endif %}</td>
                        {% endfor %}
                        <td class="target-cell">{% if row[0] %}<code>{{ row[0] }}</code>{% else %}<span class="empty-cell">-</span>{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="section" id="value-mappings">
        <h2>2. Value Mappings</h2>
        <p>Standardizes field values from legacy formats to target schema values.</p>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Original Value</th>
                        <th>Standardized Value</th>
                    </tr>
                </thead>
                <tbody>
                    {% for mapping in value_mappings %}
                    <tr>
                        <td><code>{{ mapping.field }}</code></td>
                        <td><code>{{ mapping.old_value }}</code></td>
                        <td><code>{{ mapping.new_value }}</code></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="section" id="patches">
        <h2>3. Conditional Patches</h2>
        <p>Rule-based transformations applied when specific conditions are met.</p>
        <ul class="patch-list">
            {% for patch in patches %}
            <li class="patch-item">
                <span class="patch-number">#{{ loop.index }}</span>
                {{ patch }}
            </li>
            {% endfor %}
        </ul>
    </div>

    <div class="footer">
        Generated by generate-transformation-summary.py
    </div>
</body>
</html>
"""


def read_field_mappings_csv(csv_file: str) -> Tuple[List[str], List[List[str]]]:
    """
    Read field mappings CSV preserving the matrix format.

    Args:
        csv_file: Path to the field mappings CSV file

    Returns:
        Tuple of (headers, rows) where headers is the first row
        and rows is a list of data rows
    """
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: Field mapping CSV file '{csv_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    if len(rows) < 2:
        print("Error: CSV file must have at least 2 rows (header + data).", file=sys.stderr)
        sys.exit(1)

    headers = rows[0]
    data_rows = rows[1:]

    return headers, data_rows


def aggregate_value_mappings(output_dir: str) -> List[Dict[str, str]]:
    """
    Aggregate value mappings from all output JSON files, removing duplicates.

    Args:
        output_dir: Directory containing processed JSON files

    Returns:
        List of unique value mappings as dicts with field, old_value, new_value
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"Error: Output directory '{output_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    if not output_path.is_dir():
        print(f"Error: '{output_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Use a set of tuples for deduplication
    seen_mappings: Set[Tuple[str, str, str]] = set()

    json_files = list(output_path.glob("*.json"))

    if not json_files:
        print(f"Warning: No JSON files found in '{output_dir}'.", file=sys.stderr)
        return []

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            value_mappings = data.get('processing_log', {}).get('value_mappings', {})

            for field_name, mappings in value_mappings.items():
                if isinstance(mappings, dict):
                    for old_value, new_value in mappings.items():
                        seen_mappings.add((field_name, str(old_value), str(new_value)))

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON file '{json_file}': {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Error processing file '{json_file}': {e}", file=sys.stderr)

    # Convert to list of dicts, sorted by field name then old value
    result = [
        {"field": field, "old_value": old_val, "new_value": new_val}
        for field, old_val, new_val in sorted(seen_mappings)
    ]

    return result


def get_field_label(field: str) -> str:
    """
    Get human-readable label for a field name.

    Args:
        field: Technical field name

    Returns:
        Human-readable label
    """
    return FIELD_LABELS.get(field, field.replace("_", " "))


def format_condition_value(field: str, value: str) -> str:
    """
    Format a single condition with human-readable label.

    Args:
        field: Field name
        value: Field value

    Returns:
        Formatted phrase like "the assay type is 'bulk RNA'"
    """
    label = get_field_label(field)
    return f"the {label} is '<code>{value}</code>'"


def parse_conditions(conditions: Any) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
    """
    Parse conditions from a patch's 'when' clause.

    Args:
        conditions: The conditions dict or list

    Returns:
        Tuple of (must_conditions, should_groups) where:
        - must_conditions: List of formatted condition strings
        - should_groups: List of (field, values) tuples for OR conditions
    """
    must_conditions = []
    should_groups = []

    if isinstance(conditions, dict):
        must_list = conditions.get('__must__', [])

        for item in must_list:
            if isinstance(item, dict):
                if '__should__' in item:
                    # Handle nested __should__ (OR conditions)
                    should_items = item['__should__']
                    if should_items:
                        # Group by field name
                        field_values: Dict[str, List[str]] = {}
                        for should_item in should_items:
                            if isinstance(should_item, dict):
                                for field, value in should_item.items():
                                    if field not in ('__must__', '__should__'):
                                        if field not in field_values:
                                            field_values[field] = []
                                        field_values[field].append(str(value))

                        for field, values in field_values.items():
                            should_groups.append((field, values))
                else:
                    # Regular condition
                    for field, value in item.items():
                        if field not in ('__must__', '__should__'):
                            must_conditions.append(format_condition_value(field, str(value)))

    return must_conditions, should_groups


def format_actions_inline(then_clause: Dict[str, Any]) -> str:
    """
    Format actions as inline text (Option B - simple patches).

    Args:
        then_clause: Dict of field -> value actions

    Returns:
        Formatted actions string like "input entity as 'tissue (bulk)', barcode read as 'N/A'"
    """
    actions = []
    for field, value in then_clause.items():
        label = get_field_label(field)
        if value is None:
            actions.append(f"{label} as <code>null</code>")
        else:
            actions.append(f"{label} as '<code>{value}</code>'")

    return ", ".join(actions)


def format_actions_bullets(then_clause: Dict[str, Any]) -> str:
    """
    Format actions as bullet list (Option C - complex patches).

    Args:
        then_clause: Dict of field -> value actions

    Returns:
        HTML bullet list of actions
    """
    items = []
    for field, value in then_clause.items():
        label = get_field_label(field)
        if value is None:
            items.append(f"<li>Set {label} to <code>null</code></li>")
        else:
            items.append(f"<li>Set {label} to '<code>{value}</code>'</li>")

    return f"<ul class='patch-actions-list'>{''.join(items)}</ul>"


def narrate_patch(patch: Dict[str, Any]) -> str:
    """
    Convert a patch to human-readable narration.

    Uses Option B (inline) for simple patches with few actions,
    and Option C (bullet points) for complex patches with many actions.

    Args:
        patch: The patch dict with 'when' and 'then' clauses

    Returns:
        Human-readable narration string
    """
    when_clause = patch.get('when', {})
    then_clause = patch.get('then', {})

    must_conditions, should_groups = parse_conditions(when_clause)

    # Determine if this is a complex patch (use bullets) or simple (use inline)
    is_complex = len(then_clause) >= COMPLEX_PATCH_THRESHOLD

    # Build condition parts
    parts = []

    if must_conditions:
        parts.extend(must_conditions)

    if should_groups:
        for field, values in should_groups:
            label = get_field_label(field)
            if len(values) == 1:
                parts.append(f"the {label} is '<code>{values[0]}</code>'")
            else:
                values_str = ", ".join([f"'<code>{v}</code>'" for v in values])
                parts.append(f"the {label} is one of [{values_str}]")

    # Format the narration based on complexity
    if parts:
        conditions_text = " and ".join(parts)
        if is_complex:
            # Option C: Bullet points for complex patches
            actions = format_actions_bullets(then_clause)
            return f"<span class='patch-context'>When {conditions_text}:</span>{actions}"
        else:
            # Option B: Inline for simple patches
            actions = format_actions_inline(then_clause)
            return f"When {conditions_text}: <span class='patch-action'>Sets</span> {actions}."
    else:
        # No conditions - just actions
        if is_complex:
            actions = format_actions_bullets(then_clause)
            return f"<span class='patch-context'>Always apply:</span>{actions}"
        else:
            actions = format_actions_inline(then_clause)
            return f"<span class='patch-action'>Sets</span> {actions}."


def read_patches(patch_file: str) -> List[str]:
    """
    Read patches from JSON file and convert to narrations.

    Args:
        patch_file: Path to the patches JSON file

    Returns:
        List of human-readable patch narrations
    """
    try:
        with open(patch_file, 'r', encoding='utf-8') as f:
            patches = json.load(f)
    except FileNotFoundError:
        print(f"Error: Patch file '{patch_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse patch file: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(patches, list):
        print("Error: Patch file must contain a JSON array.", file=sys.stderr)
        sys.exit(1)

    narrations = []
    for patch in patches:
        narration = narrate_patch(patch)
        narrations.append(narration)

    return narrations


def generate_html(
    title: str,
    field_mapping_headers: List[str],
    field_mappings: List[List[str]],
    value_mappings: List[Dict[str, str]],
    patches: List[str]
) -> str:
    """
    Generate HTML report using Jinja2 template.

    Args:
        title: Report title (assay type)
        field_mapping_headers: CSV header row
        field_mappings: CSV data rows
        value_mappings: List of value mapping dicts
        patches: List of patch narrations

    Returns:
        Generated HTML string
    """
    template = Template(HTML_TEMPLATE)

    # Transform headers to human-readable labels
    display_headers = [get_header_label(h) for h in field_mapping_headers]

    return template.render(
        title=title,
        field_mapping_headers=display_headers,
        field_mappings=field_mappings,
        value_mappings=value_mappings,
        patches=patches
    )


def generate_transformation_summary(
    field_mapping_csv: str,
    output_dir: str,
    patch_file: str,
    title: str,
    output_file: str
):
    """
    Generate the complete transformation summary HTML report.

    Args:
        field_mapping_csv: Path to field mappings CSV file
        output_dir: Directory containing processed JSON files
        patch_file: Path to patches JSON file
        title: Report title (assay type)
        output_file: Path to output HTML file
    """
    # Read field mappings from CSV
    headers, field_mappings = read_field_mappings_csv(field_mapping_csv)

    # Aggregate value mappings from output files
    value_mappings = aggregate_value_mappings(output_dir)

    # Read and narrate patches
    patches = read_patches(patch_file)

    # Generate HTML
    html_content = generate_html(
        title=title,
        field_mapping_headers=headers,
        field_mappings=field_mappings,
        value_mappings=value_mappings,
        patches=patches
    )

    # Write output file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    print(f"Transformation summary saved to: {output_file}")
    print(f"  Field mappings: {len(field_mappings)} rows")
    print(f"  Value mappings: {len(value_mappings)} unique mappings")
    print(f"  Patches: {len(patches)} rules")


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Generate HTML transformation summary report for metadata"
    )
    parser.add_argument(
        "--field-mapping-csv",
        required=True,
        help="Path to field mappings CSV file"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory containing processed output JSON files"
    )
    parser.add_argument(
        "--patch-file",
        required=True,
        help="Path to patches JSON file"
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Report title (e.g., 'RNAseq', 'CODEX')"
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Path to output HTML file"
    )

    args = parser.parse_args()

    generate_transformation_summary(
        field_mapping_csv=args.field_mapping_csv,
        output_dir=args.output_dir,
        patch_file=args.patch_file,
        title=args.title,
        output_file=args.output_file
    )


if __name__ == "__main__":
    main()
