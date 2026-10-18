from __future__ import annotations

import csv
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HUMAN = ROOT / "03_human_oracle"
TABLES = ROOT / "10_tables"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def safe_div(a: int, b: int) -> float:
    return a / b if b else 0.0


def defined_values(rows: list[dict[str, str]], field: str) -> list[float]:
    values = []
    for row in rows:
        try:
            values.append(float(row[field]))
        except (TypeError, ValueError):
            continue
    return values


def pooled(subset: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    tp = sum(int(r["tp"]) for r in rows)
    tn = sum(int(r["tn"]) for r in rows)
    fp = sum(int(r["fp"]) for r in rows)
    fn = sum(int(r["fn"]) for r in rows)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)
    f1 = safe_div(2 * precision * recall, precision + recall)
    return {
        "consensus_subset": subset,
        "optimizer_configurations": len(rows),
        "pooled_configuration_item_decisions": tp + tn + fp + fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "balanced_accuracy": (recall + specificity) / 2,
        "false_removal_count": fp,
        "false_removal_rate": safe_div(fp, fp + tn),
        "macro_mean_precision_defined_only": statistics.fmean(defined_values(rows, "precision")),
        "undefined_precision_configurations": len(rows) - len(defined_values(rows, "precision")),
        "macro_mean_recall_defined_only": statistics.fmean(defined_values(rows, "recall")),
        "undefined_recall_configurations": len(rows) - len(defined_values(rows, "recall")),
        "macro_mean_f1_defined_only": statistics.fmean(defined_values(rows, "f1")),
        "undefined_f1_configurations": len(rows) - len(defined_values(rows, "f1")),
        "macro_mean_balanced_accuracy_defined_only": statistics.fmean(defined_values(rows, "balanced_accuracy")),
        "macro_mean_false_removal_rate_defined_only": statistics.fmean(defined_values(rows, "false_removal_rate")),
    }


def main() -> None:
    sources = [
        ("all", HUMAN / "optimizer_performance_all.csv"),
        ("3/3 unanimous", HUMAN / "optimizer_performance_unanimous.csv"),
        ("2/3 majority", HUMAN / "optimizer_performance_majority.csv"),
    ]
    table_e = []
    for label, path in sources:
        rows = read(path)
        if len(rows) != 72:
            raise SystemExit(f"Expected 72 optimizer configurations in {path}, found {len(rows)}")
        table_e.append(pooled(label, rows))
    write(TABLES / "table_E_human_consensus_robustness.csv", table_e)

    agreement = read(HUMAN / "agreement_statistics.csv")
    overall = next(r for r in agreement if r["source_model"] == "Overall")
    strata = read(HUMAN / "consensus_stratification.csv")
    unanimous = next(r for r in strata if r["source_model"] == "Overall" and r["consensus_strength"] == "3/3 unanimous")
    majority = next(r for r in strata if r["source_model"] == "Overall" and r["consensus_strength"] == "2/3 majority")
    table_f = [{
        "scope": "Overall",
        "aligned_items": overall["aligned_items"],
        "fleiss_kappa": overall["fleiss_kappa"],
        "cohen_h1_h2": overall["cohen_h1_h2"],
        "cohen_h1_h3": overall["cohen_h1_h3"],
        "cohen_h2_h3": overall["cohen_h2_h3"],
        "raw_three_way_agreement": overall["raw_three_way_agreement"],
        "gwet_ac1": overall["gwet_ac1"],
        "unanimous_count": unanimous["count"],
        "unanimous_percentage": unanimous["percentage"],
        "majority_count": majority["count"],
        "majority_percentage": majority["percentage"],
        "unresolved": overall["unresolved"],
    }]
    write(TABLES / "table_F_human_agreement.csv", table_f)
    print("Created manuscript Tables E and F from 72 aligned optimizer configurations and 1,074 human items")


if __name__ == "__main__":
    main()
