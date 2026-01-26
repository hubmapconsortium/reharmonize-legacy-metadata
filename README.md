# HubMAP Legacy Metadata Standardization

## Overview

This project standardizes legacy metadata from 17 different assay types into schema-compliant formats for the Human BioMolecular Atlas Program (HubMAP). The transformation ensures data quality, consistency, and compliance with current metadata standards.

**Per October 31, 2025**: 2,192 legacy metadata files processed across 12 assay types

**Per December 4, 2025**: 2,568 legacy metadata files processed across 17 assay types, and 2,192 are reviewed

---

## Deliverable 1: Standardized Metadata by Dataset Type

The `metadata/` folder contains processed metadata organized by assay type. Each subfolder represents a distinct experimental methodology:

### Dataset Types

| Dataset Type | # of Files | Description | Processed | Reviewed | Todo | Summary |
|-------------|------------|-------------|:---------:|:--------:|:----:|:-------:|
| **[rnaseq](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/rnaseq)** | 639 | RNA sequencing metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/rnaseq/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/rnaseq/transformation-summary.html) |
| **[atacseq](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/atacseq)** | 567 | ATAC sequencing metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/atacseq/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/atacseq/transformation-summary.html) |
| **[lcms](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lcms)** | 267 | Liquid chromatography-mass spectrometry metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lcms/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/lcms/transformation-summary.html) |
| **[mibi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/mibi)** | 211 | Multiplexed ion beam imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/mibi/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/mibi/transformation-summary.html) |
| **[af](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/af)** | 136 | Auto-fluorescence imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/af/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/af/transformation-summary.html) |
| **[codex](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/codex)** | 133 | CODEX imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/codex/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/codex/transformation-summary.html) |
| **[maldi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/maldi)** | 93 | MALDI imaging mass spectrometry metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/maldi/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/maldi/transformation-summary.html) |
| **[histology](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/histology)** | 77 | Histology imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/histology/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/histology/transformation-summary.html) |
| **[celldive](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/celldive)** | 32 | Cell DIVE imaging metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/celldive/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/celldive/transformation-summary.html) |
| **[desi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/desi)** | 15 | DESI imaging mass spectrometry metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/desi/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/desi/transformation-summary.html) |
| **[imc-2d](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/imc-2d)** | 13 | Imaging mass cytometry 2D metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/imc-2d/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/imc-2d/transformation-summary.html) |
| **[lightsheet](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lightsheet)** | 9 | Light sheet microscopy metadata | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/lightsheet/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/lightsheet/transformation-summary.html) |
| **[10x-multiome](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-10x-multiome)** | 102 | 10X Multiome metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-10x-multiome/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-10x-multiome/transformation-summary.html) |
| **[histology](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-histology)** | 88 | Histology imaging metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-histology/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-histology/transformation-summary.html) |
| **[visium-no-probes](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-visium-no-probes)** | 83 | Visium (no probes) metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-visium-no-probes/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-visium-no-probes/transformation-summary.html) |
| **[rnaseq](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-rnaseq)** | 50 | RNA sequencing metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-rnaseq/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-rnaseq/transformation-summary.html) |
| **[af](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-af)** | 28 | Auto-fluorescence imaging metadata (from CEDAR instances) | ✅ | ✅ | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-af/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-af/transformation-summary.html) |
| **[music](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-music)** | 14 | MuSIC metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-music/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-music/transformation-summary.html) |
| **[lightsheet](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-lightsheet)** | 8 | Light sheet microscopy metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-lightsheet/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-lightsheet/transformation-summary.html) |
| **[maldi](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-maldi)** | 3 | MALDI imaging mass spectrometry metadata (from CEDAR instances) | ✅ | | [link](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata/cedar-maldi/todo) | [link](https://github-html-preview.dohyeon5626.com/?https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/metadata/cedar-maldi/transformation-summary.html) |

**Acknowledgement**: Metadata review conducted by Jean G. Rosario ([jrosar7](https://github.com/jrosar7)) at University of Pennsylvania.

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
├── {dataset-type}-nonstandard-values.json  # Quality assurance analysis results
└── transformation-summary.html    # HTML report summarizing all transformations
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

#### Transformation Summary (`transformation-summary.html`)
An HTML report providing a comprehensive overview of all transformations applied to the dataset type. The report includes:
- **Field mappings table:** Shows the mapping from legacy field names to target schema field names
- **Value mappings table:** Aggregated and deduplicated value standardizations extracted from output files
- **Patches list:** Human-readable narration of conditional transformation rules applied

This report serves as documentation for reviewers to understand exactly what transformations were performed without needing to inspect individual output files.

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

**generate-transformation-summary.py**
- Generates HTML report summarizing all transformations for a dataset type
- Aggregates field mappings, value mappings, and conditional patches
- Produces human-readable narration of patch rules using templates

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
