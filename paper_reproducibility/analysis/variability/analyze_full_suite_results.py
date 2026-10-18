from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "07_variability_analysis" / "aggregated_results.csv"
VAR = ROOT / "07_variability_analysis"
SCEN = ROOT / "08_scenario_metrics"
TABLES = ROOT / "10_tables"
EXPECTED_RUNS = 60
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20261017


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def f(value: str | float | int | None) -> float:
    if value in (None, ""):
        return math.nan
    return float(value)


def bootstrap_mean_ci(values: list[float]) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    rng = random.Random(BOOTSTRAP_SEED + len(values) + int(sum(values) * 1_000_000))
    means = []
    for _ in range(BOOTSTRAP_DRAWS):
        means.append(statistics.fmean(rng.choice(values) for _ in values))
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    return lo, hi


def describe(values: list[float], prefix: str) -> dict[str, Any]:
    values = [v for v in values if not math.isnan(v)]
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    lo, hi = bootstrap_mean_ci(values)
    return {
        f"{prefix}_mean": mean,
        f"{prefix}_sample_sd": sd,
        f"{prefix}_median": statistics.median(values),
        f"{prefix}_minimum": min(values),
        f"{prefix}_maximum": max(values),
        f"{prefix}_range": max(values) - min(values),
        f"{prefix}_cv": sd / mean if mean != 0 else (0.0 if sd == 0 else "undefined"),
        f"{prefix}_bootstrap95_low": lo,
        f"{prefix}_bootstrap95_high": hi,
    }


def fleiss_binary(counts: list[tuple[int, int]], raters: int) -> tuple[float | str, float]:
    p_items = [(a * (a - 1) + b * (b - 1)) / (raters * (raters - 1)) for a, b in counts]
    raw = statistics.fmean(p_items)
    total = len(counts) * raters
    p_a = sum(a for a, _ in counts) / total
    p_b = sum(b for _, b in counts) / total
    expected = p_a * p_a + p_b * p_b
    if math.isclose(expected, 1.0):
        return "undefined due to single-category occupancy", raw
    return (raw - expected) / (1.0 - expected), raw


def discover_run_dirs() -> list[Path]:
    found = []
    for base in (ROOT / "05_bulk_runs", ROOT / "06_parallel_runs"):
        for metrics in base.rglob("metrics.json"):
            if "attempts" not in metrics.parts:
                found.append(metrics.parent)
    return sorted(found)


def main() -> None:
    rows = read_csv(AGG)
    rows = [r for r in rows if r.get("experiment_id") == "reviewer_revision_2026_full_suite" and r.get("status") == "COMPLETE"]
    run_ids = [r["run_id"] for r in rows]
    if len(rows) != EXPECTED_RUNS:
        raise SystemExit(f"Expected {EXPECTED_RUNS} successful runs, found {len(rows)}")
    if len(set(run_ids)) != EXPECTED_RUNS:
        raise SystemExit("Duplicate successful run IDs detected")
    if any("SERIAL" in run_id.upper() or "Serial" in r.get("mode", "") for run_id, r in zip(run_ids, rows)):
        raise SystemExit("Serial run detected in new experiment")

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["suite_id"], row["model_key"], row["mode"])].append(row)
    if len(grouped) != 12 or any(len(v) != 5 for v in grouped.values()):
        raise SystemExit(f"Expected 12 cells with five repeats, got {[((k), len(v)) for k, v in grouped.items()]}")

    metric_names = [
        "unique_count", "similar_count", "trr", "artifact_scoped_scp",
        "artifact_scoped_srg", "comparison_count", "runtime_seconds", "transitivity_conflicts",
    ]
    variability = []
    stability = []
    unstable = []
    stability_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    dirs_by_id = {}
    for run_dir in discover_run_dirs():
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("status") == "COMPLETE":
            dirs_by_id[metrics["run_id"]] = run_dir

    for key, cell in sorted(grouped.items()):
        suite_id, model_key, mode = key
        cell.sort(key=lambda r: int(r["repeat"]))
        out: dict[str, Any] = {
            "suite_id": suite_id,
            "model_key": model_key,
            "model_display": cell[0]["model_display"],
            "mode": mode,
            "repeats": len(cell),
            "total_input_cases": int(cell[0]["total_input_cases"]),
        }
        for metric in metric_names:
            out.update(describe([f(r[metric]) for r in cell], metric))
        variability.append(out)

        item_decisions: dict[str, list[str]] = defaultdict(list)
        item_meta: dict[str, dict[str, str]] = {}
        for run in cell:
            run_dir = dirs_by_id[run["run_id"]]
            decisions = read_csv(run_dir / "case_classifications.csv")
            if len(decisions) != int(run["total_input_cases"]):
                raise SystemExit(f"Incomplete case classifications for {run['run_id']}")
            for decision in decisions:
                uid = decision["case_uid"]
                item_decisions[uid].append(decision["decision"])
                item_meta[uid] = decision
        counts = []
        agreements = []
        for uid, decisions in sorted(item_decisions.items()):
            tally = Counter(decisions)
            unique_n, similar_n = tally["Unique"], tally["Similar"]
            if unique_n + similar_n != 5:
                raise SystemExit(f"Non-binary or missing decisions for {key} {uid}: {tally}")
            modal_n = max(unique_n, similar_n)
            modal_label = "Unique" if unique_n > similar_n else "Similar"
            agreement = modal_n / 5
            disagreement = 1 - agreement
            counts.append((unique_n, similar_n))
            agreements.append(agreement)
            row = {
                "suite_id": suite_id, "model_key": model_key, "model_display": cell[0]["model_display"],
                "mode": mode, "case_uid": uid, "scenario_id": item_meta[uid]["scenario_id"],
                "artifact_scoped_scenario_id": item_meta[uid]["artifact_scoped_scenario_id"],
                "test_case_id": item_meta[uid]["test_case_id"], "title": item_meta[uid]["title"],
                "unique_votes": unique_n, "similar_votes": similar_n, "modal_label": modal_label,
                "modal_agreement": agreement, "disagreement_rate": disagreement,
            }
            stability.append(row)
            if agreement < 1.0:
                unstable.append(row)
        kappa, raw_agreement = fleiss_binary(counts, 5)
        stable_count = sum(1 for a in agreements if a == 1.0)
        summary = {
            "suite_id": suite_id, "model_key": model_key, "model_display": cell[0]["model_display"],
            "mode": mode, "items": len(agreements), "stable_items": stable_count,
            "unstable_items": len(agreements) - stable_count,
            "unstable_item_percentage": 100 * (len(agreements) - stable_count) / len(agreements),
            "mean_modal_agreement": statistics.fmean(agreements),
            "mean_disagreement_rate": statistics.fmean(1 - a for a in agreements),
            "repeated_run_fleiss_kappa": kappa, "raw_repeated_run_agreement": raw_agreement,
        }
        stability_lookup[key] = summary

    write_csv(VAR / "variability_statistics.csv", variability)
    write_csv(VAR / "decision_stability.csv", stability)
    write_csv(VAR / "unstable_items.csv", unstable)
    write_csv(VAR / "decision_stability_summary.csv", list(stability_lookup.values()))

    # Scenario identity mapping and raw/scoped metrics. Each suite is intentionally analyzed alone
    # and also as a combined corpus to expose raw ScenarioID collisions across artifacts.
    mapping: dict[tuple[str, str], dict[str, str]] = {}
    for suite_id in ("FULLREQ", "FULLSRC"):
        suite = json.loads((ROOT / "04_full_suite_design" / "suites" / f"{suite_id}.json").read_text(encoding="utf-8"))
        for case in suite["cases"]:
            mapping[(suite_id, case["CaseUID"])] = {
                "suite_id": suite_id, "case_uid": case["CaseUID"], "scenario_id": case["ScenarioID"],
                "artifact_scoped_scenario_id": case["ArtifactScopedScenarioID"],
                "test_case_id": case["TestCaseID"], "source_artifact": suite["source_artifact"],
            }
    mapping_rows = list(mapping.values())
    write_csv(SCEN / "scenario_identity_mapping.csv", mapping_rows)
    collision_groups: dict[str, set[str]] = defaultdict(set)
    for row in mapping_rows:
        collision_groups[row["scenario_id"]].add(row["artifact_scoped_scenario_id"])
    collisions = {raw: scoped for raw, scoped in collision_groups.items() if len(scoped) > 1}
    raw_vs_scoped = []
    for row in rows:
        raw_vs_scoped.append({
            "analysis_scope": "single_suite", "run_id": row["run_id"], "suite_id": row["suite_id"], "model_key": row["model_key"],
            "mode": row["mode"], "repeat": row["repeat"], "legacy_raw_id_scp": row["legacy_raw_id_scp"],
            "artifact_scoped_scp": row["artifact_scoped_scp"],
            "difference": f(row["artifact_scoped_scp"]) - f(row["legacy_raw_id_scp"]),
        })
    # Pair the two fixed suites for the same model/mode/repeat. This combined view is
    # where raw labels such as TS_001 can mask loss in one artifact because the same
    # label remains represented by the other artifact.
    by_pair = {(r["suite_id"], r["model_key"], r["mode"], int(r["repeat"])): r for r in rows}
    for model_key in sorted({r["model_key"] for r in rows}):
        for mode in sorted({r["mode"] for r in rows}):
            for repeat in range(1, 6):
                paired = [by_pair[(suite_id, model_key, mode, repeat)] for suite_id in ("FULLREQ", "FULLSRC")]
                retained_raw: set[str] = set()
                retained_scoped: set[str] = set()
                before_raw: set[str] = set()
                before_scoped: set[str] = set()
                run_ids = []
                for run in paired:
                    run_ids.append(run["run_id"])
                    decisions = read_csv(dirs_by_id[run["run_id"]] / "case_classifications.csv")
                    for decision in decisions:
                        before_raw.add(decision["scenario_id"])
                        before_scoped.add(decision["artifact_scoped_scenario_id"])
                        if decision["decision"] == "Unique":
                            retained_raw.add(decision["scenario_id"])
                            retained_scoped.add(decision["artifact_scoped_scenario_id"])
                raw_scp = len(retained_raw) / len(before_raw)
                scoped_scp = len(retained_scoped) / len(before_scoped)
                raw_vs_scoped.append({
                    "analysis_scope": "combined_two_suite", "run_id": "+".join(run_ids), "suite_id": "COMBINED",
                    "model_key": model_key, "mode": mode, "repeat": repeat,
                    "legacy_raw_id_scp": raw_scp, "artifact_scoped_scp": scoped_scp,
                    "difference": scoped_scp - raw_scp,
                })
    write_csv(SCEN / "raw_vs_scoped_scp.csv", raw_vs_scoped)
    combined = [r for r in raw_vs_scoped if r["analysis_scope"] == "combined_two_suite"]
    differing = [r for r in combined if not math.isclose(float(r["difference"]), 0.0)]
    report = [
        "# Scenario collision report", "", f"Mapped cases: {len(mapping_rows)}.",
        f"Distinct raw ScenarioID values: {len(collision_groups)}.",
        f"Distinct artifact-scoped identities: {len({r['artifact_scoped_scenario_id'] for r in mapping_rows})}.",
        f"Raw IDs that map to more than one artifact-scoped identity: {len(collisions)}.", "",
        f"Combined paired runs evaluated: {len(combined)}.",
        f"Combined paired runs where raw-ID SCP differs from artifact-scoped SCP: {len(differing)}.",
        (f"Observed combined SCP difference range (scoped minus raw): "
         f"{min(float(r['difference']) for r in combined):.6f} to {max(float(r['difference']) for r in combined):.6f}."), "",
        "## Collisions", "",
    ]
    report.extend(f"- `{raw}` -> {', '.join(f'`{v}`' for v in sorted(values))}" for raw, values in sorted(collisions.items()))
    report.extend(["", "The primary new-study metric is artifact-scoped SCP. Raw-ID SCP is retained only as a legacy comparison."])
    (SCEN / "scenario_collision_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    # Manuscript-ready Tables A-D; Tables E-F derive from the independent Human Oracle outputs.
    table_a = []
    for key, cell in sorted(grouped.items()):
        suite_id, model_key, mode = key
        table_a.append({
            "source_artifact": cell[0]["source_artifact"], "suite_id": suite_id,
            "suite_size": cell[0]["total_input_cases"], "scenario_count": cell[0]["artifact_scoped_scenarios_before"],
            "model": cell[0]["model_display"], "mode": mode, "repeats": 5,
        })
    write_csv(TABLES / "table_A_full_suite_design.csv", table_a)
    for wanted_mode, filename in (("Local Bulk", "table_B_local_bulk_variability.csv"), ("Controlled Local Parallel", "table_C_controlled_local_parallel_variability.csv")):
        table = []
        for row in variability:
            if row["mode"] != wanted_mode:
                continue
            key = (row["suite_id"], row["model_key"], row["mode"])
            s = stability_lookup[key]
            table.append({
                "suite_id": row["suite_id"], "model": row["model_display"], "total": row["total_input_cases"],
                "unique_mean": row["unique_count_mean"], "unique_sd": row["unique_count_sample_sd"],
                "similar_mean": row["similar_count_mean"], "similar_sd": row["similar_count_sample_sd"],
                "trr_mean": row["trr_mean"], "trr_sd": row["trr_sample_sd"],
                "scoped_scp_mean": row["artifact_scoped_scp_mean"], "scoped_scp_sd": row["artifact_scoped_scp_sample_sd"],
                "srg_mean": row["artifact_scoped_srg_mean"], "srg_sd": row["artifact_scoped_srg_sample_sd"],
                "modal_agreement": s["mean_modal_agreement"], "repeated_run_kappa": s["repeated_run_fleiss_kappa"],
                "comparison_count_mean": row["comparison_count_mean"], "runtime_seconds_mean": row["runtime_seconds_mean"],
                "runtime_seconds_sd": row["runtime_seconds_sample_sd"],
            })
        write_csv(TABLES / filename, table)
    write_csv(TABLES / "table_D_decision_stability.csv", list(stability_lookup.values()))
    print(f"Analyzed {len(rows)} successful runs across {len(grouped)} cells")


if __name__ == "__main__":
    main()
