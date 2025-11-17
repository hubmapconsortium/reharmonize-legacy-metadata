# Metadata Transformation Scripts

This directory contains utility scripts for generating field mappings, target schemas, and identifying values requiring expert review in metadata transformation workflows.

---

## Scripts

### 1. `generate-field-mapping.py`

Generates JSON field mappings from CSV files that map legacy field names to target field names.

**Usage:**
```bash
python generate-field-mapping.py <input_csv> <output_json>
```

**Example:**
```bash
python generate-field-mapping.py mappings/field-mapping/rnaseq.csv mappings/field-mapping/rnaseq.json
```

**CSV Format:**
- Column 1: Target field names (new schema)
- Columns 2+: Legacy field names (old schemas)

**Output:** JSON object mapping legacy fields to target fields
```json
{
  "legacy_field": "target_field",
  "old_name": "new_name"
}
```

---

### 2. `generate-target-schema.py`

Fetches a YAML schema from a URL or local file and converts it to simplified JSON format for validation.

**Usage:**
```bash
python generate-target-schema.py <yaml_source> <output_json>
```

**Examples:**
```bash
# From remote URL:
python generate-target-schema.py \
  "https://raw.githubusercontent.com/hubmapconsortium/dataset-metadata-spreadsheet/refs/heads/main/rnaseq/latest/rnaseq.yml" \
  schemas/rnaseq.json

# From local file:
python generate-target-schema.py \
  local/schema.yml \
  schemas/output.json
```

**Output:** JSON array of field definitions
```json
[
  {
    "name": "field_name",
    "description": "Field description",
    "type": "text",
    "required": true,
    "regex": null,
    "default_value": null,
    "permissible_values": null
  }
]
```

**Requirements:**
- PyYAML: `pip install PyYAML`

---

### 3. `find-nonstandard-values.py`

Identifies non-standard values from modified metadata that are not in the standardized value set. These values require review by domain experts and data curators to determine if they should be added to the standard or corrected.

**Usage:**
```bash
python find-nonstandard-values.py <input_dir> <schema_file> <output_json>
```

**Examples:**
```bash
# Find non-standard values from RNAseq processed metadata
python find-nonstandard-values.py \
  metadata/rnaseq/output \
  metadata/rnaseq/rnaseq-schema.json \
  metadata/rnaseq/rnaseq-nonstandard-values.json

# This generates:
# - metadata/rnaseq/rnaseq-nonstandard-values.json (aggregated JSON)
# - metadata/rnaseq/todo/ folder with:
#   - Excel files grouped by group_name:
#     - University of California San Diego TMC (RNAseq).xlsx
#     - Stanford TMC (RNAseq).xlsx
#     - etc.
#   - summary-report.json (dataset counts per group)

# Find non-standard values from ATACseq processed metadata
python find-nonstandard-values.py \
  metadata/atacseq/output \
  metadata/atacseq/atacseq-schema.json \
  metadata/atacseq/atacseq-nonstandard-values.json
```

**How it works (three detection approaches):**

1. **Non-Permissible Values Detection:**
   - Checks values in `modified_metadata` against schema's standardized `permissible_values`
   - Flags values that aren't in the standardized value set for categorical fields

2. **Missing Required Values Detection:**
   - Identifies required fields that have null or empty values in `modified_metadata`
   - Ensures all mandatory fields are properly populated

3. **Regex Pattern Violations Detection:**
   - Validates values against regex constraints defined in the schema
   - Flags values that don't match expected patterns

4. **Aggregation:**
   - Merges all three detection results
   - Aggregates across all files and deduplicates
   - Outputs single values as strings, multiple values as arrays

**Input:**
- Directory containing processed metadata JSON files
- Schema JSON file with standardized permissible value definitions

**Output Formats:**

The script automatically generates both JSON and Excel outputs:

**1. JSON Output (aggregated across all files):**

Single file with all non-standard values across all datasets:
```json
{
  "sequencing_reagent_kit": [
    "10X_scRNASeq_protocol",
    "NovaSeq 6000 S1",
    "P2"
  ],
  "barcode_offset": "1",
  "acquisition_instrument_model": "NovaSeq"
}
```

**2. Excel Spreadsheet Output (grouped by group_name):**

Automatically generates a `todo/` folder next to the JSON output, containing one Excel file per group_name:
- `{Group Name} ({DatasetType}).xlsx`

Example for RNAseq:
- `metadata/rnaseq/todo/University of California San Diego TMC (RNAseq).xlsx`
- `metadata/rnaseq/todo/Stanford TMC (RNAseq).xlsx`
- `metadata/rnaseq/todo/University of Florida TMC (RNAseq).xlsx`
- `metadata/rnaseq/todo/TMC - University of California San Diego focusing on female reproduction (RNAseq).xlsx`
- etc.

Each Excel workbook contains 3 sheets:

- **Non-Standard Value**: Values not in schema's permissible values list
  - Columns: Dataset ID, Field Name, Current Value, New Value, Dataset URL

- **Missing Required Value**: Required fields with null/empty values
  - Columns: Dataset ID, Field Name, New Value, Dataset URL

- **Invalid Input Pattern**: Values that don't match regex constraints
  - Columns: Dataset ID, Field Name, Current Value, New Value, Expected Input Hint, Dataset URL

Each sheet lists issues per dataset, with datasets sorted alphabetically. Dataset ID and URL appear in all rows for easier data filtering. Excel's AutoFilter is enabled on header rows for convenient filtering and sorting.

**Excel Features:**
- **Dropdown Validations**: New Value columns have dropdowns with permissible values from the schema
- **AutoFilter**: Enabled on header rows for easy filtering by Dataset ID, Field Name, etc.
- **Expected Input Hints**: Human-readable descriptions of regex patterns for non-technical users
- **Dataset URLs**: Clickable links to HubMAP portal for each dataset

**3. Summary Report (JSON format):**

Located in `todo/summary-report.json`, this file provides a high-level overview of issues per group:

```json
[
  {
    "group_name": "University of California San Diego TMC",
    "dataset_type": "RNAseq",
    "datasets_with_non_standard_values": 465,
    "datasets_with_missing_required_values": 465,
    "datasets_with_invalid_input_patterns": 465,
    "total_datasets_with_issues": 465
  },
  {
    "group_name": "Stanford TMC",
    "dataset_type": "RNAseq",
    "datasets_with_non_standard_values": 89,
    "datasets_with_missing_required_values": 92,
    "datasets_with_invalid_input_patterns": 92,
    "total_datasets_with_issues": 92
  }
]
```

The summary report shows:
- **group_name**: Institution/group name
- **dataset_type**: Type of datasets (e.g., RNAseq, ATACseq)
- **datasets_with_non_standard_values**: Count of unique datasets with non-permissible values
- **datasets_with_missing_required_values**: Count of unique datasets missing required values
- **datasets_with_invalid_input_patterns**: Count of unique datasets with regex violations
- **total_datasets_with_issues**: Count of unique datasets with any issues (deduplicated)

**Requirements for Excel and summary outputs:**
- openpyxl: `pip install openpyxl`

**Use case:** After transformation, review these values with domain experts and data curators to decide:
- Should the non-standard value be added to the standardized value set?
- Is it a data quality issue that needs correction?
- Should it map to an existing standardized value?
- Is the schema definition incomplete or outdated?

---

## Quick Reference

| Script | Input | Output | Use Case |
|--------|-------|--------|----------|
| `generate-field-mapping.py` | CSV file | JSON file | Map legacy → target fields |
| `generate-target-schema.py` | YAML URL or file path | JSON file | Generate simplified metadata schema from CEDAR template |
| `find-nonstandard-values.py` | Processed JSON directory + Schema file | JSON file + todo/ folder with grouped Excel files | Find non-standard values not in standardized value set for curator review |

---

## Integration

These scripts are used in GitHub Actions workflows (`.github/workflows/transform-rnaseq.yml`) to automate metadata transformation processes.
