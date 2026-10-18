# Paper Result Map

| Manuscript result | Processed evidence | Analysis program | Raw evidence |
|---|---|---|---|
| 60 successful new runs: 30 Bulk and 30 Parallel; 12 cells × 5 repeats | `results/traceability/db_file_crosscheck.csv`, `results/final_tables/table_A_full_suite_design.csv` | `analysis/traceability/crosscheck_experiment.py` | `results/full_suite/bulk/`, `results/full_suite/parallel/` |
| Two fixed 64-case suites with eight scenarios each | `environment/suite_manifest.csv` | `experiments/full_suite/prepare_full_suite_study.py` | `experiments/full_suite/suites/FULLSRC.json`, `experiments/full_suite/suites/FULLREQ.json` |
| Bulk and Parallel TRR variability and modal agreement ranges | `results/variability/variability_statistics.csv`, `results/variability/decision_stability_summary.csv` | `analysis/variability/analyze_full_suite_results.py` | `results/full_suite/` |
| Human Oracle: 1,074 aligned items and 3,222 ratings | `results/human_oracle/aligned_evaluator_decisions.csv`, `results/human_oracle/agreement_statistics.csv` | `analysis/human_oracle/build_human_oracle_analysis.py` | `human_oracle/Human 1/`, `Human 2/`, `Human 3/` |
| 473 unanimous and 601 majority-only items | `results/human_oracle/consensus_stratification.csv` | `analysis/human_oracle/build_human_oracle_analysis.py` | `results/human_oracle/aligned_evaluator_decisions.csv` |
| Overall Fleiss κ = 0.186386 | `results/human_oracle/agreement_statistics.csv` | `analysis/human_oracle/build_human_oracle_analysis.py` | `results/human_oracle/aligned_evaluator_decisions.csv` |
| TF-IDF at 0.50: F1 = 0.493197, balanced accuracy = 0.643417, 109 false removals | `results/baseline/tfidf_baseline_metrics.csv` | `analysis/tfidf_baseline/analyze_revision_public_archive.py` | `results/human_oracle/aligned_evaluator_decisions.csv` |
| Artifact-scoped SCP differs from raw-ID SCP in 9/30 paired model-mode-repeat observations | `results/scenario_metrics/raw_vs_scoped_scp.csv` | `analysis/scenario_metrics/build_revision_evidence.py` | `results/full_suite/` |
| Table 4 extrema 7,090 and 3,015; exact spread 57.4753% (rounded table value 57%) | `results/final_tables/regenerated_table4.csv`, `results/final_tables/table4_validation_report.md` | `analysis/table_validation/regenerate_readable_figures.py` | `results/historical/` |
| Full-suite TRR figure | `figures/reproducibility_figures/full_suite_trr_variability.pdf` | `analysis/variability/generate_full_suite_figures.py` | `results/variability/aggregated_results.csv` |
| Full-suite decision-stability figure | `figures/reproducibility_figures/full_suite_decision_stability.pdf` | `analysis/variability/generate_full_suite_figures.py` | `results/variability/decision_stability.csv` |

The machine-readable statement-by-statement audit is `results/traceability/numerical_traceability.csv`.

