# Reproducibility Guide

## Prerequisites

- Python 3.12 or later for the validated analysis environment.
- Packages used by the selected analysis scripts, including pandas, NumPy, SciPy, scikit-learn, matplotlib, and PySide6 for the annotation GUI.
- Backend dependencies from `requirements.txt` only when running the STLC Manager application or the experiment harness.
- Node.js and npm for the frontend under `src/frontend/`.
- Local model servers and model files only when intentionally repeating generation/optimization; model binaries are not included.

Create an isolated environment and install the analysis dependencies appropriate to the scripts you intend to run. Do not reuse or commit a secret-bearing `.env`.

## Analysis-only workflow

The validated manuscript numbers can be checked without rerunning local language models:

```bash
python analysis/human_oracle/build_human_oracle_analysis.py
python analysis/human_oracle/build_human_oracle_tables.py
python analysis/tfidf_baseline/analyze_revision_public_archive.py
python analysis/variability/analyze_full_suite_results.py
python analysis/variability/generate_full_suite_figures.py
python analysis/traceability/crosscheck_experiment.py
```

Some retained scripts were originally executed from the final-revision working tree and encode paths relative to that layout. When running them from this publication package, pass package-local input/output paths where the script exposes arguments; otherwise update only the path constants in a disposable working copy. The validated outputs and source hashes are already preserved here.

## Controlled experiment workflow

Use `experiments/full_suite/prepare_full_suite_study.py` to validate fixed-suite inputs and `experiments/full_suite/run_full_suite_experiment.py` for an explicitly configured rerun. Consult `experiments/full_suite/experiment_design.md`, `environment/model_manifest.csv`, and `environment/suite_manifest.csv` first. A rerun requires the exact local models and recorded inference settings and is not needed to verify the packaged results.

## Human Oracle workflow

Launch the GUI with:

```bash
python human_oracle/human_oracle_pyside6.py
```

The original three evaluator exports are under `human_oracle/Human 1/`, `Human 2/`, and `Human 3/`. The analysis-ready alignment is `results/human_oracle/aligned_evaluator_decisions.csv`.

## Integrity checks

The release-level `result_integrity_check.csv` records source and packaged SHA-256 hashes for every copied evidence file. `results/traceability/db_file_crosscheck.csv` connects the 60 filesystem run packages to their database record identifiers. Model hashes are in `environment/model_hashes/`.

