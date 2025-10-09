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
python find-nonstandard-values.py metadata/rnaseq/output metadata/rnaseq/rnaseq-schema.json rnaseq-nonstandard-values.json

# Find non-standard values from ATACseq processed metadata
python find-nonstandard-values.py metadata/atacseq/output metadata/atacseq/atacseq-schema.json atacseq-nonstandard-values.json
```

**How it works (two detection approaches):**

1. **Null Mappings Detection:**
   - Examines `processing_log/value_mappings` in processed JSON files
   - Identifies fields where legacy values map to `null` (no standard mapping available)

2. **Non-Standard Values Detection:**
   - Checks values in `modified_metadata` against schema's standardized `permissible_values`
   - Flags values that aren't in the standardized value set for categorical fields

3. **Merges both results:**
   - Aggregates all non-standard values across all files
   - Deduplicates automatically
   - Outputs single values as strings, multiple values as arrays

**Input:**
- Directory containing processed metadata JSON files
- Schema JSON file with standardized permissible value definitions

**Output:** JSON object with non-standard values
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
| `find-nonstandard-values.py` | Processed JSON directory + Schema file | JSON file | Find non-standard values not in standardized value set for curator review |

---

## Integration

These scripts are used in GitHub Actions workflows (`.github/workflows/transform-rnaseq.yml`) to automate metadata transformation processes.
