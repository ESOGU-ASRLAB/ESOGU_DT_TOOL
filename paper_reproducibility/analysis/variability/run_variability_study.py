from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import traceback
import types
from typing import Any
from urllib.request import urlopen


REVISION_ROOT = Path(r"C:\Users\matisse\Desktop\STLC-Manager\test_results\reviewer_revision_2026")
STUDY_ROOT = REVISION_ROOT / "03_variability_study"
STLC_ROOT = Path(r"C:\Users\matisse\Desktop\STLC-Manager")
BACKEND_ROOT = STLC_ROOT / "backend"
SERVER_EXE = Path(
    r"C:\Users\matisse\.cache\lm-studio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.55.0\llama-server.exe"
)
INPUTS = {
    "source_code": STLC_ROOT / "test_inputs" / "ProductDetection.cpp",
    "requirements": STLC_ROOT / "test_inputs" / "Functional_and_NonFunctional_Requirements.txt",
}
SOURCE_SESSIONS = {
    "source_code": "52083295-62a9-45f4-bd77-ad32cc2599c2",
    "requirements": "40b370ff-da15-46f2-ad96-692814082995",
}
MODELS = {
    "llama3.2-3b": {
        "selected_key": "llama3.2:3b",
        "alias": "llama-3.2-3b-instruct",
        "class": "lightweight",
        "model_path": Path(
            r"C:\Users\matisse\.cache\lm-studio\models\MaziyarPanahi\Llama-3.2-3B-Instruct-GGUF\Llama-3.2-3B-Instruct.Q4_K_S.gguf"
        ),
    },
    "gpt-oss-20b": {
        "selected_key": "openai/gpt-oss-20b",
        "alias": "openai/gpt-oss-20b",
        "class": "medium",
        "model_path": Path(
            r"C:\Users\matisse\.cache\lm-studio\models\lmstudio-community\gpt-oss-20b-GGUF\gpt-oss-20b-MXFP4.gguf"
        ),
    },
    "qwen3-coder-30b": {
        "selected_key": "qwen/qwen3-coder-30b",
        "alias": "qwen/qwen3-coder-30b",
        "class": "high-capacity",
        "model_path": Path(
            r"C:\Users\matisse\.cache\lm-studio\models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q3_K_L.gguf"
        ),
    },
}
FIXED_SEED = 20261017
CONTEXT_LENGTH = 8192
REVISION_TAG = "reviewer_revision_2026_variability"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_case_fingerprint(case: dict[str, Any]) -> str:
    fields = [
        str(case.get("ScenarioID", "")),
        str(case.get("TestCaseID", "")),
        str(case.get("Title", "")),
        str(case.get("Description", "")),
        str(case.get("Objective", "")),
    ]
    return hashlib.sha256("\x1f".join(fields).encode("utf-8")).hexdigest()


def artifact_identity(case: dict[str, Any]) -> str:
    return "::".join(
        [
            str(case.get("ArtifactType", "unknown")),
            str(case.get("SourceFile", "unknown")),
            str(case.get("ScenarioID", "missing")),
        ]
    )


def build_fixed_dataset(db: Any) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for artifact_type, session_id in SOURCE_SESSIONS.items():
        document = db["session_history"].find_one({"session_id": session_id})
        if document is None:
            raise RuntimeError(f"Source session not found: {session_id}")
        generation = (document.get("processes") or {}).get("test_case_generation") or {}
        results = (generation.get("output") or {}).get("test_case_results") or []
        source_file = INPUTS[artifact_type].name
        by_scenario: dict[str, dict[str, Any]] = {}
        for group in results:
            if not isinstance(group, dict) or group.get("status") != "success":
                continue
            scenario_id = str(group.get("scenario_id", ""))
            test_cases = group.get("test_cases") or []
            if scenario_id and test_cases and scenario_id not in by_scenario:
                case = dict(test_cases[0])
                case["ScenarioID"] = scenario_id
                case["ArtifactType"] = artifact_type
                case["SourceFile"] = source_file
                case["SourceSessionID"] = session_id
                case["ArtifactScopedScenarioID"] = artifact_identity(case)
                case["InputSHA256"] = sha256_file(INPUTS[artifact_type])
                by_scenario[scenario_id] = case
        if len(by_scenario) < 4:
            raise RuntimeError(f"Need at least four scenarios for {artifact_type}; found {len(by_scenario)}")
        for scenario_id in sorted(by_scenario)[:4]:
            selected.append(by_scenario[scenario_id])
    selected.sort(key=lambda c: (c["ArtifactType"], c["ScenarioID"], c.get("TestCaseID", "")))
    return selected


def write_dataset_outputs(dataset: list[dict[str, Any]]) -> None:
    (STUDY_ROOT / "fixed_dataset.json").write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    fields = [
        "dataset_row",
        "artifact_type",
        "source_file",
        "source_session_id",
        "input_sha256",
        "scenario_id",
        "artifact_scoped_scenario_id",
        "test_case_id",
        "title",
        "case_fingerprint",
    ]
    with (STUDY_ROOT / "dataset_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, case in enumerate(dataset, 1):
            writer.writerow(
                {
                    "dataset_row": index,
                    "artifact_type": case["ArtifactType"],
                    "source_file": case["SourceFile"],
                    "source_session_id": case["SourceSessionID"],
                    "input_sha256": case["InputSHA256"],
                    "scenario_id": case["ScenarioID"],
                    "artifact_scoped_scenario_id": case["ArtifactScopedScenarioID"],
                    "test_case_id": case.get("TestCaseID", ""),
                    "title": case.get("Title", ""),
                    "case_fingerprint": stable_case_fingerprint(case),
                }
            )


def start_server(model: dict[str, Any], log_path: Path) -> subprocess.Popen[str]:
    command = [
        str(SERVER_EXE),
        "--model",
        str(model["model_path"]),
        "--host",
        "127.0.0.1",
        "--port",
        "1234",
        "--ctx-size",
        str(CONTEXT_LENGTH),
        "--gpu-layers",
        "all",
        "--parallel",
        "1",
        "--seed",
        str(FIXED_SEED),
        "--alias",
        str(model["alias"]),
    ]
    log_handle = log_path.open("w", encoding="utf-8")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        command,
        cwd=str(STLC_ROOT),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creationflags,
    )
    process._revision_log_handle = log_handle  # type: ignore[attr-defined]
    deadline = time.time() + 300
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited with code {process.returncode}; see {log_path}")
        try:
            with urlopen("http://127.0.0.1:1234/v1/models", timeout=2) as response:
                if response.status == 200:
                    return process
        except Exception:
            time.sleep(1)
    raise TimeoutError(f"llama-server did not become ready; see {log_path}")


def stop_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    handle = getattr(process, "_revision_log_handle", None)
    if handle is not None:
        handle.close()


def map_results(dataset: list[dict[str, Any]], result_data: dict[str, Any]) -> list[dict[str, Any]]:
    input_by_fingerprint = {stable_case_fingerprint(case): case for case in dataset}
    retained = {
        stable_case_fingerprint(case)
        for case in (result_data.get("unique_test_cases") or [])
        if isinstance(case, dict)
    }
    removed = set()
    for item in result_data.get("similar_test_cases") or []:
        if not isinstance(item, dict):
            continue
        duplicate = item.get("DuplicateCase") or item.get("duplicate_case") or {}
        if isinstance(duplicate, dict):
            removed.add(stable_case_fingerprint(duplicate))
    rows = []
    for fingerprint, case in input_by_fingerprint.items():
        decision = "Unique" if fingerprint in retained else "Similar" if fingerprint in removed else "Unmapped"
        rows.append(
            {
                "case_fingerprint": fingerprint,
                "artifact_type": case["ArtifactType"],
                "source_file": case["SourceFile"],
                "scenario_id": case["ScenarioID"],
                "artifact_scoped_scenario_id": case["ArtifactScopedScenarioID"],
                "test_case_id": case.get("TestCaseID", ""),
                "title": case.get("Title", ""),
                "decision": decision,
            }
        )
    return rows


def calculate_metrics(dataset: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(dataset)
    unique = sum(row["decision"] == "Unique" for row in decisions)
    similar = sum(row["decision"] == "Similar" for row in decisions)
    unmapped = sum(row["decision"] == "Unmapped" for row in decisions)
    retained_rows = [row for row in decisions if row["decision"] == "Unique"]
    raw_before = {str(case.get("ScenarioID", "")) for case in dataset}
    raw_after = {row["scenario_id"] for row in retained_rows}
    corrected_before = {artifact_identity(case) for case in dataset}
    corrected_after = {row["artifact_scoped_scenario_id"] for row in retained_rows}
    trr = similar / total if total else None
    legacy_scp = len(raw_after) / len(raw_before) if raw_before else None
    corrected_scp = len(corrected_after) / len(corrected_before) if corrected_before else None
    denominator = None if trr is None else 1 - trr
    legacy_srg = legacy_scp / denominator if legacy_scp is not None and denominator else None
    corrected_srg = corrected_scp / denominator if corrected_scp is not None and denominator else None
    return {
        "total_input_cases": total,
        "unique_count": unique,
        "similar_count": similar,
        "unmapped_count": unmapped,
        "trr": trr,
        "raw_scenarios_before": len(raw_before),
        "raw_scenarios_after": len(raw_after),
        "legacy_raw_id_scp": legacy_scp,
        "legacy_srg": legacy_srg,
        "artifact_scoped_scenarios_before": len(corrected_before),
        "artifact_scoped_scenarios_after": len(corrected_after),
        "corrected_artifact_scoped_scp": corrected_scp,
        "corrected_srg": corrected_srg,
    }


async def run_one(
    service: Any,
    dataset: list[dict[str, Any]],
    model_name: str,
    model: dict[str, Any],
    mode: str,
    run_number: int,
) -> dict[str, Any]:
    run_id = f"{REVISION_TAG}_{model_name}_{mode}_run_{run_number:02d}"
    run_dir = STUDY_ROOT / "raw_runs" / model_name / mode / f"run_{run_number:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "experiment_id": REVISION_TAG,
        "run_id": run_id,
        "revision_tag": REVISION_TAG,
        "model_key": model["selected_key"],
        "model_alias": model["alias"],
        "model_class": model["class"],
        "model_path": str(model["model_path"]),
        "model_size_bytes": model["model_path"].stat().st_size,
        "mode": mode,
        "run_number": run_number,
        "fixed_seed": FIXED_SEED,
        "temperature": 0.1,
        "context_length": CONTEXT_LENGTH,
        "input_files": {key: str(path) for key, path in INPUTS.items()},
        "input_hashes": {key: sha256_file(path) for key, path in INPUTS.items()},
        "dataset_file": str(STUDY_ROOT / "fixed_dataset.json"),
        "dataset_sha256": sha256_file(STUDY_ROOT / "fixed_dataset.json"),
        "sample_size": len(dataset),
        "prompt_source": str(BACKEND_ROOT / "services" / "test_case_optimization_service.py"),
        "prompt_source_sha256": sha256_file(BACKEND_ROOT / "services" / "test_case_optimization_service.py"),
    }
    (run_dir / "run_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    with (run_dir / "input_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["artifact_type", "path", "sha256", "size_bytes"])
        for key, path in INPUTS.items():
            writer.writerow([key, str(path), sha256_file(path), path.stat().st_size])
    started = time.time()
    if mode == "serial":
        response = await service.run_smart_selection(
            dataset,
            custom_prompt=None,
            selected_model=model["selected_key"],
            api_key=None,
            process_id=run_id,
        )
    else:
        response = await service.run_bulk_smart_selection(
            dataset,
            custom_prompt=None,
            selected_model=model["selected_key"],
            api_key=None,
            process_id=run_id,
        )
    elapsed = time.time() - started
    raw_payload = {
        "config": config,
        "elapsed_seconds": elapsed,
        "response": response,
    }
    (run_dir / "raw_output.json").write_text(
        json.dumps(raw_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    if not response.get("success"):
        failure = {
            "experiment_id": REVISION_TAG,
            "run_id": run_id,
            "model": model_name,
            "mode": mode,
            "run_number": run_number,
            "status": "failed",
            "elapsed_seconds": elapsed,
            "error": response.get("message", "unknown failure"),
        }
        (run_dir / "metrics.json").write_text(json.dumps(failure, indent=2), encoding="utf-8")
        (run_dir / "execution_log.txt").write_text(failure["error"] + "\n", encoding="utf-8")
        return failure
    result_data = response.get("data") or {}
    decisions = map_results(dataset, result_data)
    with (run_dir / "classified_pairs.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)
    metrics = calculate_metrics(dataset, decisions)
    record = {
        "experiment_id": REVISION_TAG,
        "run_id": run_id,
        "model": model_name,
        "model_key": model["selected_key"],
        "mode": mode,
        "run_number": run_number,
        "status": "completed" if metrics["unmapped_count"] == 0 else "completed_with_unmapped_cases",
        "elapsed_seconds": elapsed,
        **metrics,
    }
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (run_dir / "execution_log.txt").write_text(
        f"{record['status']}\nelapsed_seconds={elapsed:.6f}\n", encoding="utf-8"
    )
    persistence_payload = dict(result_data)
    persistence_payload["optimization_type"] = mode
    persistence_payload["revision_metadata"] = {**config, **record}
    saved = service.save_optimization_results(run_id, persistence_payload, model["selected_key"])
    if not saved:
        record["status"] = "completed_file_only_db_save_failed"
    db_doc = service.db["test_case_optimizations"].find_one({"process_title": run_id}, {"_id": 1})
    record["database_record_id"] = str(db_doc["_id"]) if db_doc else "MISSING"
    (run_dir / "database_record_ids.txt").write_text(
        record["database_record_id"] + "\n", encoding="utf-8"
    )
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def write_aggregates(records: list[dict[str, Any]], decision_records: list[dict[str, Any]]) -> None:
    fields = sorted({key for record in records for key in record})
    with (STUDY_ROOT / "aggregated_results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    complete = [record for record in records if str(record.get("status", "")).startswith("completed")]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in complete:
        grouped.setdefault((record["model"], record["mode"]), []).append(record)
    stat_rows: list[dict[str, Any]] = []
    metric_names = [
        "unique_count",
        "similar_count",
        "trr",
        "legacy_raw_id_scp",
        "corrected_artifact_scoped_scp",
        "legacy_srg",
        "corrected_srg",
        "elapsed_seconds",
    ]
    for (model, mode), group in sorted(grouped.items()):
        for metric in metric_names:
            values = [float(row[metric]) for row in group if row.get(metric) is not None]
            if not values:
                continue
            mean = statistics.fmean(values)
            sd = statistics.stdev(values) if len(values) > 1 else 0.0
            stat_rows.append(
                {
                    "model": model,
                    "mode": mode,
                    "metric": metric,
                    "n": len(values),
                    "mean": mean,
                    "standard_deviation": sd,
                    "median": statistics.median(values),
                    "minimum": min(values),
                    "maximum": max(values),
                    "range": max(values) - min(values),
                    "coefficient_of_variation": sd / mean if mean else None,
                }
            )
    with (STUDY_ROOT / "variability_statistics.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(stat_rows[0]) if stat_rows else ["model", "mode"])
        writer.writeheader()
        writer.writerows(stat_rows)
    if decision_records:
        with (STUDY_ROOT / "decision_stability.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(decision_records[0]))
            writer.writeheader()
            writer.writerows(decision_records)


def calculate_decision_stability(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    complete = [record for record in records if str(record.get("status", "")).startswith("completed")]
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in complete:
        by_group.setdefault((record["model"], record["mode"]), []).append(record)
    rows: list[dict[str, Any]] = []
    for (model, mode), group in sorted(by_group.items()):
        decisions_by_case: dict[str, list[str]] = {}
        metadata: dict[str, dict[str, str]] = {}
        for record in group:
            path = STUDY_ROOT / "raw_runs" / model / mode / f"run_{int(record['run_number']):02d}" / "classified_pairs.csv"
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    fingerprint = row["case_fingerprint"]
                    decisions_by_case.setdefault(fingerprint, []).append(row["decision"])
                    metadata[fingerprint] = row
        for fingerprint, decisions in sorted(decisions_by_case.items()):
            counts = {label: decisions.count(label) for label in sorted(set(decisions))}
            majority = max(counts.values()) if counts else 0
            n = len(decisions)
            rows.append(
                {
                    "model": model,
                    "mode": mode,
                    "case_fingerprint": fingerprint,
                    "artifact_type": metadata[fingerprint]["artifact_type"],
                    "source_file": metadata[fingerprint]["source_file"],
                    "scenario_id": metadata[fingerprint]["scenario_id"],
                    "artifact_scoped_scenario_id": metadata[fingerprint]["artifact_scoped_scenario_id"],
                    "n_runs": n,
                    "unique_decisions": counts.get("Unique", 0),
                    "similar_decisions": counts.get("Similar", 0),
                    "unmapped_decisions": counts.get("Unmapped", 0),
                    "percent_agreement": majority / n if n else None,
                    "disagreement_rate": 1 - (majority / n) if n else None,
                    "instability_flag": int(len(counts) > 1),
                }
            )
    return rows


async def main_async(args: argparse.Namespace) -> int:
    os.environ["MONGO_URI"] = "mongodb://127.0.0.1:27017"
    os.environ["DATABASE_NAME"] = "stlc_database"
    os.environ["MODEL_API_BASE_URL"] = "http://127.0.0.1:1234"
    os.environ["MODEL_API_KEY"] = ""
    sys.path.insert(0, str(BACKEND_ROOT))
    # The production client imports the optional paid-provider SDK at module
    # import time even when a local model is selected.  The revision study is
    # local-only, so provide an inert import shim when that optional SDK is not
    # installed.  No Gemini code path is called by this script.
    try:
        import google.generativeai  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError:
        try:
            import google  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            google = types.ModuleType("google")
            google.__path__ = []  # type: ignore[attr-defined]
            sys.modules["google"] = google
        generativeai = types.ModuleType("google.generativeai")
        generativeai.configure = lambda **_: None  # type: ignore[attr-defined]
        generativeai.GenerativeModel = object  # type: ignore[attr-defined]
        sys.modules["google.generativeai"] = generativeai
        setattr(google, "generativeai", generativeai)
    # The dirty working tree contains an optional FastEmbed retrieval layer
    # that is not installed on this machine and was not part of the archived
    # serial experiment.  Inject a legacy-order compatibility module so the
    # application service compares against all retained candidates in their
    # original order, without downloading an embedding model.
    semantic_module = types.ModuleType("services.semantic_similarity_service")

    def legacy_rank_semantic_candidates(case: Any, candidates: Any, limit: Any = None) -> list[tuple[Any, float]]:
        del case, limit
        return [(candidate, 0.0) for candidate in candidates]

    semantic_module.rank_semantic_candidates = legacy_rank_semantic_candidates  # type: ignore[attr-defined]
    sys.modules["services.semantic_similarity_service"] = semantic_module
    from pymongo import MongoClient

    db = MongoClient(os.environ["MONGO_URI"])[os.environ["DATABASE_NAME"]]
    dataset = build_fixed_dataset(db)
    write_dataset_outputs(dataset)
    selected_models = args.models or list(MODELS)
    records: list[dict[str, Any]] = []
    aggregate_path = STUDY_ROOT / "aggregated_results.csv"
    if aggregate_path.exists():
        with aggregate_path.open("r", encoding="utf-8-sig", newline="") as handle:
            records.extend(csv.DictReader(handle))
    existing_run_ids = {str(record.get("run_id", "")) for record in records}
    for model_name in selected_models:
        model = MODELS[model_name]
        if not model["model_path"].exists():
            records.append(
                {
                    "experiment_id": REVISION_TAG,
                    "run_id": f"{REVISION_TAG}_{model_name}_model_load",
                    "model": model_name,
                    "status": "failed",
                    "error": f"Model file not found: {model['model_path']}",
                }
            )
            continue
        server_log = STUDY_ROOT / "raw_runs" / model_name / "llama_server.log"
        server_log.parent.mkdir(parents=True, exist_ok=True)
        process: subprocess.Popen[str] | None = None
        try:
            process = start_server(model, server_log)
            from services.test_case_optimization_service import TestCaseOptimizationService

            service = TestCaseOptimizationService()
            for mode in args.modes:
                for run_number in range(args.start_run, args.repeats + 1):
                    planned_run_id = f"{REVISION_TAG}_{model_name}_{mode}_run_{run_number:02d}"
                    if planned_run_id in existing_run_ids:
                        continue
                    try:
                        record = await run_one(service, dataset, model_name, model, mode, run_number)
                    except Exception as exc:
                        record = {
                            "experiment_id": REVISION_TAG,
                            "run_id": f"{REVISION_TAG}_{model_name}_{mode}_run_{run_number:02d}",
                            "model": model_name,
                            "model_key": model["selected_key"],
                            "mode": mode,
                            "run_number": run_number,
                            "status": "failed",
                            "error": f"{type(exc).__name__}: {exc}",
                            "traceback": traceback.format_exc(),
                        }
                        run_dir = STUDY_ROOT / "raw_runs" / model_name / mode / f"run_{run_number:02d}"
                        run_dir.mkdir(parents=True, exist_ok=True)
                        (run_dir / "metrics.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
                        (run_dir / "execution_log.txt").write_text(record["traceback"], encoding="utf-8")
                    records.append(record)
                    existing_run_ids.add(str(record.get("run_id", "")))
                    write_aggregates(records, calculate_decision_stability(records))
        except Exception as exc:
            records.append(
                {
                    "experiment_id": REVISION_TAG,
                    "run_id": f"{REVISION_TAG}_{model_name}_model_load",
                    "model": model_name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )
            write_aggregates(records, calculate_decision_stability(records))
        finally:
            if process is not None:
                stop_server(process)
    write_aggregates(records, calculate_decision_stability(records))
    return 0 if all(str(record.get("status", "")).startswith("completed") for record in records) else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", choices=list(MODELS))
    parser.add_argument("--modes", nargs="+", default=["serial", "bulk"], choices=["serial", "bulk"])
    parser.add_argument("--start-run", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(parse_args())))
