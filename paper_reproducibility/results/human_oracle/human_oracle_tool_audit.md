# Human Oracle PySide6 tool audit

- Archived source: `test_results/human_oracle_pyside6.py`
- SHA-256: `861d9c602e6ef52b89520d8917ddc48b12548064bfff275d01dac121a76dab96`
- Input: `calculation_db.coverage_db.json`, accepting either a JSON array or JSON Lines.
- Item extraction: unique and both sides of Similar pairs are normalized; duplicate `case_key` values are removed; records are sorted before `row_ref` values `R0001...` are assigned.
- `case_key`: MD5 over session, process, optimization type, model, scenario ID, test-case ID, title, description, and objective.
- Persistence: MongoDB `calculation_db.human_oracle_decisions`; updates use `row_ref` as the unique upsert key. The process-level JSON function copies selected records to the system clipboard and does not directly save evaluator-specific JSON files.
- Decisions: Unique, Similar, and Unclear.
- Additional fields: Similar To and 1-5 confidence are available in the interface. Save time is assigned during each bulk save.
- Evaluator identifier: the archived source hard-codes `reviewer_id=human_expert_1`; evaluator separation is therefore established by the separate public archived-output directories, not by a configurable UI identity. The code does not establish the external mechanism by which those public JSON files were written, so no unverified export mechanism is claimed.

## Blinding and anchoring

The interface is not blinded. Its table and detail metadata visibly expose the model (`used_model`), optimization type, and original LLM label. Consequently, evaluator judgements could be anchored by model identity, mode, or the original classifier output. The manuscript must report this as a human-reference validity limitation and must not claim evaluator blinding.

## Identity limitation

Although `case_key` contains strong content and provenance fields, the database save/update key is `row_ref`. The public exports align successfully because the three archives share the same row references and identical content signatures; nevertheless, row references could change if the source dataset or sort order changed. The reproduction therefore validates content signatures in addition to `row_ref`.
