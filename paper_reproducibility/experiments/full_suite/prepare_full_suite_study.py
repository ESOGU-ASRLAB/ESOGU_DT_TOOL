from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from pymongo import MongoClient


STLC = Path(r"C:\Users\matisse\Desktop\STLC-Manager")
MANUSCRIPT = Path(r"C:\Users\matisse\Desktop\applsci-4556799")
ROOT = STLC / "test_results" / "reviewer_revision_2026" / "final_revision"
PREVIOUS = STLC / "test_results" / "reviewer_revision_2026"

INPUTS = {
    "source_code": STLC / "test_inputs" / "ProductDetection.cpp",
    "requirements": STLC / "test_inputs" / "Functional_and_NonFunctional_Requirements.txt",
}
SESSIONS = {
    "source_code": "52083295-62a9-45f4-bd77-ad32cc2599c2",
    "requirements": "40b370ff-da15-46f2-ad96-692814082995",
}
MODELS = {
    "llama32": {
        "display": "Llama 3.2 3B",
        "api_model": "llama3.2:3b",
        "alias": "llama-3.2-3b-instruct",
        "quantization": "Q4_K_S",
        "parameter_class": "3B",
        "path": Path(r"C:\Users\matisse\.cache\lm-studio\models\MaziyarPanahi\Llama-3.2-3B-Instruct-GGUF\Llama-3.2-3B-Instruct.Q4_K_S.gguf"),
    },
    "gptoss20": {
        "display": "GPT-OSS 20B",
        "api_model": "openai/gpt-oss-20b",
        "alias": "openai/gpt-oss-20b",
        "quantization": "MXFP4",
        "parameter_class": "20B",
        "path": Path(r"C:\Users\matisse\.cache\lm-studio\models\lmstudio-community\gpt-oss-20b-GGUF\gpt-oss-20b-MXFP4.gguf"),
    },
    "qwen30": {
        "display": "Qwen3-Coder 30B A3B",
        "api_model": "qwen/qwen3-coder-30b",
        "alias": "qwen/qwen3-coder-30b",
        "quantization": "Q3_K_L",
        "parameter_class": "30B-A3B",
        "path": Path(r"C:\Users\matisse\.cache\lm-studio\models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q3_K_L.gguf"),
    },
}
SERVER = Path(r"C:\Users\matisse\.cache\lm-studio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.55.0\llama-server.exe")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_text(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        return (result.stdout or result.stderr).strip()
    except Exception as exc:
        return f"UNAVAILABLE: {exc}"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def input_manifest(db: Any) -> dict[str, str]:
    output = ROOT / "00_inputs"
    output.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    lines = ["# Canonical input artifact manifest", ""]
    for artifact_type, path in INPUTS.items():
        if not path.exists() or not os.access(path, os.R_OK):
            raise FileNotFoundError(path)
        digest = sha256(path)
        hashes[artifact_type] = digest
        duplicates = []
        for candidate in STLC.rglob(path.name):
            if candidate.is_file():
                duplicates.append((candidate, sha256(candidate)))
        session = db["session_history"].find_one({"session_id": SESSIONS[artifact_type]})
        serialized = json.dumps(session, ensure_ascii=False, default=str) if session else ""
        historical_hash_evidence = "EXPLICIT HASH MATCH" if digest.lower() in serialized.lower() else "NOT ESTABLISHED; session provides content records but no matching explicit source hash"
        lines.extend([
            f"## {path.name}", "",
            f"- Artifact type: `{artifact_type}`",
            f"- Authoritative path: `{path}`",
            f"- Readable: YES",
            f"- Size: {path.stat().st_size} bytes",
            f"- Last modified: {datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()}",
            f"- SHA-256: `{digest}`",
            f"- Historical exact-instance equivalence: {historical_hash_evidence}",
            f"- Same-name copies found: {len(duplicates)}", "",
        ])
        for candidate, candidate_hash in duplicates:
            relation = "HASH MATCH" if candidate_hash == digest else "HASH MISMATCH"
            lines.append(f"  - `{candidate}` - `{candidate_hash}` - {relation}")
        lines.append("")
    (output / "input_artifact_manifest.md").write_text("\n".join(lines), encoding="utf-8")
    return hashes


def extract_suites(db: Any, input_hashes: dict[str, str]) -> list[dict[str, Any]]:
    directory = ROOT / "04_full_suite_design" / "suites"
    directory.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for artifact_type, session_id in SESSIONS.items():
        document = db["session_history"].find_one({"session_id": session_id})
        if not document:
            raise RuntimeError(f"Source session missing: {session_id}")
        generation = ((document.get("processes") or {}).get("test_case_generation") or {})
        output = generation.get("output") or {}
        groups = output.get("test_case_results") or []
        cases: list[dict[str, Any]] = []
        scenario_ids: list[str] = []
        for group in groups:
            if not isinstance(group, dict) or group.get("status") != "success":
                continue
            scenario_id = str(group.get("scenario_id", ""))
            scenario_ids.append(scenario_id)
            for ordinal, raw_case in enumerate(group.get("test_cases") or [], 1):
                case = dict(raw_case)
                case["ScenarioID"] = scenario_id
                case["ArtifactType"] = artifact_type
                case["SourceFile"] = INPUTS[artifact_type].name
                case["SourceSessionID"] = session_id
                case["SourceInputSHA256"] = input_hashes[artifact_type]
                case["ArtifactScopedScenarioID"] = f"{artifact_type}::{INPUTS[artifact_type].name}::{scenario_id}"
                case["CaseUID"] = f"{artifact_type}::{INPUTS[artifact_type].name}::{scenario_id}::{case.get('TestCaseID','')}::{ordinal:02d}"
                cases.append(case)
        if not cases:
            raise RuntimeError(f"No full-suite cases in {session_id}")
        suite_id = "FULLSRC" if artifact_type == "source_code" else "FULLREQ"
        payload = {
            "suite_id": suite_id,
            "artifact_type": artifact_type,
            "source_artifact": str(INPUTS[artifact_type]),
            "source_artifact_hash": input_hashes[artifact_type],
            "source_session_id": session_id,
            "generation_model": generation.get("selected_model") or output.get("used_model") or (output.get("metadata") or {}).get("model_used") or "NOT RECORDED",
            "generation_timestamp": output.get("timestamp") or (output.get("metadata") or {}).get("generated_at") or document.get("updated_at") or document.get("created_at") or "NOT RECORDED",
            "database_record_id": str(document.get("_id")),
            "scenario_count": len(set(scenario_ids)),
            "test_case_count": len(cases),
            "cases": cases,
        }
        payload["suite_content_hash"] = json_hash(cases)
        path = directory / f"{suite_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        manifest.append({key: payload[key] for key in (
            "suite_id", "artifact_type", "source_artifact", "source_artifact_hash", "source_session_id",
            "generation_model", "generation_timestamp", "database_record_id", "scenario_count", "test_case_count", "suite_content_hash"
        )})
    write_csv(ROOT / "04_full_suite_design" / "suite_manifest.csv", manifest, list(manifest[0]))
    return manifest


def model_manifest() -> None:
    rows = []
    for key, model in MODELS.items():
        path: Path = model["path"]
        rows.append({
            "model_key": key, "display_name": model["display"], "api_model": model["api_model"],
            "model_alias": model["alias"], "local_path": str(path), "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else "",
            "sha256": "DEFERRED; computed once before execution and recorded in run configuration",
            "quantization": model["quantization"], "parameter_class": model["parameter_class"],
            "backend": str(SERVER), "context_length_per_request": 8192,
        })
    write_csv(ROOT / "04_full_suite_design" / "model_manifest.csv", rows, list(rows[0]))


def environment_report() -> None:
    out = ROOT / "01_environment"
    out.mkdir(parents=True, exist_ok=True)
    try:
        import psutil
        ram = psutil.virtual_memory().total
        cpu = platform.processor() or run_text(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"])
    except Exception:
        ram, cpu = "UNAVAILABLE", platform.processor()
    nvidia = run_text(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    cuda = run_text(["nvidia-smi"])
    commit = run_text(["git", "-C", str(STLC), "rev-parse", "HEAD"])
    docker = run_text(["docker", "version", "--format", "{{.Client.Version}} / {{.Server.Version}}"])
    server_version = run_text([str(SERVER), "--version"])
    content = f"""# Machine and runtime environment

- Recorded: {datetime.now().astimezone().isoformat()}
- Hostname: {socket.gethostname()}
- OS: {platform.platform()}
- CPU: {cpu}
- Logical processors: {os.cpu_count()}
- RAM bytes: {ram}
- GPU, VRAM, driver: {nvidia}
- CUDA information: see `nvidia-smi` summary below.
- Python: {platform.python_version()} ({platform.python_implementation()})
- llama.cpp backend: `{SERVER}`
- llama.cpp version: {server_version}
- LM Studio model store: `C:/Users/matisse/.cache/lm-studio/models`
- Docker client/server: {docker}
- STLC Manager Git commit: `{commit}`
- MongoDB: local `stlc_database` on `127.0.0.1:27017`

## NVIDIA summary

```text
{cuda}
```

No credentials, API keys, or passwords are included in this report.
"""
    (out / "machine_environment.md").write_text(content, encoding="utf-8")


def project_inventory() -> None:
    files = {
        "Backend": STLC / "backend",
        "Frontend": STLC / "frontend",
        "Model client": STLC / "backend" / "utils" / "model_client.py",
        "Optimization service": STLC / "backend" / "services" / "test_case_optimization_service.py",
        "Historical parallel service": STLC / "backend" / "services" / "parallel_optimization_service.py",
        "Persistence": STLC / "backend" / "core" / "database.py",
        "Human Oracle tool": ROOT / "03_human_oracle" / "public_archive" / "test_results" / "human_oracle_pyside6.py",
        "Manuscript": MANUSCRIPT / "applsci-4556799-revised.tex",
        "Bibliography": MANUSCRIPT / "applsci-4556799-revised.bib",
    }
    lines = ["# Project inventory", ""]
    for label, path in files.items():
        lines.append(f"- {label}: `{path}` - {'PRESENT' if path.exists() else 'MISSING'}")
    lines.extend([
        "", "## Parallel implementation finding", "",
        "The application router restricts the historical `parallel` mode to Gemini models and the implementation invokes the provider-specific Gemini Batch API. It is therefore not reused or relabelled as a local equivalent. The new experiment uses a separately documented Controlled Local Parallel adapter with complete deterministic pair generation and local llama.cpp inference.",
        "", "## Reviewer document", "",
        "The expected latest reviewer-comments DOCX was not found in `C:/Users/matisse/Downloads` during this audit. Reviewer requirements are therefore derived from the supplied revision brief until the authoritative DOCX is restored.",
    ])
    (ROOT / "01_environment" / "project_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_historical_audit() -> None:
    out = ROOT / "02_historical_audit"
    out.mkdir(parents=True, exist_ok=True)
    mapping = {
        PREVIOUS / "01_database_validation" / "manuscript_reported_results.csv": out / "manuscript_reported_results.csv",
        PREVIOUS / "01_database_validation" / "database_historical_results.csv": out / "database_historical_results.csv",
        PREVIOUS / "01_database_validation" / "historical_consistency_report.md": out / "historical_consistency_report.md",
    }
    provenance = ["# Historical audit provenance", ""]
    for source, destination in mapping.items():
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copy2(source, destination)
        provenance.append(f"- `{destination.name}` copied without modification from `{source}`; SHA-256 `{sha256(destination)}`.")
    provenance.append("\nThe previous audit programmatically verified 140 Table 3 values against the frozen database export. Copying these results into the final-revision tree preserves, rather than rewrites, the historical audit evidence.\n")
    (out / "audit_provenance.md").write_text("\n".join(provenance), encoding="utf-8")


def main() -> None:
    client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=5000)
    db = client["stlc_database"]
    db.command("ping")
    hashes = input_manifest(db)
    suites = extract_suites(db, hashes)
    model_manifest()
    environment_report()
    project_inventory()
    copy_historical_audit()
    print(json.dumps({"input_hashes": hashes, "suites": suites}, indent=2, default=str))


if __name__ == "__main__":
    main()
