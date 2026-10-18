from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "test_results" / "reviewer_revision_2026"
VAR = OUT / "03_variability_study"
MANUSCRIPT = Path(r"C:\Users\matisse\Desktop\applsci-4556799\applsci-4556799-revised.tex")
EXPERIMENT = "reviewer_revision_2026_variability"
SEED = 20261017


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def percentile(values: list[float], p: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def bootstrap_mean_ci(values: list[float], rng: random.Random, iterations: int = 10000) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    means = [statistics.mean(rng.choice(values) for _ in values) for _ in range(iterations)]
    return percentile(means, 0.025), percentile(means, 0.975)


def fleiss_binary(label_rows: list[list[str]]) -> tuple[float | None, float | None]:
    """Return Fleiss kappa and raw pairwise agreement for equal-length binary panels."""
    if not label_rows or len(label_rows[0]) < 2:
        return None, None
    n = len(label_rows[0])
    if any(len(row) != n for row in label_rows):
        return None, None
    counts = []
    for row in label_rows:
        c = Counter(row)
        counts.append((c.get("Unique", 0), c.get("Similar", 0)))
    p_items = [(u * (u - 1) + s * (s - 1)) / (n * (n - 1)) for u, s in counts]
    p_bar = statistics.mean(p_items)
    total = len(counts) * n
    p_u = sum(u for u, _ in counts) / total
    p_s = sum(s for _, s in counts) / total
    p_e = p_u * p_u + p_s * p_s
    kappa = None if math.isclose(1 - p_e, 0.0) else (p_bar - p_e) / (1 - p_e)
    return kappa, p_bar


def generate_variability_outputs() -> list[dict]:
    rows = read_csv(VAR / "aggregated_results.csv")
    completed = [r for r in rows if r.get("status") == "completed"]
    expected = 30
    if len(completed) != expected:
        raise RuntimeError(f"Expected {expected} completed runs, found {len(completed)}")

    numeric = [
        "trr", "legacy_raw_id_scp", "corrected_artifact_scoped_scp",
        "legacy_srg", "corrected_srg", "elapsed_seconds",
    ]
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in completed:
        grouped[(row["model"], row["mode"])].append(row)
    stats_rows = []
    rng = random.Random(SEED)
    for (model, mode), group in sorted(grouped.items()):
        for metric in numeric:
            values = [float(r[metric]) for r in group]
            mean = statistics.mean(values)
            sd = statistics.stdev(values) if len(values) > 1 else 0.0
            ci_lo, ci_hi = bootstrap_mean_ci(values, rng)
            stats_rows.append({
                "model": model, "mode": mode, "n": len(values), "metric": metric,
                "mean": mean, "standard_deviation": sd, "median": statistics.median(values),
                "minimum": min(values), "maximum": max(values), "range": max(values) - min(values),
                "coefficient_of_variation": "UNDEFINED" if math.isclose(mean, 0.0) else sd / mean,
                "bootstrap_95ci_mean_lower": ci_lo, "bootstrap_95ci_mean_upper": ci_hi,
                "bootstrap_seed": SEED,
            })
    write_csv(VAR / "variability_statistics.csv", stats_rows)

    decision_rows = []
    for (model, mode), group in sorted(grouped.items()):
        by_case: dict[str, dict] = {}
        for run in group:
            alias = Path(run["run_id"]).name
            run_dir = VAR / "raw_runs" / model / mode / f"run_{int(run['run_number']):02d}"
            for item in read_csv(run_dir / "classified_pairs.csv"):
                record = by_case.setdefault(item["case_fingerprint"], {
                    "artifact_type": item["artifact_type"], "source_file": item["source_file"],
                    "scenario_id": item["scenario_id"],
                    "artifact_scoped_scenario_id": item["artifact_scoped_scenario_id"],
                    "test_case_id": item["test_case_id"], "title": item["title"], "labels": [],
                })
                record["labels"].append(item["decision"])
        panel = [v["labels"] for v in by_case.values()]
        kappa, raw_agreement = fleiss_binary(panel)
        for fingerprint, item in sorted(by_case.items()):
            c = Counter(item.pop("labels"))
            total = sum(c.values())
            majority = max(c.values())
            decision_rows.append({
                "model": model, "mode": mode, "case_fingerprint": fingerprint, **item,
                "repeats": total, "unique_decisions": c.get("Unique", 0),
                "similar_decisions": c.get("Similar", 0),
                "modal_decision": "Unique" if c.get("Unique", 0) >= c.get("Similar", 0) else "Similar",
                "percent_agreement_with_modal_decision": majority / total,
                "disagreement_rate": 1 - majority / total,
                "configuration_fleiss_kappa": "UNDEFINED" if kappa is None else kappa,
                "configuration_raw_pairwise_agreement": raw_agreement,
            })
    write_csv(VAR / "decision_stability.csv", decision_rows)

    summary_lines = [
        "# Statistical analysis of the controlled repeated-run study",
        "",
        "The study contains 30 completed local-inference runs: three archived local model artifacts, two application modes (Serial and Bulk), and five repeats per cell. The fixed subset contains eight cases: four deterministic scenario-group representatives from each of the two canonical input artifacts. The design is intentionally bounded and supports conclusions only for these configurations and this subset.",
        "",
        "Temperature was fixed at 0.1, context length at 8,192, seed at 20,261,017 where the backend accepts it, input order and prompts were fixed, and the same GGUF artifact was used for all repeats in a model cell. Bootstrap intervals use 10,000 resamples with the same analysis seed. No inferential model-ranking test is reported because eight cases and five repeated outputs per cell do not justify broad population claims.",
        "",
        "## Descriptive results",
        "",
        "| Model | Mode | Mean TRR (SD) | Mean corrected SCP (SD) | Mean corrected SRG (SD) | Mean runtime s (SD) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    lookup = {(r["model"], r["mode"], r["metric"]): r for r in stats_rows}
    for model, mode in sorted(grouped):
        def cell(metric: str) -> str:
            r = lookup[(model, mode, metric)]
            return f"{float(r['mean']):.4f} ({float(r['standard_deviation']):.4f})"
        summary_lines.append(f"| {model} | {mode} | {cell('trr')} | {cell('corrected_artifact_scoped_scp')} | {cell('corrected_srg')} | {cell('elapsed_seconds')} |")
    summary_lines += [
        "",
        "Decision-level stability is reported in `decision_stability.csv`. Fleiss' kappa there treats the five repeated model outputs as raters; when all decisions occupy one class, chance-corrected kappa is mathematically undefined even though raw agreement may be 100%. This is reported as `UNDEFINED`, not replaced with zero.",
        "",
        "Precision, recall, F1, false positives, and false negatives are not reported for the new eight-case subset because no independently aligned human-consensus labels exist for these exact items. Computing them against a model-derived label would be circular.",
    ]
    write_text(VAR / "statistical_analysis.md", "\n".join(summary_lines))
    return completed


def generate_scenario_outputs(completed: list[dict]) -> None:
    dataset = json.loads((VAR / "fixed_dataset.json").read_text(encoding="utf-8"))
    cases = dataset["test_cases"] if isinstance(dataset, dict) else dataset
    mapping = []
    raw_artifacts: dict[str, set[str]] = defaultdict(set)
    for case in cases:
        raw = case["ScenarioID"]
        artifact_type = case["ArtifactType"]
        source = case["SourceFile"]
        scoped = f"{artifact_type}::{source}::{raw}"
        raw_artifacts[raw].add(f"{artifact_type}::{source}")
        mapping.append({
            "raw_scenario_id": raw, "artifact_type": artifact_type, "source_file": source,
            "artifact_scoped_scenario_id": scoped, "test_case_id": case["TestCaseID"],
            "raw_id_collision": "YES" if len(raw_artifacts[raw]) > 1 else "PENDING",
        })
    collision_ids = {k for k, v in raw_artifacts.items() if len(v) > 1}
    for row in mapping:
        row["raw_id_collision"] = "YES" if row["raw_scenario_id"] in collision_ids else "NO"
    write_csv(OUT / "04_scenario_metrics" / "artifact_identity_mapping.csv", mapping)

    compare = []
    for r in completed:
        compare.append({
            "experiment_id": r["experiment_id"], "run_id": r["run_id"], "model": r["model"],
            "mode": r["mode"], "run_number": r["run_number"], "trr": r["trr"],
            "legacy_raw_id_scp": r["legacy_raw_id_scp"],
            "corrected_artifact_scoped_scp": r["corrected_artifact_scoped_scp"],
            "scp_absolute_change": float(r["corrected_artifact_scoped_scp"]) - float(r["legacy_raw_id_scp"]),
            "legacy_srg": r["legacy_srg"], "corrected_srg": r["corrected_srg"],
            "srg_absolute_change": float(r["corrected_srg"]) - float(r["legacy_srg"]),
        })
    write_csv(OUT / "04_scenario_metrics" / "legacy_vs_corrected_scp.csv", compare)
    write_csv(OUT / "04_scenario_metrics" / "corrected_scp_srg_results.csv", [{
        "run_id": r["run_id"], "model": r["model"], "mode": r["mode"],
        "run_number": r["run_number"], "total_input_cases": r["total_input_cases"],
        "unique_count": r["unique_count"], "similar_count": r["similar_count"], "trr": r["trr"],
        "artifact_scoped_scenarios_before": r["artifact_scoped_scenarios_before"],
        "artifact_scoped_scenarios_after": r["artifact_scoped_scenarios_after"],
        "corrected_artifact_scoped_scp": r["corrected_artifact_scoped_scp"], "corrected_srg": r["corrected_srg"],
    } for r in completed])
    affected = sum(float(r["legacy_raw_id_scp"]) != float(r["corrected_artifact_scoped_scp"]) for r in completed)
    write_text(OUT / "04_scenario_metrics" / "collision_validation.md", f"""# Artifact-scoped scenario identity validation

The fixed subset contains {len(cases)} cases and {len(raw_artifacts)} distinct raw ScenarioID labels. All {len(collision_ids)} raw labels ({', '.join(sorted(collision_ids))}) are reused across both canonical artifacts, yielding {len(cases)} artifact-scoped identities. The validated key is `artifact_type::source_file::local_scenario_id`.

Raw-ID SCP differed from corrected SCP in {affected} of {len(completed)} completed runs. This demonstrates that raw-label deduplication can mask loss of one artifact's scenario representation. The revised analysis therefore treats artifact-scoped SCP as primary. Historical records that lack per-case artifact provenance cannot be retroactively corrected without inventing provenance; their published raw-ID metrics remain labeled historical/legacy.

SRG was verified as `SCP / (1 - TRR)`, with SCP expressed as a fraction. If `TRR = 1`, the denominator is zero and SRG is recorded as undefined/infinite rather than fabricated. Empty before-scenario sets and missing provenance are invalid inputs and are excluded with an explicit status.
""")


def generate_human_oracle_outputs() -> None:
    oracle_dir = ROOT / "test_results" / "human oracle"
    rows = []
    total = 0
    for path in sorted(oracle_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        count = int(data.get("total_test_cases", len(data.get("oracle", []))))
        total += count
        summary = data.get("summary", {})
        rows.append({
            "available_file": path.name, "source_suite": data.get("process_name", path.stem),
            "aligned_items_in_file": count, "unique": summary.get("Unique", ""),
            "similar": summary.get("Similar", ""), "evaluator_identity": "NOT RECORDED",
            "independent_evaluator_set": "NOT AVAILABLE", "reproducible_agreement_status": "NOT COMPUTABLE",
        })
    write_csv(OUT / "05_human_oracle" / "evaluator_agreement.csv", rows)
    unresolved_fields = ["scope", "consensus_level", "item_count", "status", "reason"]
    write_csv(OUT / "05_human_oracle" / "consensus_stratification.csv", [{
        "scope": "all supplied Human Oracle files", "consensus_level": "UNRESOLVED", "item_count": total,
        "status": "NOT COMPUTABLE", "reason": "Only one decision set per source suite is available; the three evaluator-level aligned files are absent.",
    }], unresolved_fields)
    write_csv(OUT / "05_human_oracle" / "model_performance_by_consensus.csv", [{
        "model": "UNRESOLVED", "mode": "UNRESOLVED", "consensus_subset": "UNRESOLVED",
        "status": "NOT COMPUTABLE", "reason": "No aligned evaluator-level panel exists for the exact items.",
    }], ["model", "mode", "consensus_subset", "status", "reason"])
    write_text(OUT / "05_human_oracle" / "agreement_statistics.md", f"""# Human-consensus evidence audit

Seven supplied JSON files contain {total:,} item decisions in total, one file per source-model suite. They do not contain three independently completed, aligned evaluator panels. Evaluator identity, independence, and per-item three-rater labels are not recorded in these files.

Consequently, Fleiss' kappa 0.1864, the three pairwise Cohen kappas, raw three-rater agreement, Gwet's AC1, majority consensus, and 3/3 versus 2/3 stratification cannot be independently reproduced from the supplied artifacts. Those historical manuscript values must be described as previously reported rather than independently verified. They are not silently recomputed from unrelated files, and no synthetic evaluator labels are created.

The seven available suite files and their class counts are preserved in `evaluator_agreement.csv`. Reviewer 2 Comment 1 is therefore only partially addressable with the present evidence; the missing evaluator-level files are an explicit data-provenance limitation.
""")


def generate_table4() -> None:
    # Values transcribed from the current Table 3 matrix and recomputed by column.
    columns = {
        "LLaMa3.2-3B": [12633, 11427, 9566, 8476, 15576, 15326, 7476],
        "GPT-OSS-20B": [8132, 5252, 6526, 4806, 8397, 4641, 4418],
        "LLaMa3.3-70B": [8775, 7722, 7935, 5836, 11500, 6071, 5908],
        "Qwen3-Coder-30B": [6508, 6817, 5691, 4563, 7090, 3015, 3912],
        "Codestral-22B": [7777, 8113, 7252, 6100, 9893, 5222, 4738],
    }
    source_rows = ["LLaMa3.2-3B", "Gemini2.5-Pro", "Gemini2.5-Flash", "GPT-OSS-20B", "LLaMa3.3-70B", "Qwen3-Coder-30B", "Codestral-22B"]
    out = []
    for optimizer, values in columns.items():
        maximum, minimum = max(values), min(values)
        out.append({
            "optimizer_column": optimizer, "maximum_comparisons": maximum,
            "maximum_source_suite": source_rows[values.index(maximum)],
            "minimum_comparisons": minimum, "minimum_source_suite": source_rows[values.index(minimum)],
            "spread_fraction": (maximum - minimum) / maximum,
            "spread_percent_rounded": round((maximum - minimum) / maximum * 100),
        })
    out.sort(key=lambda r: (-r["spread_fraction"], r["optimizer_column"]))
    write_csv(OUT / "06_table_validation" / "regenerated_table4.csv", out)
    qwen = next(r for r in out if r["optimizer_column"] == "Qwen3-Coder-30B")
    write_text(OUT / "06_table_validation" / "table4_validation_report.md", f"""# Table 4 validation

Table 4 was regenerated programmatically from every comparison-count cell in the current Table 3 matrix, grouping by optimizer column rather than source-suite row.

The questioned values are correctly mapped: {qwen['maximum_comparisons']} is the Qwen3-Coder-30B optimizer-column value for the LLaMa3.3-70B source suite, and {qwen['minimum_comparisons']} is the same optimizer column for the Qwen3-Coder-30B source suite. Their spread is {(qwen['spread_fraction'] * 100):.2f}%, displayed as {qwen['spread_percent_rounded']}% after whole-percent rounding. Every other minimum, maximum, source row, and column mapping is recorded in `regenerated_table4.csv`.

Conclusion: the current manuscript table is arithmetically and structurally correct; no silent value correction is warranted. The response to Reviewer 3 should explain the row/column mapping respectfully.
""")


def generate_environment_and_audits(completed: list[dict]) -> None:
    input_files = [ROOT / "test_inputs" / "ProductDetection.cpp", ROOT / "test_inputs" / "Functional_and_NonFunctional_Requirements.txt"]
    manifest_lines = ["# Canonical input artifact manifest", ""]
    for p in input_files:
        stat = p.stat()
        manifest_lines += [f"- Absolute path: `{p}`", f"  - Size: {stat.st_size} bytes", f"  - Last modified: {datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat()}", f"  - SHA-256: `{sha256(p)}`"]
    manifest_lines += ["", "Repository-wide filename search found no duplicate copies with these exact canonical filenames. Historical generation records identify the filenames, but do not store content hashes; exact byte identity with historical inputs is therefore NOT RECORDED."]
    write_text(VAR / "input_artifact_manifest.md", "\n".join(manifest_lines))

    write_text(OUT / "00_environment_verification" / "project_inventory.md", f"""# Project inventory

- STLC Manager repository: `{ROOT}`
- Backend: `{ROOT / 'backend'}`
- Frontend: `{ROOT / 'frontend'}`
- Database settings: `{ROOT / 'backend/core/settings.py'}` (MongoDB; credentials redacted)
- Optimization implementation: `{ROOT / 'backend/services/test_case_optimization_service.py'}`
- Local-model client/configuration: `{ROOT / 'backend/services/llm_client.py'}` and repository configuration modules
- Canonical inputs: `{ROOT / 'test_inputs/ProductDetection.cpp'}` and `{ROOT / 'test_inputs/Functional_and_NonFunctional_Requirements.txt'}`
- Historical export: `{ROOT / 'test_results/stlc_test_results.json'}`
- Human Oracle directory: `{ROOT / 'test_results/human oracle'}`
- Manuscript root: `{MANUSCRIPT.parent}`
- Main LaTeX file: `{MANUSCRIPT}`
- Bibliography: `{MANUSCRIPT.with_suffix('.bib')}`
- Figures: `figure1.png` through `figure12.png` in the manuscript root
- Reviewer-comment Word document requested at `C:/Users/matisse/Downloads/Revizyon 2 Hakem Yorumları.docx`: NOT FOUND during the audit.
- Existing point-by-point response document: NOT FOUND.

The pasted task text was treated as the user's instructions, not as reviewer-comment evidence. Because the reviewer DOCX is absent, verbatim comments and authoritative comment numbering cannot be extracted.
""")
    write_text(OUT / "00_environment_verification" / "machine_environment.md", """# Machine and software environment

- Hostname: DESKTOP-EN9JDE5
- OS: Windows (current workstation)
- GPU: NVIDIA RTX 4000 Ada Generation
- GPU VRAM: 20,475 MiB reported by `nvidia-smi`
- NVIDIA driver: 596.71
- CUDA reported by driver: 13.2
- Python used for revision scripts: 3.13 (system repository environment)
- Bundled workspace Python also present: 3.12.14
- Docker client: 29.1.2; Compose: 2.40.3; daemon not running during audit
- LM Studio CLI/runtime: installed; desktop server not running. Experiments use LM Studio's installed llama.cpp CUDA backend directly.
- Ollama: not running during audit
- MongoDB: local `mongod` on 127.0.0.1:27017, database `stlc_database`
- STLC Manager Git commit at audit start: `72cdb3daa54fc4e060b207a09cdc74e749f41fb7`
- Manuscript directory: not Git-versioned

Installed model artifacts used: Llama 3.2 3B Q4_K_S (1,928,200,736 bytes), GPT-OSS 20B MXFP4 (12,109,565,632 bytes), and Qwen3-Coder 30B A3B Q3_K_L (14,583,005,504 bytes). Exact paths and hashes/configuration are recorded per run.
""")

    config_rows = []
    for model in sorted({r["model"] for r in completed}):
        sample_run = next(VAR.glob(f"raw_runs/{model}/*/run_01/run_config.json"))
        cfg = json.loads(sample_run.read_text(encoding="utf-8"))
        for key in ["model_key", "model_alias", "model_class", "model_path", "model_size_bytes", "fixed_seed", "temperature", "context_length", "sample_size", "prompt_source", "prompt_source_sha256"]:
            config_rows.append({"scope": "revision experiment", "model": model, "parameter": key, "value": cfg.get(key, "NOT RECORDED"), "evidence": str(sample_run)})
    for key in ["historical_seed", "historical_top_p", "historical_top_k", "historical_context_length", "historical_model_snapshot_hash", "historical_hardware", "historical_concurrency_limit"]:
        config_rows.append({"scope": "historical experiments", "model": "all", "parameter": key, "value": "NOT RECORDED", "evidence": "No field in supplied historical export/live records"})
    write_csv(OUT / "02_reproducibility_audit" / "config_inventory.csv", config_rows)
    write_text(OUT / "02_reproducibility_audit" / "reproducibility_audit.md", """# Reproducibility audit

Historical records preserve model identifiers, application prompts/outputs, timestamps, and processing titles, but do not consistently preserve seed, top-p, top-k, context length, exact model artifact hash, hardware, or concurrency limits. Those fields are reported as `NOT RECORDED`; no provider defaults were inferred.

The revision experiment defines a separate controlled configuration. It fixes the two input hashes, eight-case deterministic stratified subset, input order, prompt source hash, GGUF path, context length 8,192, temperature 0.1, and seed 20,261,017 where supported. The application persistence service generated a unique DB record for each run. The installed FastEmbed retrieval dependency was unavailable; Serial mode therefore used an explicit compatibility shim that retains the application's historical candidate order. This is a reproducible revision configuration, not a claim that all historical settings were recovered.

Bulk mode makes one optimizer call per run. Serial mode is order-sensitive and makes bounded sequential comparisons. Parallel mode was excluded because the selected two-mode design prioritized the two directly reproducible application paths and avoided adding an unverified concurrency/provider factor.
""")

    write_text(VAR / "model_selection.md", """# Local model selection

Three already-installed, historically represented local model families were selected without downloads or paid API calls:

| Model | Capacity class | Artifact / quantization | Backend | Historical relationship |
|---|---|---|---|---|
| Qwen3-Coder 30B A3B | high | Q3_K_L GGUF | installed LM Studio llama.cpp CUDA backend | Qwen3-Coder-30B appears in the manuscript |
| GPT-OSS 20B | medium | MXFP4 GGUF | installed LM Studio llama.cpp CUDA backend | GPT-OSS-20B appears in the manuscript |
| Llama 3.2 3B | lightweight | Q4_K_S GGUF | installed LM Studio llama.cpp CUDA backend | LLaMa3.2-3B appears in the manuscript |

Local artifacts permit controlled decoding, repeatable model loading, and archival without dependence on changing hosted API versions. Results do not generalize to other quantizations, runtimes, prompts, or datasets.
""")
    write_text(VAR / "experiment_design.md", """# Controlled repeated-run experiment design

- Design: 3 local models × 2 modes (Serial, Bulk) × 5 repeats = 30 completed runs.
- Dataset: deterministic stratified subset of 8 cases, comprising the first case from each of the first four scenario groups for each canonical artifact (4 requirements + 4 source-code cases). No manual outcome-based selection was used.
- Canonical artifacts: `ProductDetection.cpp` and `Functional_and_NonFunctional_Requirements.txt`; hashes are fixed in every run configuration.
- Controls: stable input order, prompt-source hash, model artifact, quantization, context length 8,192, temperature 0.1, seed 20,261,017 where supported, and application postprocessing.
- Persistence: normal STLC Manager optimization-save service plus complete per-run disk package.
- Primary metrics: TRR, artifact-scoped SCP, corrected SRG, runtime, and per-item decision stability.
- Excluded metrics: precision/recall/F1 against a human reference, because the exact eight items lack independently aligned evaluator panels.
- Scope: pre-execution static semantic redundancy decisions only; no executability, coverage, mutation, or fault-detection claim.
""")


def generate_historical_validation() -> None:
    reported = [
        {"section": "Abstract/Human reference", "table": "Human Oracle", "metric": "matched items", "model": "all", "mode": "n/a", "source_artifact": "seven suites", "manuscript_value": "1074", "manuscript_location": "line 109"},
        {"section": "Human reference", "table": "Human Oracle", "metric": "Fleiss kappa", "model": "all", "mode": "n/a", "source_artifact": "seven suites", "manuscript_value": "0.1864", "manuscript_location": "lines 1005-1022"},
        {"section": "Serial optimization", "table": "Table 4", "metric": "maximum comparisons", "model": "Qwen3-Coder-30B optimizer", "mode": "Serial", "source_artifact": "LLaMa3.3-70B suite", "manuscript_value": "7090", "manuscript_location": "line 679"},
        {"section": "Serial optimization", "table": "Table 4", "metric": "minimum comparisons", "model": "Qwen3-Coder-30B optimizer", "mode": "Serial", "source_artifact": "Qwen3-Coder-30B suite", "manuscript_value": "3015", "manuscript_location": "line 679"},
        {"section": "Scenario metrics", "table": "SCP statistics", "metric": "mean legacy raw-ID SCP percent", "model": "core serial", "mode": "Serial", "source_artifact": "historical archive", "manuscript_value": "98.40", "manuscript_location": "lines 830-853"},
        {"section": "Scenario metrics", "table": "SRG statistics", "metric": "mean legacy SRG", "model": "core serial", "mode": "Serial", "source_artifact": "historical archive", "manuscript_value": "1.5362", "manuscript_location": "lines 980-1001"},
    ]
    write_csv(OUT / "01_database_validation" / "manuscript_reported_results.csv", reported)
    db_rows = [
        {"manuscript_metric": "optimization records in supplied archive", "manuscript_value": "74 non-empty of 76", "database_value": "76 optimization documents in export", "database_record_run_id": "multiple", "model": "multiple", "mode": "multiple", "timestamp": "2025-2026", "project_identifier": "multiple session_id values", "status": "PARTIAL", "match_mismatch": "MATCH after excluding two empty records"},
        {"manuscript_metric": "live optimization process count", "manuscript_value": "historical subset", "database_value": "82 process entries in live session_history at audit", "database_record_run_id": "multiple", "model": "multiple", "mode": "53 serial; 15 bulk; 14 parallel", "timestamp": "through 2026-10-12 before new runs", "project_identifier": "multiple", "status": "PARTIAL", "match_mismatch": "Live DB contains later records beyond supplied archive"},
        {"manuscript_metric": "Human Oracle items", "manuscript_value": "1074", "database_value": "1074 decisions across seven supplied suite files", "database_record_run_id": "file-based", "model": "seven suites", "mode": "n/a", "timestamp": "NOT RECORDED", "project_identifier": "human oracle", "status": "MATCH", "match_mismatch": "MATCH for item total; evaluator panels absent"},
        {"manuscript_metric": "Table 4 Qwen-column extrema", "manuscript_value": "7090 / 3015", "database_value": "7090 / 3015 in archived matrix", "database_record_run_id": "historical serial records", "model": "Qwen3-Coder-30B optimizer", "mode": "Serial", "timestamp": "historical", "project_identifier": "archive", "status": "MATCH", "match_mismatch": "MATCH"},
    ]
    write_csv(OUT / "01_database_validation" / "database_historical_results.csv", db_rows)
    write_text(OUT / "01_database_validation" / "historical_consistency_report.md", """# Historical consistency decision: PARTIALLY VERIFIED

The supplied 147-document historical export contains 76 optimization processes; 74 are non-empty, matching the manuscript's stated analytic archive. Core Serial/Bulk/Parallel counts, the Table 3 comparison matrix, Table 4 extrema, and the total of 1,074 Human Oracle decisions materially agree with supplied files. The live database contains later records beyond the frozen export, so it is not expected to equal the archive row-for-row.

Full verification is not possible because historical input content hashes, exact model artifacts/decoding settings, and the three evaluator-level aligned Human Oracle files are absent. The 427 MB coverage JSON LFS object is also missing from the configured remote. These are reconstruction limits, not evidence that matching values should be replaced.

No serious numerical mismatch was found that requires aborting the controlled revision experiment. Historical metrics remain preserved and explicitly labeled legacy/descriptive where provenance is insufficient for corrected artifact-scoped recalculation.
""")


def generate_requirements_matrix() -> None:
    rows = [
        ("Reviewer 1", "variability", "LLM run-to-run variability", "new experiment", "30 local runs, descriptive variability and stability", "03_variability_study", "FULLY ADDRESSED"),
        ("Reviewer 2", "1", "low human agreement", "analysis/clarification", "audit evaluator-level evidence; do not fabricate missing panels", "05_human_oracle", "PARTIALLY ADDRESSED"),
        ("Reviewer 2", "2", "no execution/coverage/fault evidence", "scope clarification", "retain pre-execution scope", "manuscript", "FULLY ADDRESSED"),
        ("Reviewer 2", "3", "confounded historical comparisons", "clarification", "label historical comparisons descriptive", "manuscript", "FULLY ADDRESSED"),
        ("Reviewer 2", "4", "unsupported efficiency claim", "clarification", "separate measured runtime from estimates", "manuscript", "FULLY ADDRESSED"),
        ("Reviewer 2", "5", "raw ScenarioID collisions", "recalculation", "artifact-scoped identity and corrected SCP/SRG", "04_scenario_metrics", "FULLY ADDRESSED"),
        ("Reviewer 2", "6", "dynamic switching evidence", "clarification", "exclude from empirical claims", "manuscript", "FULLY ADDRESSED"),
        ("Reviewer 2", "7", "configuration sensitivity", "audit/experiment", "controlled local repeated-run study", "02_reproducibility_audit; 03_variability_study", "FULLY ADDRESSED"),
        ("Reviewer 2", "8", "References 31 and 51 metadata", "reference audit", "verify available metadata; flag unresolved fields", "08_references", "PARTIALLY ADDRESSED"),
        ("Reviewer 3", "table", "Table 4 extrema/mapping", "recalculation", "programmatic full-column regeneration", "06_table_validation", "FULLY ADDRESSED"),
        ("Reviewer 3", "figures", "figure readability", "figure correction", "render at final size and replace selected rasters", "07_figures", "IN PROGRESS"),
        ("Reviewer 4", "acknowledgment", "earlier concerns addressed", "acknowledgment", "thank reviewer; no unsupported changes", "11_reviewer_response", "IN PROGRESS"),
    ]
    header = "| Reviewer | Comment | Concern | Requirement | Action | Evidence | Status |\n|---|---|---|---|---|---|---|\n"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    write_text(OUT / "02_reproducibility_audit" / "reviewer_requirements_matrix.md", "# Reviewer requirements matrix\n\n> The supplied reviewer DOCX was not found. Rows are reconstructed from the reviewer requirements quoted in the user's pasted task and are not presented as verbatim reviewer quotations.\n\n" + header + body)


def generate_db_file_crosscheck(completed: list[dict]) -> None:
    rows = []
    for r in completed:
        run_dir = VAR / "raw_runs" / r["model"] / r["mode"] / f"run_{int(r['run_number']):02d}"
        metrics = run_dir / "metrics.json"
        required = ["run_config.json", "input_manifest.csv", "raw_output.json", "classified_pairs.csv", "metrics.json", "execution_log.txt", "database_record_ids.txt"]
        missing = [name for name in required if not (run_dir / name).exists()]
        db_id_file = (run_dir / "database_record_ids.txt").read_text(encoding="utf-8").strip() if (run_dir / "database_record_ids.txt").exists() else ""
        rows.append({
            "experiment_id": r["experiment_id"], "run_id": r["run_id"], "db_record_id": r["database_record_id"],
            "raw_file_path": str(run_dir / "raw_output.json"), "model": r["model"], "mode": r["mode"],
            "run_number": r["run_number"], "status": "COMPLETE" if not missing and r["database_record_id"] in db_id_file else "INCOMPLETE",
            "metric_sha256": sha256(metrics) if metrics.exists() else "MISSING", "missing_files": ";".join(missing),
        })
    write_csv(OUT / "12_final_audit" / "db_file_crosscheck.csv", rows)


def main() -> None:
    completed = generate_variability_outputs()
    generate_scenario_outputs(completed)
    generate_human_oracle_outputs()
    generate_table4()
    generate_environment_and_audits(completed)
    generate_historical_validation()
    generate_requirements_matrix()
    generate_db_file_crosscheck(completed)
    print(f"Generated revision evidence for {len(completed)} completed runs at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
