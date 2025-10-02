# Metadata Transformation Scripts

This directory contains utility scripts for generating field mappings and target schemas used in metadata transformation workflows.

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

## Quick Reference

| Script | Input | Output | Use Case |
|--------|-------|--------|----------|
| `generate-field-mapping.py` | CSV file | JSON file | Map legacy → target fields |
| `generate-target-schema.py` | YAML URL or file path | JSON file | Generate simplified metadata schema from CEDAR template |

---

## Integration

These scripts are used in GitHub Actions workflows (`.github/workflows/transform-rnaseq.yml`) to automate metadata transformation processes.
