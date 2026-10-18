from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "15_final_audit"
EXPERIMENT = "reviewer_revision_2026_full_suite"
REQUIRED = {
    "run_config.json", "suite_manifest.json", "raw_output.json", "classified_pairs.csv",
    "retained_cases.json", "removed_cases.json", "metrics.json", "execution_log.txt",
    "database_record_ids.txt", "case_classifications.csv",
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    packages: dict[str, tuple[Path, dict[str, Any]]] = {}
    failures = []
    for base in (ROOT / "05_bulk_runs", ROOT / "06_parallel_runs"):
        for path in base.rglob("metrics.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("experiment_id") != EXPERIMENT:
                continue
            if "attempts" in path.parts:
                if data.get("status") == "FAILED":
                    failures.append({
                        "run_id": data.get("run_id"), "suite_id": data.get("suite_id"),
                        "model_key": data.get("model_key"), "mode": data.get("mode"),
                        "repeat": data.get("repeat"), "attempt_path": str(path.parent),
                        "runtime_seconds": data.get("runtime_seconds"), "error": data.get("error"),
                    })
                continue
            if data.get("status") == "COMPLETE":
                run_id = data["run_id"]
                if run_id in packages:
                    raise SystemExit(f"Duplicate filesystem run ID: {run_id}")
                packages[run_id] = (path.parent, data)

    client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=5000)
    db = client["stlc_database"]
    docs = list(db["test_case_optimizations"].find(
        {"optimization_results.revision_metadata.experiment_id": EXPERIMENT}
    ))
    docs_by_id: dict[str, dict[str, Any]] = {}
    for doc in docs:
        run_id = doc.get("process_title")
        if run_id in docs_by_id:
            raise SystemExit(f"Duplicate DB run ID: {run_id}")
        docs_by_id[run_id] = doc

    all_ids = sorted(set(packages) | set(docs_by_id))
    rows = []
    for run_id in all_ids:
        package = packages.get(run_id)
        doc = docs_by_id.get(run_id)
        path, metrics = package if package else (None, {})
        revision = (((doc or {}).get("optimization_results") or {}).get("revision_metadata") or {})
        present = set(p.name for p in path.iterdir() if p.is_file()) if path else set()
        missing = sorted(REQUIRED - present)
        file_db_id = (path / "database_record_ids.txt").read_text(encoding="utf-8").strip() if path and (path / "database_record_ids.txt").exists() else ""
        db_id = str(doc["_id"]) if doc else ""
        status = "VERIFIED"
        issues = []
        if not package:
            issues.append("missing filesystem package")
        if not doc:
            issues.append("missing DB record")
        if missing:
            issues.append("missing files: " + ", ".join(missing))
        if doc and file_db_id != db_id:
            issues.append("DB ID mismatch")
        if doc and metrics.get("configuration_hash") != revision.get("configuration_hash"):
            issues.append("configuration hash mismatch")
        if doc and metrics.get("comparison_prompt_template_sha256") != revision.get("comparison_prompt_template_sha256"):
            issues.append("prompt hash mismatch")
        if "SERIAL" in run_id.upper() or str(metrics.get("mode", "")).lower() == "serial":
            issues.append("prohibited Serial run")
        if issues:
            status = "MISMATCH"
        rows.append({
            "run_id": run_id, "suite": metrics.get("suite_id", revision.get("suite_id", "")),
            "model": metrics.get("model_key", revision.get("model_key", "")),
            "mode": metrics.get("mode", revision.get("mode", "")),
            "repeat": metrics.get("repeat", revision.get("repeat", "")),
            "db_id": db_id, "raw_path": str(path) if path else "",
            "config_hash": metrics.get("configuration_hash", ""),
            "prompt_hash": metrics.get("comparison_prompt_template_sha256", ""),
            "status": status, "issues": "; ".join(issues),
        })
    write_csv(OUT / "db_file_crosscheck.csv", rows)
    write_csv(OUT / "failed_attempts.csv", failures)

    cell_counts: dict[tuple[str, str, str], set[int]] = {}
    for _, metrics in packages.values():
        key = (metrics["suite_id"], metrics["model_key"], metrics["mode"])
        cell_counts.setdefault(key, set()).add(int(metrics["repeat"]))
    problems = []
    if len(packages) != 60:
        problems.append(f"filesystem successful runs={len(packages)}")
    if len(docs) != 60:
        problems.append(f"database successful runs={len(docs)}")
    if len(cell_counts) != 12:
        problems.append(f"design cells={len(cell_counts)}")
    for key, repeats in sorted(cell_counts.items()):
        if repeats != {1, 2, 3, 4, 5}:
            problems.append(f"{key} repeats={sorted(repeats)}")
    mismatches = [r for r in rows if r["status"] != "VERIFIED"]
    if mismatches:
        problems.append(f"crosscheck mismatches={len(mismatches)}")
    summary = [
        "# Database/file crosscheck summary", "",
        f"- Successful filesystem packages: {len(packages)}",
        f"- Experiment-tagged database records: {len(docs)}",
        f"- Design cells: {len(cell_counts)}",
        f"- Failed attempts preserved separately: {len(failures)}",
        f"- Serial runs in the new experiment: {sum('SERIAL' in rid.upper() for rid in all_ids)}",
        f"- Crosscheck mismatches: {len(mismatches)}", "",
        "## Verdict", "", "PASS" if not problems else "FAIL: " + "; ".join(problems), "",
    ]
    (OUT / "db_file_crosscheck_report.md").write_text("\n".join(summary), encoding="utf-8")
    if problems:
        raise SystemExit("; ".join(problems))
    print("Crosscheck PASS: 60 filesystem packages and 60 database records")


if __name__ == "__main__":
    main()
