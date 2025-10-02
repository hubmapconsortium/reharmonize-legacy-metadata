# Value Mapping Guide

## Overview

Value mapping files are used to transform legacy field values into standardized target values during metadata transformation. These mappings ensure consistency and standardization across datasets by converting various legacy representations into unified terminology.

## File Format

Value mapping files are stored in **JSON format** with a specific structure:

```json
{
  "field_name": {
    "legacy_value": "target_value"
  }
}
```

### Structure Components

1. **Root Key**: The field name that this mapping applies to (e.g., `"library_layout"`, `"is_targeted"`, `"dataset_type"`)
2. **Nested Object**: A key-value mapping where:
   - **Key**: The legacy value from the source data
   - **Value**: The target value to transform to (can be `string`, `array`, or `null`)

## Value Types

### String Values (Standard Mapping)

The most common case: a legacy value maps to a single target value.

**Example 1**:
```json
{
  "library_layout": {
    "single": "single-end"
  }
}
```

**Example 2**:
```json
{
  "is_targeted": {
    "TRUE": "Yes",
    "True": "Yes",
    "FALSE": "No",
    "False": "No"
  }
}
```

### Null Values (No Mapping Available)

When `null` is used as the target value, it indicates that no suitable mapping has been determined yet.

**Example**:
```json
{
  "dataset_type": {
    "WGS": null,
    "3D Imaging Mass Cytometry": null,
    "seqFISH": null
  }
}
```

**Use case**: Indicates that this legacy value needs further review to determine the appropriate target value.

### Array Values (Ambiguous Cases)

When the target value is an **array**, it indicates an **ambiguous case** where the legacy value could map to multiple possible target values. These require manual review by domain experts.

**Example**:
```json
{
  "ms_scan_mode": {
    "MS": [
      "MS1",
      "MS2",
      "MS3"
    ]
  }
}
```

**Use case**: The legacy value "MS" is ambiguous and could refer to MS1, MS2, or MS3 scan modes. Domain experts must review the source data context to determine the correct value.

## Creating a Value Mapping File

### Step 1: Identify the Field

Determine which field requires value mapping. The filename should match the field name:
- Field: `acquisition_instrument_vendor`
- Filename: `acquisition_instrument_vendor.json`

### Step 2: Collect Legacy Values

Gather all unique values from the legacy data for this field.

### Step 3: Determine Target Values

For each legacy value, determine the appropriate target value:
- Use standardized terminology
- Normalize variations (e.g., "Thermo", "ThermoFisher", "Thermo Scientific" → "Thermo Fisher Scientific")
- Use `null` if no mapping is determined yet
- Use an array if multiple valid target values exist

### Step 4: Create the JSON File

```json
{
  "field_name": {
    "Legacy Value 1": "Target Value 1",
    "Legacy Value 2": "Target Value 2",
    "Ambiguous Value": ["Option A", "Option B"],
    "Undetermined Value": null
  }
}
```

## Complete Example

```json
{
  "acquisition_instrument_vendor": {
    "Thermo": "Thermo Fisher Scientific",
    "Thermo Fisher": "Thermo Fisher Scientific",
    "ThermoFisher": "Thermo Fisher Scientific",
    "Carl Zeiss Microscopy": "Zeiss Microscopy",
    "Zeiss": "Zeiss Microscopy",
    "Bruker Daltonics": "Bruker",
    "Fluidigm": "Standard BioTools (Fluidigm)",
    "Waters Corp.": null,
    "Andor sCMOS Camera": null
  }
}
```