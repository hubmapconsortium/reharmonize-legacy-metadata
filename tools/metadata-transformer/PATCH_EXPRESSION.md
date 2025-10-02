# Patch Expression Syntax

This document describes the syntax for writing conditional patch expressions in the metadata transformer.

## Overview

Patches allow you to conditionally modify metadata **before** field and value mapping occurs. Each patch consists of:
- A `when` clause that defines conditions
- A `then` clause that defines what fields to set when conditions match

## Basic Structure

```json
[
  {
    "when": { /* conditions */ },
    "then": { /* fields to set */ }
  }
]
```

## Condition Operators

### `__must__` (AND Operator)

All items in the `__must__` array must evaluate to true.

**Syntax:**
```json
{
  "when": {
    "__must__": [
      /* array of conditions - ALL must be true */
    ]
  }
}
```

**Example:**
```json
{
  "when": {
    "__must__": [
      {"assay_type": "RNA-seq"},
      {"protocol_version": "v2"}
    ]
  },
  "then": {
    "standardized_assay": "rna_sequencing_v2"
  }
}
```

This patch applies when **both** `assay_type` is "RNA-seq" **AND** `protocol_version` is "v2".

### `__should__` (OR Operator)

At least one item in the `__should__` array must evaluate to true.

**Syntax:**
```json
{
  "when": {
    "__should__": [
      /* array of conditions - ANY must be true */
    ]
  }
}
```

**Example:**
```json
{
  "when": {
    "__should__": [
      {"donor_status": "deceased"},
      {"donor_status": "living"}
    ]
  },
  "then": {
    "donor_type": "human"
  }
}
```

This patch applies when `donor_status` is **either** "deceased" **OR** "living".

## Simple Field Matching

### Single Field

```json
{"field_name": "expected_value"}
```

Evaluates to true when `metadata["field_name"]` equals `"expected_value"`.

### Multiple Fields (Implicit AND)

```json
{"field1": "value1", "field2": "value2"}
```

Evaluates to true when **all** fields match (implicit AND within the object).

## Nested Logic

You can nest `__must__` and `__should__` operators to create complex logical expressions.

### Example 1: AND with nested OR

**Logic:** `A AND (B OR C) AND (D OR E)`

```json
{
  "when": {
    "__must__": [
      {"field0": "value0"},           // A
      {
        "__should__": [                // B OR C
          {"field1": "value1"},        // B
          {"field2": "value2"}         // C
        ]
      },
      {
        "__should__": [                // D OR E
          {"field3": "value3"},        // D
          {"field4": "value4"}         // E
        ]
      }
    ]
  },
  "then": {
    "complex_match": "true"
  }
}
```

**Applies when:**
- `field0` is "value0" AND
- (`field1` is "value1" OR `field2` is "value2") AND
- (`field3` is "value3" OR `field4` is "value4")

### Example 2: OR with nested AND

**Logic:** `A OR (B AND C) OR (D AND E)`

```json
{
  "when": {
    "__should__": [
      {"field0": "value0"},           // A
      {
        "__must__": [                  // B AND C
          {"field1": "value1"},        // B
          {"field2": "value2"}         // C
        ]
      },
      {
        "__must__": [                  // D AND E
          {"field1": "value3"},        // D
          {"field2": "value4"}         // E
        ]
      }
    ]
  },
  "then": {
    "flexible_match": "true"
  }
}
```

**Applies when:**
- `field0` is "value0" OR
- (`field1` is "value1" AND `field2` is "value2") OR
- (`field1` is "value3" AND `field2` is "value4")

### Example 3: Deeply Nested

**Logic:** `A AND (B OR (C AND D))`

```json
{
  "when": {
    "__must__": [
      {"assay_type": "proteomics"},    // A
      {
        "__should__": [                 // B OR (C AND D)
          {"protocol": "standard"},     // B
          {
            "__must__": [               // C AND D
              {"protocol": "custom"},   // C
              {"validated": "yes"}      // D
            ]
          }
        ]
      }
    ]
  },
  "then": {
    "assay_category": "valid_proteomics"
  }
}
```

**Applies when:**
- `assay_type` is "proteomics" AND
- (`protocol` is "standard" OR (`protocol` is "custom" AND `validated` is "yes"))

## Combining __must__ and __should__

You can use both `__must__` and `__should__` at the top level. They are ANDed together.

```json
{
  "when": {
    "__must__": [
      {"dataset_type": "clinical"}
    ],
    "__should__": [
      {"institution": "harvard"},
      {"institution": "stanford"}
    ]
  },
  "then": {
    "elite_clinical_data": "true"
  }
}
```

**Applies when:**
- `dataset_type` is "clinical" AND
- (`institution` is "harvard" OR `institution` is "stanford")

## Practical Examples

### Example: Standardizing Assay Types

```json
[
  {
    "when": {
      "__should__": [
        {"assay_type": "RNA-seq"},
        {"assay_type": "RNASeq"},
        {"assay_type": "rna_sequencing"}
      ]
    },
    "then": {
      "assay_type": "RNA_sequencing"
    }
  }
]
```

### Example: Complex Protocol Validation

```json
[
  {
    "when": {
      "__must__": [
        {"tissue_type": "kidney"},
        {
          "__should__": [
            {
              "__must__": [
                {"preservation": "fresh"},
                {"processing_time": "< 2hr"}
              ]
            },
            {
              "__must__": [
                {"preservation": "frozen"},
                {"storage_temp": "-80C"}
              ]
            }
          ]
        }
      ]
    },
    "then": {
      "quality_tier": "premium",
      "suitable_for_sequencing": "true"
    }
  }
]
```

**Logic:** Kidney tissue that is **either** (fresh AND processed quickly) **OR** (frozen AND stored correctly).

### Example: Multi-Site Data Harmonization

```json
[
  {
    "when": {
      "__must__": [
        {
          "__should__": [
            {"data_source": "site_a"},
            {"data_source": "site_b"}
          ]
        },
        {"data_type": "metabolomics"},
        {"version": "legacy"}
      ]
    },
    "then": {
      "harmonization_required": "true",
      "target_schema": "metabolomics_v2"
    }
  }
]
```

## Edge Cases

### Empty Arrays

**Empty `__must__` array:**
```json
{"__must__": []}  // Always evaluates to TRUE (vacuous truth)
```

**Empty `__should__` array:**
```json
{"__should__": []}  // Always evaluates to FALSE
```

### Empty When Clause

```json
{
  "when": {},
  "then": {"always_applied": "true"}
}
```

An empty `when` clause causes the patch to **always** apply.

## Validation Rules

1. **`when` must be an object**
2. **`when` can only contain `__must__` and/or `__should__` keys**
3. **`__must__` and `__should__` must be arrays**
4. **Array items must be objects**
5. **Items can be either:**
   - Simple field-value objects: `{"field": "value"}`
   - Nested logic objects: `{"__must__": [...]}` or `{"__should__": [...]}`

## Tips and Best Practices

### 1. Start Simple

Begin with simple conditions and build complexity as needed:

```json
// Simple
{"when": {"__must__": [{"status": "active"}]}}

// More complex
{
  "when": {
    "__must__": [
      {"status": "active"},
      {"__should__": [{"tier": "gold"}, {"tier": "platinum"}]}
    ]
  }
}
```

### 2. Use Comments in Development

While JSON doesn't support comments, you can add them during development:

```jsonc
{
  "when": {
    "__must__": [
      {"assay_type": "proteomics"},  // Must be proteomics
      {
        "__should__": [              // Accept multiple protocols
          {"protocol": "TMT"},
          {"protocol": "iTRAQ"}
        ]
      }
    ]
  }
}
```

(Remove comments before using in production)

### 3. Test Incrementally

Test each level of nesting separately:

```json
// Test level 1
{"__must__": [{"field1": "value1"}]}

// Test level 2
{
  "__must__": [
    {"field1": "value1"},
    {"__should__": [{"field2": "value2"}]}
  ]
}

// Test full nesting
{
  "__must__": [
    {"field1": "value1"},
    {
      "__should__": [
        {"field2": "value2"},
        {"__must__": [{"field3": "value3"}]}
      ]
    }
  ]
}
```

### 4. Use Descriptive Then Values

Make it clear why a patch was applied:

```json
{
  "when": { /* ... */ },
  "then": {
    "patch_applied": "protocol_normalization",
    "patch_reason": "legacy_site_a_format",
    "normalized_protocol": "standard_v2"
  }
}
```

### 5. Order Patches Strategically

Patches are applied in order. Later patches can override earlier ones:

```json
[
  {
    "when": {"__must__": [{"source": "site_a"}]},
    "then": {"quality": "standard"}
  },
  {
    "when": {
      "__must__": [
        {"source": "site_a"},
        {"validated": "yes"}
      ]
    },
    "then": {"quality": "high"}  // Overrides previous
  }
]
```

## Error Messages

The validation provides detailed error messages:

- `'when' can only contain '__must__' and/or '__should__' keys, found 'must'`
- `'__must__' must be an array, got dict`
- `Patch 0 in file.json.__must__[1] must be an object, got str`
- `Patch 0 in file.json must have 'when' and 'then' keys`

## Complete Example

Here's a real-world example combining multiple concepts:

```json
[
  {
    "when": {
      "__must__": [
        {
          "__should__": [
            {"dataset_type": "rnaseq"},
            {"dataset_type": "RNA-seq"},
            {"dataset_type": "rna_sequencing"}
          ]
        },
        {
          "__should__": [
            {
              "__must__": [
                {"institution": "broad"},
                {"platform": "illumina"}
              ]
            },
            {
              "__must__": [
                {"institution": "ucsd"},
                {"platform": "pacbio"}
              ]
            }
          ]
        },
        {"qc_status": "passed"}
      ]
    },
    "then": {
      "standardized_assay_type": "bulk_rna_sequencing",
      "data_tier": "production",
      "harmonization_applied": "true",
      "harmonization_rules": "rnaseq_multi_site_v1"
    }
  }
]
```

**Logic:**
- Dataset type is some variant of RNA-seq AND
- ((Institution is Broad AND platform is Illumina) OR (Institution is UCSD AND platform is PacBio)) AND
- QC status is passed

## Summary

- **`__must__`** = AND operator (all must be true)
- **`__should__`** = OR operator (any must be true)
- **Nest freely** to create complex logic
- **Simple objects** like `{"field": "value"}` are leaf conditions
- **Arrays can contain** both simple conditions and nested logic
- **Patches apply in order** - later patches can override earlier ones
