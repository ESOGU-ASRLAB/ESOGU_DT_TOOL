from __future__ import annotations

import csv
from pathlib import Path

from bson import ObjectId
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "test_results" / "reviewer_revision_2026"
SOURCE = OUT / "12_final_audit" / "db_file_crosscheck.csv"


with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.DictReader(handle))

collection = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=5000)["stlc_database"]["test_case_optimizations"]
for row in rows:
    document = collection.find_one({"_id": ObjectId(row["db_record_id"])})
    row["db_lookup_status"] = "FOUND" if document else "MISSING"
    row["db_process_title_match"] = "YES" if document and document.get("process_title") == row["run_id"] else "NO"
    metadata = (document or {}).get("optimization_results", {}).get("revision_metadata", {})
    row["db_revision_tag_match"] = "YES" if metadata.get("experiment_id") == row["experiment_id"] else "NO"
    if not document or row["db_process_title_match"] != "YES" or row["db_revision_tag_match"] != "YES":
        row["status"] = "INCOMPLETE"

fields = list(rows[0])
with SOURCE.open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

found = sum(r["db_lookup_status"] == "FOUND" for r in rows)
complete = sum(r["status"] == "COMPLETE" for r in rows)
print(f"DB records found: {found}/{len(rows)}; fully cross-checked: {complete}/{len(rows)}")
