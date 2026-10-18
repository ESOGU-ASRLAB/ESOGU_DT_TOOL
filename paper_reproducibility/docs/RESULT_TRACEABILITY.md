# Result Traceability

The traceability chain is:

1. Fixed source inputs and suite JSON under `test_inputs/` and `experiments/full_suite/suites/`.
2. Per-run configuration, raw decisions, retained/removed cases, and metrics under `results/full_suite/`.
3. Analysis code under `analysis/`.
4. Aggregates under `results/variability/`, `results/scenario_metrics/`, `results/baseline/`, and `results/final_tables/`.
5. Manuscript-level claims in `results/traceability/numerical_traceability.csv` and `docs/PAPER_RESULT_MAP.md`.

`results/traceability/db_file_crosscheck.csv` records 60 unique database IDs and corresponding run paths. `environment/suite_manifest.csv` records the fixed suite provenance and content hashes. The release-level integrity manifest proves byte identity between the validated source evidence and this package.

The primary 60-run results must not be confused with the earlier eight-case pilot or historical Serial evidence. Historical material is retained for provenance, but the controlled full-suite corpus is the primary revision-time evidence.

