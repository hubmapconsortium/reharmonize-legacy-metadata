# Metadata Transformer

A Python tool for transforming legacy metadata objects into new schema-compliant structures.

## Overview

This tool processes legacy metadata files and transforms them according to specified field mappings, value mappings, and target schemas. It supports both bulk directory processing and single file processing.

## Features

- **Conditional Patching**: Apply patches to metadata based on conditions before transformation (Phase 0)
- **Field Mapping**: Transforms legacy field names to target schema field names (Phase 1)
- **Value Mapping**: Transforms legacy field values to target schema values (Phase 2)
- **Schema Compliance**: Ensures output conforms to target schema requirements (Phase 3)
- **Comprehensive Logging**: Structured processing log tracks all transformations and reports excluded fields (Phase 4)
- **Flexible Processing**: Supports both bulk and single file processing modes
- **CLI Interface**: Easy-to-use command-line interface with Click

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Usage

### Bulk Processing (entire directory)
```bash
metadata-transform \
  --field-mapping-file <field-mapping-file.json> \
  --value-mapping-dir <value-mapping-dir> \
  --target-schema-file <schema-file.json> \
  --input-dir <legacy-metadata-dir> \
  --output-dir <output-dir>
```

### Single File Processing
```bash
metadata-transform \
  --field-mapping-file <field-mapping-file.json> \
  --value-mapping-dir <value-mapping-dir> \
  --target-schema-file <schema-file.json> \
  --input-file <legacy-metadata-file.json> \
  --output-dir <output-dir>
```

### With Optional Patches (Directory)
```bash
metadata-transform \
  --field-mapping-file <field-mapping-file.json> \
  --value-mapping-dir <value-mapping-dir> \
  --target-schema-file <schema-file.json> \
  --patches-dir <patches-dir> \
  --input-file <legacy-metadata-file.json> \
  --output-dir <output-dir>
```

### With Optional Patches (Single File)
```bash
metadata-transform \
  --field-mapping-file <field-mapping-file.json> \
  --value-mapping-dir <value-mapping-dir> \
  --target-schema-file <schema-file.json> \
  --patches-file <patch-file.json> \
  --input-file <legacy-metadata-file.json> \
  --output-dir <output-dir>
```

## Arguments

- `--field-mapping-file`: JSON file containing field name mappings (required)
- `--value-mapping-dir`: Directory containing JSON value mapping files (required)
- `--target-schema-file`: Path to target schema JSON file (required)
- `--patches-dir`: Directory containing JSON patch files for conditional patching (optional)
- `--patches-file`: Single JSON patch file for conditional patching (optional, can be used with --patches-dir)
- `--input-dir`: Directory containing legacy metadata files for bulk processing (mutually exclusive with --input-file)
- `--input-file`: Path to single legacy metadata file to process (mutually exclusive with --input-dir)
- `--output-dir`: Directory where transformed files will be written (required)
- `--verbose`, `-v`: Enable verbose output (optional)

## Output Format

Each transformed file contains:
```json
{
  "metadata": {
    // Original metadata from input file
  },
  "modified_metadata": {
    // Transformed metadata compliant with target schema
  },
  "processing_log": {
    "field_mappings": {
      // Legacy field name to target field name mappings
    },
    "value_mappings": {
      // Field-specific value transformations
    },
    "ambiguous_mappings": [
      // Values that couldn't be mapped automatically
    ],
    "excluded_data": {
      // Fields that don't map to target schema
    },
    "metadata_patches": [
      // Patches that were applied in Phase 0
    ]
  }
}
```

## Development

### Setup Development Environment

```bash
# Create and activate virtual environment (from tools directory)
cd /path/to/tools
python3 -m venv .venv
source .venv/bin/activate

# Install package with dev dependencies (from metadata-transformer directory)
cd metadata-transformer
pip install -e ".[dev]"
```

### Running Tests
```bash
# Activate virtual environment first
source ../.venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov

# Run specific test file
pytest tests/test_field_mapper.py
```

### Code Formatting
```bash
black src/ tests/
isort src/ tests/
```

### Linting
```bash
flake8 src/ tests/
mypy src/
```