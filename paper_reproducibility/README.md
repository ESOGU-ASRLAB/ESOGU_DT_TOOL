# STLC Manager

This repository package supports the paper **“STLC Manager: Benchmarking LLM-Driven Model-to-Test Transformation and Test Case Optimization.”** It contains the application source, controlled experiment protocols, Human Oracle annotations, raw run evidence, analysis programs, machine-readable results, and numerical traceability records used in the final major revision.

The canonical publication evidence is maintained in [ESOGU-SRLAB/ESOGU_DT_TOOL](https://github.com/ESOGU-SRLAB/ESOGU_DT_TOOL/tree/main/paper_reproducibility). [cembglm/stlc-man](https://github.com/cembglm/stlc-man/tree/main/paper_reproducibility) is the development and reproducibility mirror.

## Scope

The study evaluates **pre-execution semantic test-case redundancy**. The reported Test Reduction Rate, Similarity/Comparison Performance, decision stability, Human Oracle agreement, and TF-IDF comparison do not establish code coverage, mutation adequacy, or fault-detection effectiveness.

The controlled revision experiment contains 60 successful local runs: 30 partitioned Local Bulk runs and 30 Controlled Local Parallel runs. It crosses two fixed 64-case suites, three local models, two optimization modes, and five repeats. Serial results are historical evidence; Serial was not rerun in the controlled experiment.

## Repository structure

- `src/`: STLC Manager backend, frontend, Docker integration, and relevant tests and configuration templates.
- `experiments/full_suite/`: fixed-suite preparation, execution harness, protocol, and suite manifests.
- `analysis/`: Human Oracle, variability, scenario-metric, TF-IDF, table-validation, and traceability programs.
- `test_inputs/`: the two redistributable source artefacts from which the fixed suites were constructed.
- `results/full_suite/`: all 60 successful controlled run packages, separated into `bulk/` and `parallel/`.
- `results/human_oracle/`: aligned ratings, agreement estimates, consensus strata, and optimizer comparisons.
- `results/variability/`, `results/scenario_metrics/`, `results/baseline/`, and `results/final_tables/`: processed machine-readable outputs.
- `human_oracle/`: the PySide6 rating tool and Human 1, Human 2, and Human 3 annotation exports.
- `environment/`: machine, model, suite, input, and model-hash manifests. Model binaries are intentionally absent.
- `docs/`: experiment protocol, reproduction commands, field definitions, and paper-to-evidence maps.

## Reproduce the Human Oracle analysis

From the package root:

```bash
python analysis/human_oracle/build_human_oracle_analysis.py
python analysis/human_oracle/build_human_oracle_tables.py
```

The scripts use the evaluator exports under `human_oracle/` and produce the aligned and agreement outputs documented in `results/human_oracle/`. See `docs/REPRODUCIBILITY.md` for environment and path details.

## Reproduce the TF-IDF baseline

```bash
python analysis/tfidf_baseline/analyze_revision_public_archive.py
```

The validated threshold-0.50 result is recorded in `results/baseline/tfidf_baseline_metrics.csv`.

## Reproduce scenario metrics

```bash
python analysis/scenario_metrics/build_revision_evidence.py
python analysis/scenario_metrics/expand_historical_validation.py
```

The controlled raw-versus-artifact-scoped comparison is in `results/scenario_metrics/raw_vs_scoped_scp.csv`.

## Reproduce variability tables and figures

```bash
python analysis/variability/analyze_full_suite_results.py
python analysis/variability/generate_full_suite_figures.py
```

These commands consume `results/full_suite/` and regenerate the processed outputs represented in `results/variability/`, `results/final_tables/`, and `figures/reproducibility_figures/`.

## Local models

- Llama 3.2 3B Q4_K_S
- GPT-OSS 20B MXFP4
- Qwen3-Coder 30B A3B Q3_K_L

The exact model filenames, quantizations, sizes, and SHA-256 hashes are recorded under `environment/`. Model binaries are not distributed. The controlled runs used the recorded NVIDIA RTX 4000 Ada environment described in `environment/machine_environment.md`.

## Results and traceability

Start with `docs/PAPER_RESULT_MAP.md`. It links every headline claim to an analysis program, processed output, and raw evidence directory. `results/traceability/numerical_traceability.csv` and `results/traceability/db_file_crosscheck.csv` provide machine-readable audits.

## Installation notes

Backend dependencies are listed in `requirements.txt`; frontend dependencies are declared in `src/frontend/package.json`. Copy `src/.env.example` to a local `.env` and provide your own credentials only when running integrations that require them. Never commit the resulting `.env`.

## Citation and licence

Citation metadata is provided in `CITATION.cff`. No publication DOI is asserted because one has not yet been assigned. The software and packaged materials retain the existing Apache License 2.0 in `LICENSE`.

