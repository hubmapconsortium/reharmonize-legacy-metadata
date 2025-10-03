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

### 3. `find-values-for-review.py`

Identifies legacy values that could not be mapped to standard values, requiring domain expert review to determine if they should be added to the standard value set.

**Usage:**
```bash
python find-values-for-review.py <input_dir> <output_json>
```

**Examples:**
```bash
# Find unmapped values from LC-MS processed metadata
python find-values-for-review.py metadata/lcms/output lcms-values-for-review.json

# Find unmapped values from RNAseq processed metadata
python find-values-for-review.py metadata/rnaseq/output rnaseq-values-for-review.json
```

**How it works:**
- Examines `processing_log/value_mappings` in processed JSON files
- Identifies fields where legacy values map to `null` (no standard value found)
- Aggregates unmapped values across all files (deduplicates automatically)
- Outputs single values as strings, multiple values as arrays

**Input:** Directory containing processed metadata JSON files with `processing_log/value_mappings`

**Output:** JSON object with fields requiring review
```json
{
  "lc_column_vendor": ["Agilent Technologies", "Millipore", "Self-packed"],
  "ms_scan_mode": "MS/MS"
}
```

**Use case:** After transformation, review these values with domain experts to decide:
- Should the legacy value be added to the standard?
- Is it a data quality issue?
- Should it map to an existing standard value?

---

## Quick Reference

| Script | Input | Output | Use Case |
|--------|-------|--------|----------|
| `generate-field-mapping.py` | CSV file | JSON file | Map legacy → target fields |
| `generate-target-schema.py` | YAML URL or file path | JSON file | Generate simplified metadata schema from CEDAR template |
| `find-values-for-review.py` | Processed JSON directory | JSON file | Identify unmapped legacy values for expert review |

---

## Integration

These scripts are used in GitHub Actions workflows (`.github/workflows/transform-rnaseq.yml`) to automate metadata transformation processes.
