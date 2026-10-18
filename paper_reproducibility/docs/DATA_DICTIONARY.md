# Data Dictionary

## Controlled run records

| Field | Meaning |
|---|---|
| `run_id` | Stable identifier combining suite, model, mode, and repeat. |
| `suite_id` | `FULLSRC` for the source-code suite or `FULLREQ` for the requirements suite. |
| `model_key` | Short key: `llama32`, `gptoss20`, or `qwen30`. |
| `mode` | `Local Bulk` or `Controlled Local Parallel`. |
| `repeat` | Repeat number 1–5 within a design cell. |
| `status` | Completion state; the primary corpus contains successful `COMPLETE` runs. |
| `total_input_cases` | Number of test cases entering optimization; 64 for both fixed suites. |
| `comparison_count` | Model comparisons performed; 32 for Bulk and 2,016 for Parallel. |
| `unique_count` / `similar_count` | Counts produced by the validated classification and post-processing path. |
| `trr` | Test Reduction Rate, the removed-case fraction. |
| `legacy_raw_id_scp` | Scenario coverage proxy calculated from raw scenario identifiers. |
| `artifact_scoped_scp` | Scenario coverage proxy after scoping scenario identity by source artefact. |
| `configuration_hash` | SHA-256 identifier of the effective run configuration. |
| `suite_hash` | SHA-256 identifier of the fixed suite content. |
| `database_record_id` | MongoDB record identifier used by the DB/file cross-check. |

## Human Oracle records

| Field | Meaning |
|---|---|
| `source_model` | Model whose optimizer decision was evaluated. |
| `human1`, `human2`, `human3` | Evaluator labels: Unique, Similar, or Unclear. |
| `majority_label` | Two-of-three or three-of-three consensus label. |
| `consensus_strength` | `3/3 unanimous`, `2/3 majority`, or unresolved. |
| `fleiss_kappa` | Multi-rater chance-corrected agreement statistic. |
| `cohen_h1_h2`, `cohen_h1_h3`, `cohen_h2_h3` | Pairwise Cohen kappa values. |
| `gwet_ac1` | Prevalence-robust chance-corrected agreement statistic. |

## Baseline and stability records

| Field | Meaning |
|---|---|
| `threshold` | TF-IDF cosine-similarity decision threshold. |
| `tp_similar_removed` | Consensus-Similar items removed by the baseline. |
| `fp_unique_removed` | Consensus-Unique items incorrectly removed. |
| `f1_similar` | F1 score treating Similar as the positive class. |
| `balanced_accuracy` | Mean of sensitivity and specificity. |
| `modal_agreement` | Fraction of repeats matching the modal pair decision. |
| `difference` | Artifact-scoped SCP minus legacy raw-ID SCP. |

JSON run artefacts use the same concepts with nested configuration and decision structures. CSV files are UTF-8 and use a header row.

