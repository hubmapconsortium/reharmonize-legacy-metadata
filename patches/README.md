# Metadata Patch Objects Documentation

## Overview

Patch objects are conditional metadata transformations that apply field values based on specific criteria in the source metadata.

## Patch Object Structure

```json
{
  "when": {
    "must": {
      "legacy_field": "legacy_value"
    },
    "should": {
      "legacy_name1": "legacy_value1",
      "legacy_name2": "legacy_value2"
    }
  },
  "then": {
    "target_field1": "target_value1",
    "target_field2": "target_value2"
  }
}
```

## Structure Components

### `when` Clause - Conditional Logic

The `when` clause defines the conditions that must be met for the patch to be applied. It supports two types of conditions:

#### `must` Conditions (AND Logic)
- **Type**: Object
- **Logic**: ALL conditions must be true for the patch to apply
- **Description**: Required field-value pairs that must exactly match the source metadata

Example:
Apply the patch if the assay_type is "SNARE2-RNAseq" AND version is "v2".
```json
"must": {
  "assay_type": "SNARE2-RNAseq",
  "version": "v2"
}
```



#### `should` Conditions (OR Logic)  
- **Type**: Object
- **Logic**: ANY condition must be true for the patch to apply
- **Description**: Optional field-value pairs where at least one must match

Example:
Apply the patch if either the assay_type is "SNARE2-RNAseq" OR version is "v2".
```json
"should": {
  "assay_type": "SNARE2-RNAseq",
  "version": "v2"
}
```

#### Combined Logic
When both `must` and `should` are present:
1. **ALL** `must` conditions must be satisfied (AND logic)
2. **ANY** `should` condition must be satisfied (OR logic)
3. Both groups must pass for the patch to apply

Example:
Apply the patch if the assay_type is "SNARE2-RNAseq" AND version is "v2", and either the analyte_class is "DNA" OR assay_category is "sequence".
```json
"must": {
  "assay_type": "SNARE2-RNAseq",
  "version": "v2"
},
"should": {
  "analyte_class": "DNA",
  "assay_category": "sequence"
}
```


### `then` Clause - Field Assignments

The `then` clause defines the field values to set when conditions are met:

- **Type**: Object
- **Description**: Key-value pairs of field names and their assigned values
- **Behavior**: Values are set directly on the metadata object
- **Overwriting**: Later patches can overwrite earlier patch values

Example:
If the conditions are met then insert (or overwrite) assay_input_entity to "single nucleus", barcode_read to "Read 2 (R2)", and umi_offset to "0".
```json
"then": {
  "assay_input_entity": "single nucleus",
  "barcode_read": "Read 2 (R2)",
  "umi_offset": "0"
}
```

### Example Patch File

```json
[
  {
    "when": {
      "must": {
        "assay_type": "SNARE2-RNAseq"
      }
    },
    "then": {
      "assay_input_entity": "single nucleus",
      "barcode_read": "Read 2 (R2)",
      "barcode_size": "8,8,8",
      "barcode_offset": "10,48,86",
      "umi_read": "Read 2 (R2)",
      "umi_size": "10",
      "umi_offset": "0"
    }
  },
  {
    "when": {
      "must": {
        "assay_type": "bulkATACseq"
      }
    },
    "then": {
      "assay_input_entity": "tissue (bulk)",
      "barcode_read": "Not applicable",
      "barcode_size": "Not applicable",
      "barcode_offset": "Not applicable",
      "umi_read": "Not applicable",
      "umi_size": "Not applicable",
      "umi_offset": "Not applicable"
    }
  }
]
```

## Processing Logic

### Evaluation Process

1. **Condition Evaluation**: For each patch, the `when` clause is evaluated against the source metadata
2. **Field Assignment**: If conditions match, all fields in the `then` clause are applied to the metadata
3. **Sequential Application**: Patches are applied in file sort order, with later patches potentially overwriting earlier ones
4. **Logging**: Applied patches are logged with field name, value, and triggering conditions


## Use Cases and Examples

### Single Condition Patch

Set entity type based on assay:

```json
{
  "when": {
    "must": {
      "assay_type": "snRNAseq"
    }
  },
  "then": {
    "assay_input_entity": "single nucleus"
  }
}
```

### Multi-Field Assignment

Configure multiple sequencing parameters for 10x Genomics v3:

```json
{
  "when": {
    "must": {
      "assay_type": "scRNAseq-10xGenomics-v3"
    }
  },
  "then": {
    "assay_input_entity": "single cell",
    "barcode_read": "Read 1 (R1)",
    "barcode_size": "16",
    "barcode_offset": "0",
    "umi_read": "Read 1 (R1)",
    "umi_size": "12",
    "umi_offset": "16"
  }
}
```

### Conditional Logic with Multiple Conditions

Apply patch when assay type matches AND protocol version is specific:

```json
{
  "when": {
    "must": {
      "assay_type": "custom_protocol",
      "protocol_version": "2.1"
    }
  },
  "then": {
    "processing_method": "enhanced",
    "quality_threshold": "0.95"
  }
}
```

### Flexible Matching with Should Conditions

Apply patch if any of several protocol identifiers match:

```json
{
  "when": {
    "should": {
      "protocol_name": "standard_v1",
      "protocol_id": "STD-001",
      "method": "standard"
    }
  },
  "then": {
    "standardized_protocol": "true"
  }
}
```