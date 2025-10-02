# Task Instructions: Metadata Transformation Evaluation

**Goal:**
Evaluate the modified metadata from legacy records to determine whether they have been correctly and accurately transformed according to the current schema.

The deliverables are organized in the [metadata](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/metadata) folder by dataset type (e.g., `rnaseq`, `atacseq`). Each dataset directory contains:
- `input/` - Original legacy metadata
- `output/` - Transformed metadata files
- `field-mapping.csv` - Field mapping definitions
- `patches.json` - Metadata transformation patches

Value mappings are shared across dataset types and located in [shared/value-mappings](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/shared/value-mappings).

For detailed guidance on creating or updating field mappings, value mappings, metadata patches, and understanding the output file structure, see the **[project wiki](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/wiki)**.

Focus on the following four areas:

1. Validate **field mappings**
2. Validate **value mappings**
3. Resolve **ambiguous mappings**
4. Confirm that **excluded data** is legitimately discarded

---

## 1. Validate Field Mappings
- **How to check:**
  - Review the `field-mapping.csv` file in each dataset directory under `metadata/`.
  - Verify that field mappings are correct and justified.
- **Making changes:**
  - Update the `field-mapping.csv` file in the appropriate dataset directory.
  - Include the rationale for the change in the Git commit message.

---

## 2. Validate Value Mappings
- **How to check:**
  - Review the value mappings in the `shared/value-mappings/` directory.
  - If the mapped value is **not null**: Verify that the translation is accurate and makes sense.
  - If the mapped value is **null**: Assess whether the legacy value should be added to the new schema or whether it has no valid equivalent, taking the field name into account.
- **Making changes:**
  - Update the value mapping files in `shared/value-mappings/`.
  - Document the reasoning in the Git commit message.

---

## 3. Resolve Ambiguous Mappings
- **How to check:**
  - Identify mappings where multiple options are possible in the `output` files.
  - Suggest the most appropriate mapping, or determine if the legacy value should be included in the new schema.
- **Making changes:**
  - Record your resolution in the `patches.json` file in the appropriate dataset directory.
  - Refer to the **[project wiki](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/wiki)** for patch object structure.

---

## 4. Confirm Excluded Data
- **How to check:**
  - Verify that excluded data truly has no place in the new schema and is safe to discard.
- **Making changes:**
  - No changes are required—this is a verification step only.

---

## ✅ Deliverables
- Updated `field-mapping.csv` files in dataset directories as needed
- Updated `value-mapping.csv` files in `shared/value-mappings` directory as needed
- Updated `patches.json` files when resolving ambiguities
- Clear Git commit messages explaining the rationale for every change
