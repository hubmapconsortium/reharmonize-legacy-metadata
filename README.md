# HubMAP Legacy Metadata Standardization

## Overview

This project standardizes legacy metadata from 12 different assay types into schema-compliant formats for the Human BioMolecular Atlas Program (HubMAP). The transformation ensures data quality, consistency, and compliance with current metadata standards.

**Per October 31, 2025**: 2,192 legacy metadata files processed across 12 assay types

---

## Deliverable 1: Standardized Metadata by Dataset Type

The `metadata/` folder contains processed metadata organized by assay type. Each subfolder represents a distinct experimental methodology:

### Dataset Types

| Dataset Type | # of Files | Description | Processed | Reviewed | Todo |
|-------------|------------|-------------|:---------:|:--------:|:----:|
| **[rnaseq](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/rnaseq)** | 639 | RNA sequencing metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/rnaseq/todo) |
| **[atacseq](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/atacseq)** | 567 | ATAC sequencing metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/atacseq/todo) |
| **[lcms](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lcms)** | 267 | Liquid chromatography-mass spectrometry metadata | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lcms/todo) |
| **[mibi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/mibi)** | 211 | Multiplexed ion beam imaging metadata | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/mibi/todo) |
| **[af](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/af)** | 136 | Auto-fluorescence imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/af/todo) |
| **[codex](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/codex)** | 133 | CODEX imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/codex/todo) |
| **[maldi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/maldi)** | 93 | MALDI imaging mass spectrometry metadata | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/maldi/todo) |
| **[histology](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/histology)** | 77 | Histology imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/histology/todo) |
| **[celldive](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/celldive)** | 32 | Cell DIVE imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/celldive/todo) |
| **[desi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/desi)** | 15 | DESI imaging mass spectrometry metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/desi/todo) |
| **[imc-2d](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/imc-2d)** | 13 | Imaging mass cytometry 2D metadata | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/imc-2d/todo) |
| **[lightsheet](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lightsheet)** | 9 | Light sheet microscopy metadata | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lightsheet/todo) |

### Folder Structure

Each dataset type folder contains:

```
metadata/{dataset-type}/
├── input/                          # Original legacy metadata files
├── output/                         # Transformed, schema-compliant files
├── todo/                           # Excel reports for curator review (grouped by institution)
│   ├── {Institution Name}.xlsx    # Institution-specific review spreadsheet
│   └── summary-report.json        # Aggregated statistics
├── {dataset-type}-field-mappings.csv    # Field name mapping rules
├── {dataset-type}-patches.json    # Conditional transformation rules
└── {dataset-type}-nonstandard-values.json  # Quality assurance analysis results
```

#### Input Folder (`input/`)
Contains original legacy metadata JSON files with inconsistent field names and value formats from various data providers.

#### Output Folder (`output/`)
Contains standardized metadata JSON files with:
- Schema-compliant field names and values
- Full transformation provenance (processing logs)
- JSON patches applied during transformation
- Both original and modified metadata for comparison

Each output file includes:
```json
{
  "uuid": "...",
  "hubmap_id": "...",
  "metadata": { /* original legacy metadata */ },
  "modified_metadata": { /* standardized metadata */ },
  "json_patch": [ /* transformation operations applied */ ],
  "processing_log": {
    /* complete audit trail of:
       - field name changes
       - value standardizations
       - excluded data
       - transformation decisions */
  }
}
```

#### Todo Folder (`todo/`)
Contains Excel spreadsheets grouped by institution for data provider review. Each spreadsheet identifies:
- **Non-standard values:** Legacy values with no current schema equivalent
- **Missing required data:** Required fields that are null or empty
- **Validation issues:** Values that don't meet schema constraints (e.g., regex patterns)

Data providers use these spreadsheets to:
1. Review flagged values and determine appropriate actions
2. Update value mappings to include new standard equivalents
3. Request missing data from data providers
4. Propose schema updates for legitimate legacy values

---

## Deliverable 2: Metadata Processing System

### Overview
An automated, rule-based transformation pipeline with quality assurance analysis.

### Components

#### Core Transformation Tools (`tools/`)

**metadata-transformer** (v1.2.0)
- Command-line tool for 4-phase metadata transformation
- Phases: Conditional patching → Field mapping → Value standardization → Schema compliance
- Comprehensive logging for full traceability

**json-rules-engine** (v1.0.0)
- Conditional transformation engine
- Supports complex if/then logic for context-dependent transformations

#### Analysis Scripts (`scripts/`)

**generate-field-mapping.py**
- Converts human-readable CSV field mappings to machine-readable JSON format

**generate-target-schema.py**
- Fetches and converts schemas from HubMAP repository
- Ensures alignment with current metadata standards

**find-nonstandard-values.py**
- Quality assurance analysis after transformation
- Identifies values requiring curator review
- Generates institution-grouped Excel reports

### Transformation Pipeline

```
Legacy Metadata → [4-Phase Transformation] → Standardized Metadata → [QA Analysis] → Data Provider Review
```

**Phase 0:** Apply conditional patches (complex transformations)
**Phase 1:** Rename fields (legacy → standard names)
**Phase 2:** Standardize values (legacy → standard values)
**Phase 3:** Apply schema (ensure all required fields present)
**Phase 4:** Generate logs (complete audit trail)

### Automation

GitHub Actions workflows automate the complete transformation and analysis pipeline for each dataset type:
- Triggered manually via workflow dispatch
- Steps: Generate mappings → Transform → Analyze → Commit results
- Ensures reproducible, version-controlled transformations
