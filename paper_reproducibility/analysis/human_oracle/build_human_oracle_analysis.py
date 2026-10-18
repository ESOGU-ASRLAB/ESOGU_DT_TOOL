from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(r"C:\Users\matisse\Desktop\STLC-Manager\test_results\reviewer_revision_2026\final_revision")
OUT = ROOT / "03_human_oracle"
ARCHIVE = OUT / "public_archive"
RAW = ARCHIVE / "test_results" / "human oracle"
ARCHIVE_ANALYSIS = ARCHIVE / "test_results" / "analysis"
TOOL = ARCHIVE / "test_results" / "human_oracle_pyside6.py"

RATERS = ("Human 1", "Human 2", "Human 3")
CATEGORIES = ("Unique", "Similar", "Unclear")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_model(filename: str) -> str:
    stem = Path(filename).stem.replace("_", ".")
    aliases = {
        "Gemini2.5-Flash": "Gemini2.5-Flash",
        "Gemini2.5-Pro": "Gemini2.5-Pro",
        "LLaMa3.2-3B": "LLaMa3.2-3B",
        "LLaMa3.3-70B": "LLaMa3.3-70B",
    }
    return aliases.get(stem, stem)


def norm(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def signature(item: dict[str, Any]) -> str:
    fields = [item.get("original_id"), item.get("title"), item.get("description"), item.get("objective")]
    return hashlib.sha256("\x1f".join(norm(v) for v in fields).encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fleiss_kappa(votes: list[list[str]]) -> float:
    n = len(votes)
    r = len(votes[0]) if votes else 0
    if n == 0 or r < 2 or any(len(row) != r for row in votes):
        return math.nan
    counts = [[Counter(row)[category] for category in CATEGORIES] for row in votes]
    p_item = [sum(value * (value - 1) for value in row) / (r * (r - 1)) for row in counts]
    p_bar = sum(p_item) / n
    marginals = [sum(row[j] for row in counts) / (n * r) for j in range(len(CATEGORIES))]
    p_expected = sum(value * value for value in marginals)
    return (p_bar - p_expected) / (1 - p_expected) if p_expected != 1 else math.nan


def cohen_kappa(left: list[str], right: list[str]) -> float:
    if not left or len(left) != len(right):
        return math.nan
    n = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / n
    lc, rc = Counter(left), Counter(right)
    expected = sum((lc[c] / n) * (rc[c] / n) for c in CATEGORIES)
    return (observed - expected) / (1 - expected) if expected != 1 else math.nan


def gwet_ac1(votes: list[list[str]]) -> float:
    """Multi-rater AC1 with the standard chance term for q categories."""
    n = len(votes)
    r = len(votes[0]) if votes else 0
    if n == 0 or r < 2:
        return math.nan
    observed = sum(
        sum(value * (value - 1) for value in Counter(row).values()) / (r * (r - 1))
        for row in votes
    ) / n
    marginals = [sum(Counter(row)[c] for row in votes) / (n * r) for c in CATEGORIES]
    q = len(CATEGORIES)
    expected = sum(p * (1 - p) for p in marginals) / (q - 1)
    return (observed - expected) / (1 - expected) if expected != 1 else math.nan


def metric(value: float) -> str:
    return "UNDEFINED" if math.isnan(value) else f"{value:.6f}"


def classification_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    tp = sum(r["consensus"] == "Similar" and r["prediction"] == "Similar" for r in rows)
    tn = sum(r["consensus"] == "Unique" and r["prediction"] == "Unique" for r in rows)
    fp = sum(r["consensus"] == "Unique" and r["prediction"] == "Similar" for r in rows)
    fn = sum(r["consensus"] == "Similar" and r["prediction"] == "Unique" for r in rows)
    precision = tp / (tp + fp) if tp + fp else math.nan
    recall = tp / (tp + fn) if tp + fn else math.nan
    f1 = 2 * precision * recall / (precision + recall) if not math.isnan(precision) and not math.isnan(recall) and precision + recall else math.nan
    specificity = tn / (tn + fp) if tn + fp else math.nan
    balanced = (recall + specificity) / 2 if not math.isnan(recall) and not math.isnan(specificity) else math.nan
    false_removal_rate = fp / (tn + fp) if tn + fp else math.nan
    return {
        "n": len(rows), "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "precision": metric(precision), "recall": metric(recall), "f1": metric(f1),
        "balanced_accuracy": metric(balanced), "false_removal_count": fp,
        "false_removal_rate": metric(false_removal_rate),
    }


def load_raw() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    manifest: list[dict[str, Any]] = []
    long_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    hashes: defaultdict[str, list[str]] = defaultdict(list)
    for rater in RATERS:
        directory = RAW / rater
        for path in sorted(directory.glob("*.json")):
            file_hash = sha256(path)
            hashes[file_hash].append(str(path.relative_to(ARCHIVE)))
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                oracle = payload.get("oracle") or []
                model = canonical_model(path.name)
                available = sorted({key for item in oracle for key in item})
                manifest.append({
                    "evaluator": rater, "source_file": str(path.relative_to(ARCHIVE)),
                    "source_model": model, "number_of_rows": len(oracle),
                    "available_fields": ";".join(available), "sha256": file_hash,
                    "duplicate_status": "PENDING", "parsing_status": "OK",
                })
                if payload.get("total_test_cases") != len(oracle):
                    errors.append(f"{rater}/{path.name}: declared total differs from oracle length")
                for position, item in enumerate(oracle, 1):
                    label = str(item.get("decision", "")).strip().title()
                    if label not in CATEGORIES:
                        errors.append(f"{rater}/{path.name}/{position}: invalid label {label!r}")
                    long_rows.append({
                        "evaluator": rater, "source_model": model, "position": position,
                        "row_ref": str(item.get("row_ref", "")),
                        "test_case_id": str(item.get("original_id", "")),
                        "title": str(item.get("title", "")),
                        "description": str(item.get("description", "")),
                        "objective": str(item.get("objective", "")),
                        "decision": label, "similar_to": str(item.get("similar_to", "")),
                        "confidence": str(item.get("confidence", "")),
                        "timestamp": str(item.get("oracle_saved_at", "")),
                        "signature": signature(item),
                    })
            except Exception as exc:
                manifest.append({
                    "evaluator": rater, "source_file": str(path.relative_to(ARCHIVE)),
                    "source_model": canonical_model(path.name), "number_of_rows": 0,
                    "available_fields": "", "sha256": file_hash,
                    "duplicate_status": "PENDING", "parsing_status": f"ERROR: {exc}",
                })
                errors.append(f"{rater}/{path.name}: {exc}")
    for row in manifest:
        row["duplicate_status"] = "DUPLICATE_SHA256" if len(hashes[row["sha256"]]) > 1 else "UNIQUE_SHA256"
    return manifest, long_rows, errors


def align(long_rows: list[dict[str, Any]], errors: list[str]) -> list[dict[str, Any]]:
    grouped: defaultdict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in long_rows:
        grouped[(row["source_model"], row["row_ref"])][row["evaluator"]] = row
    aligned: list[dict[str, Any]] = []
    for (model, row_ref), raters in sorted(grouped.items()):
        base = next(iter(raters.values()))
        sigs = {row["signature"] for row in raters.values()}
        labels = [raters.get(r, {}).get("decision", "") for r in RATERS]
        counts = Counter(label for label in labels if label)
        top = counts.most_common()
        unresolved = len(raters) != 3 or not top or (len(top) > 1 and top[0][1] == top[1][1])
        consensus = "Unresolved" if unresolved else top[0][0]
        max_votes = top[0][1] if top else 0
        strength = "3/3 unanimous" if max_votes == 3 else ("2/3 majority" if max_votes == 2 else "unresolved")
        if len(sigs) != 1:
            errors.append(f"Content mismatch for {model}/{row_ref}")
        aligned.append({
            "canonical_item_id": hashlib.sha256(f"{model}|{row_ref}|{base['signature']}".encode()).hexdigest(),
            "source_model": model, "row_ref": row_ref,
            "ScenarioID": "NOT AVAILABLE IN PUBLIC EVALUATOR EXPORT",
            "TestCaseID": base["test_case_id"], "title": base["title"],
            "description": base["description"], "objective": base["objective"],
            "Human1": labels[0], "Human2": labels[1], "Human3": labels[2],
            "Human1_confidence": raters.get("Human 1", {}).get("confidence", ""),
            "Human2_confidence": raters.get("Human 2", {}).get("confidence", ""),
            "Human3_confidence": raters.get("Human 3", {}).get("confidence", ""),
            "agreement_count": max_votes, "consensus_label": consensus,
            "consensus_strength": strength, "unresolved_status": "YES" if unresolved else "NO",
            "content_signature_match": "YES" if len(sigs) == 1 else "NO",
        })
    return aligned


def agreement_rows(aligned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    models = sorted({row["source_model"] for row in aligned}) + ["Overall"]
    for model in models:
        group = aligned if model == "Overall" else [r for r in aligned if r["source_model"] == model]
        complete = [r for r in group if r["unresolved_status"] == "NO" or all(r[f"Human{i}"] for i in (1, 2, 3))]
        votes = [[r["Human1"], r["Human2"], r["Human3"]] for r in complete]
        h1, h2, h3 = ([r[f"Human{i}"] for r in complete] for i in (1, 2, 3))
        counts = {f"human{i}_{c.lower()}": sum(r[f"Human{i}"] == c for r in complete) for i in (1, 2, 3) for c in CATEGORIES}
        consensus = Counter(r["consensus_label"] for r in group)
        result.append({
            "source_model": model, "aligned_items": len(group), "complete_three_rater_items": len(complete),
            **counts, "majority_unique": consensus["Unique"], "majority_similar": consensus["Similar"],
            "unresolved": consensus["Unresolved"],
            "raw_three_way_agreement": metric(sum(len(set(v)) == 1 for v in votes) / len(votes) if votes else math.nan),
            "fleiss_kappa": metric(fleiss_kappa(votes)),
            "cohen_h1_h2": metric(cohen_kappa(h1, h2)),
            "cohen_h1_h3": metric(cohen_kappa(h1, h3)),
            "cohen_h2_h3": metric(cohen_kappa(h2, h3)),
            "gwet_ac1": metric(gwet_ac1(votes)),
        })
    return result


def consensus_rows(aligned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for model in sorted({r["source_model"] for r in aligned}) + ["Overall"]:
        group = aligned if model == "Overall" else [r for r in aligned if r["source_model"] == model]
        for strength in ("3/3 unanimous", "2/3 majority", "unresolved"):
            rows = [r for r in group if r["consensus_strength"] == strength]
            counts = Counter(r["consensus_label"] for r in rows)
            output.append({
                "source_model": model, "consensus_strength": strength, "count": len(rows),
                "percentage": f"{100 * len(rows) / len(group):.6f}" if group else "UNDEFINED",
                "unique": counts["Unique"], "similar": counts["Similar"], "unresolved": counts["Unresolved"],
            })
    return output


def optimizer_metrics(aligned: list[dict[str, Any]]) -> None:
    source = ARCHIVE_ANALYSIS / "optimizer_item_level_decisions.csv"
    if not source.exists():
        return
    consensus = {(r["source_model"], r["row_ref"]): r for r in aligned}
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        decisions = list(csv.DictReader(handle))
    grouped: defaultdict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    keys = ("record_index", "process_name", "source_model", "optimizer_model", "strategy")
    for row in decisions:
        item = consensus.get((row["source_model"], row["row_ref"]))
        if not item:
            continue
        grouped[tuple(row.get(k, "") for k in keys)].append({
            **row, "consensus": item["consensus_label"], "strength": item["consensus_strength"]
        })
    outputs: dict[str, list[dict[str, Any]]] = {"all": [], "unanimous": [], "majority": []}
    for group_key, rows in sorted(grouped.items()):
        base = dict(zip(keys, group_key))
        subsets = {
            "all": [r for r in rows if r["consensus"] in ("Unique", "Similar")],
            "unanimous": [r for r in rows if r["strength"] == "3/3 unanimous"],
            "majority": [r for r in rows if r["strength"] == "2/3 majority"],
        }
        for name, subset in subsets.items():
            outputs[name].append({**base, "subset": name, **classification_metrics(subset)})
    fields = list(next(iter(outputs["all"])).keys()) if outputs["all"] else list(keys)
    for name, rows in outputs.items():
        write_csv(OUT / f"optimizer_performance_{name}.csv", rows, fields)
    combined = outputs["all"] + outputs["unanimous"] + outputs["majority"]
    write_csv(OUT / "optimizer_by_consensus_strength.csv", combined, fields)


def write_reports(manifest: list[dict[str, Any]], aligned: list[dict[str, Any]], agreement: list[dict[str, Any]], consensus: list[dict[str, Any]], errors: list[str]) -> None:
    overall = next(row for row in agreement if row["source_model"] == "Overall")
    strata = {row["consensus_strength"]: row for row in consensus if row["source_model"] == "Overall"}
    status = "REPRODUCED WITH ROUNDING DIFFERENCE" if overall["fleiss_kappa"] == "0.186386" else "NOT REPRODUCED"
    report = f"""# Human Oracle reproduction report

## Result

- Public evaluator files parsed: {len(manifest)} (7 source suites x 3 evaluators).
- Aligned items: {overall['aligned_items']}.
- Unmatched or unresolved items: {overall['unresolved']}.
- Majority consensus: {overall['majority_unique']} Unique and {overall['majority_similar']} Similar.
- Raw three-way agreement: {overall['raw_three_way_agreement']}.
- Fleiss' kappa: {overall['fleiss_kappa']}.
- Historical kappa 0.1864 classification: **{status}**.
- Pairwise Cohen kappas: H1/H2 {overall['cohen_h1_h2']}; H1/H3 {overall['cohen_h1_h3']}; H2/H3 {overall['cohen_h2_h3']}.
- Gwet AC1: {overall['gwet_ac1']}. AC1 is supplementary and does not replace or soften the low Fleiss result.
- Unanimous items: {strata['3/3 unanimous']['count']} ({strata['3/3 unanimous']['percentage']}%).
- Two-of-three majority items: {strata['2/3 majority']['count']} ({strata['2/3 majority']['percentage']}%).

Alignment uses `(normalized source model, row_ref)` and independently requires identical TestCaseID, title, description, and objective signatures across all three exports. Row order is not used as the identity. The public JSON exports do not contain ScenarioID, confidence, or save timestamps, so those fields are reported as unavailable rather than inferred.

The majority label is a human consensus reference, not objective ground truth. The complete optimizer comparison is stratified into all, unanimous, and majority-only subsets. A false removal is a consensus-Unique item predicted Similar.

## Validation issues

""" + ("\n".join(f"- {error}" for error in errors) if errors else "- None.") + "\n"
    (OUT / "human_oracle_reproduction_report.md").write_text(report, encoding="utf-8")

    tool_hash = sha256(TOOL)
    audit = f"""# Human Oracle PySide6 tool audit

- Archived source: `test_results/human_oracle_pyside6.py`
- SHA-256: `{tool_hash}`
- Input: `calculation_db.coverage_db.json`, accepting either a JSON array or JSON Lines.
- Item extraction: unique and both sides of Similar pairs are normalized; duplicate `case_key` values are removed; records are sorted before `row_ref` values `R0001...` are assigned.
- `case_key`: MD5 over session, process, optimization type, model, scenario ID, test-case ID, title, description, and objective.
- Persistence: MongoDB `calculation_db.human_oracle_decisions`; updates use `row_ref` as the unique upsert key.
- Decisions: Unique, Similar, and Unclear.
- Additional fields: Similar To and 1-5 confidence are available in the interface. Save time is assigned during each bulk save.
- Evaluator identifier: the archived source hard-codes `reviewer_id=human_expert_1`; evaluator separation is therefore established by the separate public export directories, not by a configurable UI identity.

## Blinding and anchoring

The interface is not blinded. Its table and detail metadata visibly expose the model (`used_model`), optimization type, and original LLM label. Consequently, evaluator judgements could be anchored by model identity, mode, or the original classifier output. The manuscript must report this as a human-reference validity limitation and must not claim evaluator blinding.

## Identity limitation

Although `case_key` contains strong content and provenance fields, the database save/update key is `row_ref`. The public exports align successfully because the three archives share the same row references and identical content signatures; nevertheless, row references could change if the source dataset or sort order changed. The reproduction therefore validates content signatures in addition to `row_ref`.
"""
    (OUT / "human_oracle_tool_audit.md").write_text(audit, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, long_rows, errors = load_raw()
    aligned = align(long_rows, errors)
    agreement = agreement_rows(aligned)
    consensus = consensus_rows(aligned)
    write_csv(OUT / "evaluator_file_manifest.csv", manifest, list(manifest[0]))
    write_csv(OUT / "aligned_evaluator_decisions.csv", aligned, list(aligned[0]))
    write_csv(OUT / "agreement_statistics.csv", agreement, list(agreement[0]))
    write_csv(OUT / "consensus_stratification.csv", consensus, list(consensus[0]))
    optimizer_metrics(aligned)
    write_reports(manifest, aligned, agreement, consensus, errors)
    print(json.dumps({
        "files": len(manifest), "long_rows": len(long_rows), "aligned": len(aligned),
        "errors": len(errors), "overall": next(r for r in agreement if r["source_model"] == "Overall")
    }, indent=2))


if __name__ == "__main__":
    main()
