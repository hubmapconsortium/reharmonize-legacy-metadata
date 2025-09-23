# Task Instructions: Metadata Transformation Evaluation

**Goal:**  
Evaluate the modified metadata from legacy records to determine whether they have been correctly and accurately transformed according to the current schema.

All modified metadata are in the `output` folder (see the **[README.md](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/output/README.md)** for the metadata output structure). Focus on the following four areas:

1. Validate **field mappings**  
2. Validate **value mappings**  
3. Resolve **ambiguous mappings**  
4. Confirm that **excluded data** is legitimately discarded  

---

## 1. Validate Field Mappings
- **How to check:**
  - Use the mapping table overview in [mappings/field-mappings](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/mappings/field-mapping).
  - Cross-reference with the tables in the [glossary](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/glossary) folder to verify if the chosen field mappings are correct and justified.
- **Making changes:**  
  - If corrections are needed, update the mapping table in [mappings/field-mappings](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/mappings/field-mapping).  
  - Include the rationale for the change in the Git commit message.

---

## 2. Validate Value Mappings
- **How to check:**
  - Use the mapping files in [value-mappings](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/mappings/value-mapping).
  - If the mapped value is **not null**: Verify that the translation is accurate and makes sense.  
  - If the mapped value is **null**: Assess whether the legacy value should be added to the new schema or whether it has no valid equivalent, taking the field name into account.
- **Making changes:**  
  - Update the mapping object in [value-mappings](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/mappings/value-mapping) as needed.  
  - Document the reasoning in the Git commit message.

---

## 3. Resolve Ambiguous Mappings
- **How to check:**
  - Identify mappings where multiple options are possible.  
  - Suggest the most appropriate mapping, or determine if the legacy value should be included in the new schema.  
- **Making changes:**  
  - Record your resolution as a new patch in the [patches](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/tree/main/patches) folder.  
  - Refer to **[README.md](https://github.com/hubmapconsortium/reharmonize-legacy-metadata/blob/main/patches/README.md)** for patch object structure.

---

## 4. Confirm Excluded Data
- **How to check:**  
  - Verify that excluded data truly has no place in the new schema and is safe to discard.  
- **Making changes:**  
  - No changes are required—this is a verification step only.

---

## ✅ Deliverables
- Updated mapping files (`field-mappings`, `value-mappings`) as needed  
- New patches in the `patches` folder when resolving ambiguities  
- Clear Git commit messages explaining the rationale for every change
