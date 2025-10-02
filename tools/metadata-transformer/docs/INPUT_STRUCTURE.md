# Input Structure

This document describes the structure of the input JSON files used by the metadata transformer.

## Overview

Input files are JSON objects containing dataset information and associated metadata. Each file represents a single dataset with a unique identifier and contains both top-level fields and a flexible metadata object.

## Top-Level Structure

```json
{
  "uuid": "string",
  "dataset_type": "string",
  "metadata": { ... }
}
```

## Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `uuid` | string | **Yes** | Unique identifier for the dataset | `"421007293469db7b528ce6478c00348d"` |
| `dataset_type` | string | **Yes** | The type of dataset | `"RNAseq"` |
| `metadata` | object | **Yes** | Contains all dataset-specific metadata fields. Can contain any fields relevant to the dataset. The structure and fields within this object are flexible and vary based on the dataset type and source. | `{ ... }` |
| `hubmap_id` | string | No | HuBMAP identifier for the dataset | `"HBM575.XFCT.276"` |
| `status` | string | No | Publication or processing status | `"Published"`, `"QA"` |
| `group_name` | string | No | Name of the organization or group that produced the dataset | `"University of California San Diego TMC"` |

## Complete Example

```json
{
  "uuid": "421007293469db7b528ce6478c00348d",
  "hubmap_id": "HBM575.XFCT.276",
  "status": "Published",
  "group_name": "University of California San Diego TMC",
  "dataset_type": "RNAseq",
  "metadata": {
    "acquisition_instrument_model": "NovaSeq",
    "acquisition_instrument_vendor": "Illumina",
    "analyte_class": "RNA",
    "assay_category": "sequence",
    "assay_type": "SNARE2-RNAseq",
    "donor_id": "UCSD0006",
    "tissue_id": "UCSD0006-RK-1-1-1"
  }
}
```

## Notes

- The `metadata` object is intentionally flexible to accommodate different dataset types and evolving metadata requirements
- Field names and values in the `metadata` object may vary significantly between datasets
- All top-level fields except `uuid`, `dataset_type`, and `metadata` are optional
