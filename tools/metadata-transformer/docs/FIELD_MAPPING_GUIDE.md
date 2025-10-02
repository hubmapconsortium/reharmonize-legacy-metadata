# Field Mapping Table Guide

## Purpose
Field mapping tables document how fields from multiple legacy schemas map to a unified target schema. These tables guide data transformation during schema migration.

## Table Structure

### Basic Format
- **First row**: Schema identifiers
- **First column**: Target schema field names
- **Remaining columns**: Legacy schema field names
- **Empty cells**: No mapping exists for that schema version

### Example Structure

| cedar-rnaseq-v5.0.0 | bulkrnaseq-v0 | bulkrnaseq-v1 | scrnaseq-v0 | scrnaseq-v1 |
|---------------------|---------------|---------------|-------------|-------------|
| target_field_1      | legacy_field_1 | legacy_field_1 | legacy_field_1 | legacy_field_1 |
| target_field_2      | old_field_name | old_field_name | | |
| target_field_3      | | | new_field | new_field |

## Creating Your Mapping Table

### Step 1: Set Up the Header Row
The first row contains schema identifiers:
- Column 1: Your target schema name and version
- Remaining columns: Legacy schema names and versions in logical order

| target-schema-v2.0 | legacy-v0 | legacy-v1 | legacy-v1.5 |
|--------------------|-----------|-----------|-------------|

### Step 2: Map Fields with Equivalents
For each field in your target schema, add a row showing the corresponding field name in each legacy schema.

#### Example: Field Present in All Versions

| target-schema-v2.0 | legacy-v0 | legacy-v1 | legacy-v1.5 |
|--------------------|-----------|-----------|-------------|
| sample_id          | sample_id | sample_id | sample_id   |
| temperature        | temperature | temperature | temperature |

#### Example: Field Renamed Across Versions

| target-schema-v2.0 | legacy-v0 | legacy-v1 | legacy-v1.5 |
|--------------------|-----------|-----------|-------------|
| participant_id     | subject_id | subject_id | participant_id |
| protocol_url       | protocol_link | protocol_link | protocol_url |

#### Example: Field Added in Later Versions

| target-schema-v2.0 | legacy-v0 | legacy-v1 | legacy-v1.5 |
|--------------------|-----------|-----------|-------------|
| quality_score      |           |           | quality_score |
| batch_id           |           | batch_id  | batch_id    |

#### Example: Field Only in Specific Schema Types

| target-schema-v2.0 | bulk-v0 | bulk-v1 | single-cell-v0 | single-cell-v1 |
|--------------------|---------|---------|----------------|----------------|
| input_amount       | input_ng | input_ng |               |                |
| cell_count         |         |         | num_cells      | num_cells      |

### Step 3: Handle Value-Unit Pairs
When a target schema splits combined fields into separate value and unit fields:

| target-schema-v2.0 | legacy-v0 | legacy-v1 |
|--------------------|-----------|-----------|
| duration_value     | duration  | duration  |
| duration_unit      | duration_unit | duration_unit |
| weight_value       | weight_kg |           |
| weight_unit        |           |           |

### Step 4: List Unmapped Legacy Fields
After all target schema fields, list legacy fields that don't map to the target schema. Leave the first column empty:

| target-schema-v2.0 | legacy-v0 | legacy-v1 | legacy-v1.5 |
|--------------------|-----------|-----------|-------------|
| *(mapped fields above)* | | | |
|                    | deprecated_field_1 | deprecated_field_1 | |
|                    | internal_code |  |  |
|                    |           | temp_field |  |

## Complete Example

Here's a complete mapping table for a hypothetical assay migration:

| target-assay-v3.0 | assay-v1 | assay-v2 | assay-v3 |
|-------------------|----------|----------|-------------------|
| sample_identifier | sample_id | sample_id | sample_identifier |
| tissue_type | tissue | tissue | tissue_type |
| preparation_date | prep_date | prep_date | preparation_date |
| protocol_doi | | protocol_link | protocol_doi |
| instrument_vendor | vendor | instrument_vendor | instrument_vendor |
| instrument_model | model | instrument_model | instrument_model |
| input_amount_value | input_ng | input_amount | input_amount_value |
| input_amount_unit | | input_unit | input_amount_unit |
| library_size | | | library_size |
| read_length | read_len | read_length | read_length |
| | version | version | |
| | operator_initials | | |