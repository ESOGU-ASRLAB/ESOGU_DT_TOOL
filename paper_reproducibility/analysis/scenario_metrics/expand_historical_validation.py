from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "test_results" / "reviewer_revision_2026" / "01_database_validation"
ARCHIVE = ROOT / "test_results" / "stlc_test_results.json"

sources = [
    ("LLaMa3.2-3B", 169), ("Gemini2.5-Pro", 152), ("Gemini2.5-Flash", 139),
    ("GPT-OSS-20B", 137), ("LLaMa3.3-70B", 177), ("Qwen3-Coder-30B", 177),
    ("Codestral-22B", 123),
]
optimizers = [
    ("LLaMa3.2-3B", "llama3.2:3b"),
    ("GPT-OSS-20B", "openai/gpt-oss-20b"),
    ("LLaMa3.3-70B", "meta/llama-3.3-70b"),
    ("Qwen3-Coder-30B", "qwen/qwen3-coder-30b"),
    ("Codestral-22B", "mistralai/codestral-22b-v0.1"),
]
matrix = [
    [(155,14,12633),(104,65,8132),(105,64,8775),(79,90,6508),(96,73,7777)],
    [(149,3,11427),(85,67,5252),(113,39,7722),(88,64,6817),(111,41,8113)],
    [(138,1,9566),(92,47,6526),(115,24,7935),(81,58,5691),(108,31,7252)],
    [(130,7,8476),(80,57,4806),(98,39,5836),(66,71,4563),(88,49,6100)],
    [(177,0,15576),(118,59,8397),(137,40,11500),(105,72,7090),(123,54,9893)],
    [(172,5,15326),(73,104,4641),(89,88,6071),(56,121,3015),(79,98,5222)],
    [(122,1,7476),(82,41,4418),(95,28,5908),(69,54,3912),(86,37,4738)],
]

archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
records = []
for doc in archive:
    process = doc.get("processes", {}).get("test_case_optimization")
    if not process:
        continue
    output = process.get("output", {})
    records.append({
        "session_id": doc.get("session_id"), "timestamp": process.get("timestamp", "NOT RECORDED"),
        "model": process.get("used_model"), "mode": output.get("optimization_type") or "serial",
        "unique": len(output.get("unique_test_cases", [])),
        "similar": len(output.get("similar_test_cases", [])),
        "comparisons": len(output.get("comparison_logs", [])),
    })

reported, verified = [], []
for i, (source, total) in enumerate(sources):
    for j, (optimizer, alias) in enumerate(optimizers):
        unique, similar, comparisons = matrix[i][j]
        candidates = [r for r in records if r["mode"] == "serial" and r["model"] == alias and r["unique"] == unique and r["similar"] == similar and r["comparisons"] == comparisons]
        match = candidates[0] if len(candidates) == 1 else None
        for metric, value in [("total", total), ("unique", unique), ("similar", similar), ("comparisons", comparisons)]:
            reported.append({
                "section": "Serial optimization", "table": "Table 3", "metric": metric,
                "model": optimizer, "mode": "Serial", "source_artifact": source,
                "manuscript_value": value, "manuscript_location": f"Table 3 cell {source} x {optimizer}",
            })
            db_value = total if metric == "total" and match else (match.get(metric) if match else "NOT MAPPED")
            verified.append({
                "manuscript_metric": metric, "manuscript_value": value, "database_value": db_value,
                "database_record_run_id": match["session_id"] if match else "NOT MAPPED",
                "model": optimizer, "mode": "Serial", "source_artifact": source,
                "timestamp": match["timestamp"] if match else "NOT RECORDED",
                "project_identifier": "historical stlc_test_results.json",
                "status": "VERIFIED" if match and str(db_value) == str(value) else "UNRESOLVED",
                "match_mismatch": "MATCH" if match and str(db_value) == str(value) else "NO UNIQUE RECORD MATCH",
            })

extra = [
    ("Human reference", "Table 15", "items", "all", "n/a", "seven suites", 1074, "Table 15"),
    ("Human reference", "Table 15", "reported Fleiss kappa", "all", "n/a", "seven suites", 0.1864, "Table 15; historical-only"),
    ("Scenario metrics", "Table 10", "legacy raw-ID mean SCP percent", "core serial", "Serial", "historical archive", 98.40, "Table 10"),
    ("Scenario metrics", "Table 14", "legacy mean SRG", "core serial", "Serial", "historical archive", 1.5362, "Table 14"),
    ("Variability", "Table 9", "completed revision runs", "three local models", "Serial/Bulk", "two canonical artifacts", 30, "Table 9"),
]
for section, table, metric, model, mode, artifact, value, location in extra:
    reported.append({"section":section,"table":table,"metric":metric,"model":model,"mode":mode,"source_artifact":artifact,"manuscript_value":value,"manuscript_location":location})

def write(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

write(OUT / "manuscript_reported_results.csv", reported)
write(OUT / "database_historical_results.csv", verified)
print(f"Wrote {len(reported)} manuscript rows and {len(verified)} database comparisons; verified={sum(r['status']=='VERIFIED' for r in verified)}")
