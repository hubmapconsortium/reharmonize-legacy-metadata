# json-conditional-patch

A Python library for applying conditional JSON patches based on logical rules.

## Overview

`json-conditional-patch` provides a powerful way to conditionally modify JSON objects based on their content. It uses a rule-based system with `__must__` (AND) and `__should__` (OR) operators to evaluate conditions and apply patches when those conditions are met.

## Features

- **Conditional patching**: Apply patches only when specific conditions are met
- **Logical operators**: Use `__must__` (AND) and `__should__` (OR) for complex logic
- **Nested conditions**: Support for deeply nested logical expressions
- **Multi-field matching**: Implicit AND when multiple fields are in a single condition
- **Thread-safe**: Immutable applier instances for concurrent use
- **Zero dependencies**: Uses only Python standard library

## Installation

```bash
pip install json-conditional-patch
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from json_conditional_patch import Patches, PatchApplier

# Load patches from a directory
patches = Patches()
patches.load_patch_dir("path/to/patches/")

# Or load from a single file
patches.load_patch_file("path/to/patch.json")

# Create an applier
applier = patches.get_applier()

# Apply patches to your data
data = {"assay_type": "RNA-seq", "version": "1.0"}
result = applier.apply_patches(data)
```

## Patch Format

Patches are defined in JSON files with a `when`/`then` structure:

```json
[
  {
    "when": {
      "__must__": [
        {"assay_type": "RNA-seq"}
      ]
    },
    "then": {
      "standardized_assay": "rnaseq",
      "technology": "sequencing"
    }
  }
]
```

### Condition Syntax

#### `__must__` - AND Logic

All conditions in a `__must__` array must be true:

```json
{
  "when": {
    "__must__": [
      {"field1": "value1"},
      {"field2": "value2"}
    ]
  },
  "then": {"result": "applied"}
}
```

#### `__should__` - OR Logic

At least one condition in a `__should__` array must be true:

```json
{
  "when": {
    "__should__": [
      {"protocol": "v1"},
      {"protocol": "v2"}
    ]
  },
  "then": {"protocol_version": "legacy"}
}
```

#### Nested Logic

Combine `__must__` and `__should__` for complex conditions:

```json
{
  "when": {
    "__must__": [
      {"assay_type": "RNA-seq"},
      {
        "__should__": [
          {"protocol": "v1"},
          {"protocol": "v2"}
        ]
      }
    ]
  },
  "then": {"standardized": true}
}
```

#### Multi-field Conditions

Multiple fields in a single object use implicit AND:

```json
{
  "when": {
    "__must__": [
      {"field1": "value1", "field2": "value2"}
    ]
  },
  "then": {"result": "both matched"}
}
```

## API Reference

### `Patches`

Repository for loading and storing patch rules.

#### Methods

- `__init__()`: Initialize an empty Patches repository
- `load_patch_dir(patches_dir: Path)`: Load all JSON patch files from a directory recursively
- `load_patch_file(patch_file: Path)`: Load patches from a single file
- `get_applier() -> PatchApplier`: Create a new PatchApplier instance
- `get_all_patches() -> List[Dict[str, Any]]`: Get all loaded patches
- `get_loaded_patches_count() -> int`: Get the count of loaded patches

### `PatchApplier`

Immutable applier for applying conditional patches.

#### Methods

- `__init__(patches: List[Dict[str, Any]])`: Initialize with a list of patches
- `apply_patches(metadata: Dict[str, Any]) -> Dict[str, Any]`: Apply patches and return modified metadata
- `get_all_patches() -> List[Dict[str, Any]]`: Get all patches
- `get_loaded_patches_count() -> int`: Get the count of patches

### `PatchError`

Exception raised when there are issues with patch operations.

## Examples

### Basic Patching

```python
from json_conditional_patch import Patches

# Create and load patches
patches = Patches()
patches.load_patch_file("my_patches.json")

# Apply to data
applier = patches.get_applier()
data = {"type": "experiment", "status": "active"}
result = applier.apply_patches(data)
```

### Multiple Patch Files

```python
from pathlib import Path
from json_conditional_patch import Patches

patches = Patches()

# Load from directory (recursive)
patches.load_patch_dir(Path("patches/"))

# Add additional patches from a specific file
patches.load_patch_file(Path("special_patches.json"))

print(f"Loaded {patches.get_loaded_patches_count()} patches")
```

### Complex Conditions

```python
# patches.json
[
  {
    "when": {
      "__must__": [
        {"dataset_type": "imaging"},
        {
          "__should__": [
            {"modality": "MRI"},
            {"modality": "CT"},
            {"modality": "PET"}
          ]
        }
      ]
    },
    "then": {
      "category": "medical_imaging",
      "requires_review": true
    }
  }
]
```

## Development

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

### Linting

```bash
flake8 src/ tests/
```

## License

MIT License

## Author

Josef Hardi (johardi@stanford.edu)

## Contributing

Contributions are welcome! Please ensure all tests pass and code is properly formatted before submitting a pull request.
