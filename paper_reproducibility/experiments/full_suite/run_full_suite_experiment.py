from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import traceback
import types
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pymongo import MongoClient


STLC = Path(r"C:\Users\matisse\Desktop\STLC-Manager")
BACKEND = STLC / "backend"
ROOT = STLC / "test_results" / "reviewer_revision_2026" / "final_revision"
SUITE_DIR = ROOT / "04_full_suite_design" / "suites"
SERVER = Path(r"C:\Users\matisse\.cache\lm-studio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.55.0\llama-server.exe")
SERVER_URL = "http://127.0.0.1:1234"
EXPERIMENT_ID = "reviewer_revision_2026_full_suite"
BASE_SEED = 20261017
TEMPERATURE = 0.1
TOP_P = 0.95
TOP_K = 40
SERVER_CONTEXT = 32768
SERVER_PARALLEL = 4
PER_REQUEST_CONTEXT = 8192
BULK_BATCH_SIZE = 2
PAIR_BATCH_MAX = 8
PAIR_BATCH_CHAR_MAX = 12000
MAX_RETRIES = 4

MODELS = {
    "llama32": {
        "display": "Llama 3.2 3B", "api_model": "llama3.2:3b", "alias": "llama-3.2-3b-instruct",
        "path": Path(r"C:\Users\matisse\.cache\lm-studio\models\MaziyarPanahi\Llama-3.2-3B-Instruct-GGUF\Llama-3.2-3B-Instruct.Q4_K_S.gguf"),
        "quantization": "Q4_K_S", "parameter_class": "3B", "max_output_tokens": 256,
    },
    "gptoss20": {
        "display": "GPT-OSS 20B", "api_model": "openai/gpt-oss-20b", "alias": "openai/gpt-oss-20b",
        "path": Path(r"C:\Users\matisse\.cache\lm-studio\models\lmstudio-community\gpt-oss-20b-GGUF\gpt-oss-20b-MXFP4.gguf"),
        "quantization": "MXFP4", "parameter_class": "20B", "max_output_tokens": 1024,
    },
    "qwen30": {
        "display": "Qwen3-Coder 30B A3B", "api_model": "qwen/qwen3-coder-30b", "alias": "qwen/qwen3-coder-30b",
        "path": Path(r"C:\Users\matisse\.cache\lm-studio\models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q3_K_L.gguf"),
        "quantization": "Q3_K_L", "parameter_class": "30B-A3B", "max_output_tokens": 1024,
    },
}

SUITES = {
    "FULLSRC": {"folder": "product_detection", "path": SUITE_DIR / "FULLSRC.json"},
    "FULLREQ": {"folder": "requirements", "path": SUITE_DIR / "FULLREQ.json"},
}

SYSTEM_PROMPT = "You perform pre-execution semantic redundancy analysis of software test cases. Follow the requested JSON schema exactly and return no prose."
SEMANTIC_CRITERIA = """Two test cases are the same only when their titles are the same or substantially similar, their descriptions and/or objectives are very similar, and they serve essentially the same testing purpose for the same or a closely related scenario. Importance order: Description, Objective, Title. Otherwise they are different."""
BULK_TEMPLATE = """Analyze one fixed batch of test cases using these criteria:\n{criteria}\nReturn JSON with unique_indices and duplicate_groups. Indices are the supplied global indices. Every input index must appear exactly once either as a retained unique/representative or as a duplicate. Schema: {{\"unique_indices\":[0],\"duplicate_groups\":[{{\"representative_index\":0,\"duplicate_indices\":[1]}}]}}.\nTEST_CASES:\n{cases}"""
PAIR_TEMPLATE = """Apply these criteria independently to every explicit unordered pair:\n{criteria}\nReturn one decision for every pair_id. Schema: {{\"decisions\":[{{\"pair_id\":\"P000001\",\"is_same\":false}}]}}. Do not omit, add, or reorder pair IDs. Return exactly one compact JSON object, with no explanation or reasoning text.\nPAIRS:\n{pairs}"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json_hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode()).hexdigest()


def load_suite(suite_id: str) -> dict[str, Any]:
    payload = json.loads(SUITES[suite_id]["path"].read_text(encoding="utf-8"))
    if payload["test_case_count"] != len(payload["cases"]):
        raise RuntimeError(f"Suite count mismatch: {suite_id}")
    if stable_json_hash(payload["cases"]) != payload["suite_content_hash"]:
        raise RuntimeError(f"Suite hash mismatch: {suite_id}")
    return payload


def compact_case(index: int, case: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": index, "title": case.get("Title", ""), "description": case.get("Description", ""),
        "objective": case.get("Objective", ""),
    }


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object in response")
    return json.loads(cleaned[start : end + 1])


def api_call(model: dict[str, Any], prompt: str, seed: int, max_tokens: int, schema: dict[str, Any]) -> dict[str, Any]:
    body = {
        "model": model["alias"],
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        "temperature": TEMPERATURE, "top_p": TOP_P, "top_k": TOP_K, "seed": seed,
        "reasoning_effort": "low", "chat_template_kwargs": {"enable_thinking": False},
        "max_tokens": max_tokens, "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": "semantic_decisions", "strict": True, "schema": schema}},
    }
    request = Request(
        SERVER_URL + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    started = time.time()
    try:
        with urlopen(request, timeout=900) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:2000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Local llama.cpp request failed: {exc}") from exc
    content = payload["choices"][0]["message"]["content"]
    return {
        "seed": seed, "elapsed_seconds": time.time() - started, "request_chars": len(prompt),
        "raw_content": content, "usage": payload.get("usage", {}), "finish_reason": payload["choices"][0].get("finish_reason"),
    }


def bulk_response_schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "unique_indices": {"type": "array", "items": {"type": "integer"}},
            "duplicate_groups": {
                "type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "representative_index": {"type": "integer"},
                        "duplicate_indices": {"type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["representative_index", "duplicate_indices"],
                },
            },
        },
        "required": ["unique_indices", "duplicate_groups"],
    }


def pair_response_schema(pair_ids: list[str]) -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "decisions": {
                "type": "array", "minItems": len(pair_ids), "maxItems": len(pair_ids),
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"pair_id": {"type": "string", "enum": pair_ids}, "is_same": {"type": "boolean"}},
                    "required": ["pair_id", "is_same"],
                },
            }
        },
        "required": ["decisions"],
    }


def start_server(model: dict[str, Any], log_path: Path) -> subprocess.Popen[str]:
    if not SERVER.exists() or not model["path"].exists():
        raise FileNotFoundError(model["path"] if not model["path"].exists() else SERVER)
    command = [
        str(SERVER), "--model", str(model["path"]), "--host", "127.0.0.1", "--port", "1234",
        "--ctx-size", str(SERVER_CONTEXT), "--gpu-layers", "all", "--parallel", str(SERVER_PARALLEL),
        "--seed", str(BASE_SEED), "--alias", model["alias"],
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("a", encoding="utf-8")
    handle.write(f"\nSTART {datetime.now().astimezone().isoformat()}\nCOMMAND {json.dumps(command)}\n")
    handle.flush()
    process = subprocess.Popen(
        command, cwd=str(STLC), stdout=handle, stderr=subprocess.STDOUT, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    process._revision_log_handle = handle  # type: ignore[attr-defined]
    deadline = time.time() + 900
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited with {process.returncode}; see {log_path}")
        try:
            with urlopen(SERVER_URL + "/v1/models", timeout=3) as response:
                if response.status == 200:
                    return process
        except Exception:
            time.sleep(2)
    raise TimeoutError(f"Model server did not become ready: {model['display']}")


def stop_server(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
    handle = getattr(process, "_revision_log_handle", None)
    if handle:
        handle.close()


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        a, b = self.find(left), self.find(right)
        if a == b:
            return
        if a < b:
            self.parent[b] = a
        else:
            self.parent[a] = b


async def run_bulk(cases: list[dict[str, Any]], model: dict[str, Any], base_seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], UnionFind]:
    uf = UnionFind(len(cases))
    pair_rows: list[dict[str, Any]] = []
    raw: list[dict[str, Any]] = []
    call_index = 0
    for batch_number, start in enumerate(range(0, len(cases), BULK_BATCH_SIZE), 1):
        indices = list(range(start, min(start + BULK_BATCH_SIZE, len(cases))))
        prompt_cases = []
        for local_index, global_index in enumerate(indices):
            item = compact_case(local_index, cases[global_index])
            prompt_cases.append(item)
        prompt = BULK_TEMPLATE.format(criteria=SEMANTIC_CRITERIA, cases=json.dumps(prompt_cases, ensure_ascii=False))
        parsed = None
        errors = []
        for attempt in range(1, MAX_RETRIES + 1):
            call_index += 1
            response = await asyncio.to_thread(api_call, model, prompt, base_seed + call_index, model["max_output_tokens"], bulk_response_schema())
            response.update({"batch_number": batch_number, "attempt": attempt, "kind": "bulk"})
            raw.append(response)
            try:
                candidate = extract_json(response["raw_content"])
                unique = [int(v) for v in candidate.get("unique_indices", [])]
                groups = candidate.get("duplicate_groups", [])
                covered = set(unique)
                for group in groups:
                    covered.add(int(group["representative_index"]))
                    covered.update(int(v) for v in group.get("duplicate_indices", []))
                expected_local = set(range(len(indices)))
                if covered != expected_local:
                    raise ValueError(f"Coverage mismatch expected={sorted(expected_local)} got={sorted(covered)}")
                if any(v not in expected_local for v in covered):
                    raise ValueError("Out-of-batch index")
                parsed = candidate
                break
            except Exception as exc:
                errors.append(str(exc))
        if parsed is None:
            raise RuntimeError(f"Bulk batch {batch_number} failed validation: {errors}")
        for group in parsed.get("duplicate_groups", []):
            representative = indices[int(group["representative_index"])]
            for duplicate in group.get("duplicate_indices", []):
                uf.union(representative, indices[int(duplicate)])
        component = {i: uf.find(i) for i in indices}
        for pos, left in enumerate(indices):
            for right in indices[pos + 1 :]:
                pair_rows.append({
                    "pair_id": f"B{batch_number:02d}_{left:03d}_{right:03d}",
                    "case_a_index": left, "case_b_index": right,
                    "case_a_uid": cases[left]["CaseUID"], "case_b_uid": cases[right]["CaseUID"],
                    "is_same": component[left] == component[right], "decision_origin": "bulk_group_inference",
                    "batch_id": batch_number,
                })
    return pair_rows, raw, uf


def all_pairs(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    sequence = 0
    for left in range(len(cases)):
        for right in range(left + 1, len(cases)):
            sequence += 1
            pairs.append({
                "pair_id": f"P{sequence:06d}", "case_a_index": left, "case_b_index": right,
                "case_a_uid": cases[left]["CaseUID"], "case_b_uid": cases[right]["CaseUID"],
                "case_a": compact_case(left, cases[left]), "case_b": compact_case(right, cases[right]),
            })
    return pairs


def pair_batches(pairs: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for pair in pairs:
        compact = {"pair_id": pair["pair_id"], "case_a": pair["case_a"], "case_b": pair["case_b"]}
        size = len(json.dumps(compact, ensure_ascii=False))
        if current and (len(current) >= PAIR_BATCH_MAX or current_chars + size > PAIR_BATCH_CHAR_MAX):
            batches.append(current)
            current, current_chars = [], 0
        current.append(pair)
        current_chars += size
    if current:
        batches.append(current)
    return batches


async def run_pair_batch(batch_number: int, batch: list[dict[str, Any]], model: dict[str, Any], seed: int, semaphore: asyncio.Semaphore) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    requested = {pair["pair_id"]: pair for pair in batch}
    pending = dict(requested)
    rows: dict[str, dict[str, Any]] = {}
    raw: list[dict[str, Any]] = []
    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            compact = [{"pair_id": p["pair_id"], "case_a": p["case_a"], "case_b": p["case_b"]} for p in pending.values()]
            prompt = PAIR_TEMPLATE.format(criteria=SEMANTIC_CRITERIA, pairs=json.dumps(compact, ensure_ascii=False))
            response = await asyncio.to_thread(api_call, model, prompt, seed + attempt - 1, model["max_output_tokens"], pair_response_schema(list(pending)))
            response.update({"batch_number": batch_number, "attempt": attempt, "kind": "parallel_pairs", "requested_pair_ids": list(pending)})
            raw.append(response)
            try:
                parsed = extract_json(response["raw_content"])
                for decision in parsed.get("decisions", []):
                    pair_id = str(decision.get("pair_id", ""))
                    if pair_id not in pending or not isinstance(decision.get("is_same"), bool):
                        continue
                    pair = requested[pair_id]
                    rows[pair_id] = {
                        "pair_id": pair_id, "case_a_index": pair["case_a_index"], "case_b_index": pair["case_b_index"],
                        "case_a_uid": pair["case_a_uid"], "case_b_uid": pair["case_b_uid"],
                        "is_same": decision["is_same"], "decision_origin": "explicit_pairwise_llm",
                        "batch_id": batch_number,
                    }
                pending = {key: value for key, value in pending.items() if key not in rows}
                if not pending:
                    break
            except Exception as exc:
                response["parse_error"] = str(exc)
        if pending:
            raise RuntimeError(f"Parallel batch {batch_number} missing {sorted(pending)}")
    return [rows[pair["pair_id"]] for pair in batch], raw


async def run_parallel(cases: list[dict[str, Any]], model: dict[str, Any], base_seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], UnionFind, int]:
    pairs = all_pairs(cases)
    batches = pair_batches(pairs)
    semaphore = asyncio.Semaphore(SERVER_PARALLEL)
    tasks = [run_pair_batch(i, batch, model, base_seed + i * 10, semaphore) for i, batch in enumerate(batches, 1)]
    results = await asyncio.gather(*tasks)
    pair_rows = [row for rows, _ in results for row in rows]
    raw = [entry for _, logs in results for entry in logs]
    if len(pair_rows) != len(pairs) or len({r["pair_id"] for r in pair_rows}) != len(pairs):
        raise RuntimeError("Complete-pair validation failed")
    uf = UnionFind(len(cases))
    for row in pair_rows:
        if row["is_same"]:
            uf.union(int(row["case_a_index"]), int(row["case_b_index"]))
    conflicts = sum(
        not row["is_same"] and uf.find(int(row["case_a_index"])) == uf.find(int(row["case_b_index"]))
        for row in pair_rows
    )
    return pair_rows, raw, uf, conflicts


def classifications(cases: list[dict[str, Any]], uf: UnionFind) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    components: defaultdict[int, list[int]] = defaultdict(list)
    for index in range(len(cases)):
        components[uf.find(index)].append(index)
    retained_indices = {min(indices) for indices in components.values()}
    retained = [cases[i] for i in sorted(retained_indices)]
    removed: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for indices in components.values():
        representative = min(indices)
        for index in sorted(indices):
            decision = "Unique" if index == representative else "Similar"
            decisions.append({
                "case_index": index, "case_uid": cases[index]["CaseUID"], "scenario_id": cases[index]["ScenarioID"],
                "artifact_scoped_scenario_id": cases[index]["ArtifactScopedScenarioID"], "test_case_id": cases[index].get("TestCaseID", ""),
                "title": cases[index].get("Title", ""), "decision": decision,
                "representative_case_uid": cases[representative]["CaseUID"],
            })
            if index != representative:
                removed.append({"DuplicateCase": cases[index], "MatchedWith": cases[representative]})
    decisions.sort(key=lambda row: int(row["case_index"]))
    return retained, removed, decisions


def metrics(cases: list[dict[str, Any]], retained: list[dict[str, Any]], pair_count: int, elapsed: float, conflicts: int) -> dict[str, Any]:
    total, unique = len(cases), len(retained)
    similar = total - unique
    raw_before = {str(c.get("ScenarioID", "")) for c in cases}
    raw_after = {str(c.get("ScenarioID", "")) for c in retained}
    scoped_before = {str(c.get("ArtifactScopedScenarioID", "")) for c in cases}
    scoped_after = {str(c.get("ArtifactScopedScenarioID", "")) for c in retained}
    trr = similar / total if total else math.nan
    raw_scp = len(raw_after) / len(raw_before) if raw_before else math.nan
    scoped_scp = len(scoped_after) / len(scoped_before) if scoped_before else math.nan
    denominator = 1 - trr
    return {
        "total_input_cases": total, "unique_count": unique, "similar_count": similar, "trr": trr,
        "raw_scenarios_before": len(raw_before), "raw_scenarios_after": len(raw_after), "legacy_raw_id_scp": raw_scp,
        "artifact_scoped_scenarios_before": len(scoped_before), "artifact_scoped_scenarios_after": len(scoped_after),
        "artifact_scoped_scp": scoped_scp, "legacy_srg": raw_scp / denominator if denominator else math.nan,
        "artifact_scoped_srg": scoped_scp / denominator if denominator else math.nan,
        "comparison_count": pair_count, "runtime_seconds": elapsed, "transitivity_conflicts": conflicts,
    }


def setup_service() -> Any:
    os.environ["MONGO_URI"] = "mongodb://127.0.0.1:27017"
    os.environ["DATABASE_NAME"] = "stlc_database"
    os.environ["MODEL_API_BASE_URL"] = SERVER_URL
    os.environ["MODEL_API_KEY"] = ""
    sys.path.insert(0, str(BACKEND))
    try:
        import google.generativeai  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        try:
            import google  # type: ignore
        except ModuleNotFoundError:
            google = types.ModuleType("google")
            google.__path__ = []  # type: ignore[attr-defined]
            sys.modules["google"] = google
        generativeai = types.ModuleType("google.generativeai")
        generativeai.configure = lambda **_: None  # type: ignore[attr-defined]
        generativeai.GenerativeModel = object  # type: ignore[attr-defined]
        sys.modules["google.generativeai"] = generativeai
        setattr(google, "generativeai", generativeai)
    semantic = types.ModuleType("services.semantic_similarity_service")
    semantic.rank_semantic_candidates = lambda case, candidates, limit=None: [(c, 0.0) for c in candidates]
    sys.modules["services.semantic_similarity_service"] = semantic
    from services.test_case_optimization_service import TestCaseOptimizationService
    return TestCaseOptimizationService()


def run_id(suite_id: str, model_key: str, mode: str, repeat: int) -> str:
    mode_token = "BULK" if mode == "bulk" else "PARALLEL"
    return f"{suite_id}_{model_key.upper()}_{mode_token}_R{repeat:02d}"


def run_directory(suite_id: str, model_key: str, mode: str, repeat: int) -> Path:
    root = ROOT / ("05_bulk_runs" if mode == "bulk" else "06_parallel_runs")
    return root / SUITES[suite_id]["folder"] / model_key / f"run_{repeat:02d}"


def next_attempt(run_dir: Path) -> Path:
    attempts = run_dir / "attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    existing = [int(p.name.split("_")[-1]) for p in attempts.glob("attempt_*" if os.name != "nt" else "attempt_*") if p.name.split("_")[-1].isdigit()]
    path = attempts / f"attempt_{(max(existing) if existing else 0) + 1:03d}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def promote_attempt(attempt: Path, run_dir: Path) -> None:
    for name in ("run_config.json", "suite_manifest.json", "raw_output.json", "classified_pairs.csv", "retained_cases.json", "removed_cases.json", "metrics.json", "execution_log.txt", "database_record_ids.txt", "case_classifications.csv"):
        source = attempt / name
        if source.exists():
            shutil.copy2(source, run_dir / name)


async def run_one(service: Any, db: Any, suite: dict[str, Any], suite_id: str, model_key: str, model: dict[str, Any], mode: str, repeat: int, model_hash: str) -> dict[str, Any]:
    identifier = run_id(suite_id, model_key, mode, repeat)
    run_dir = run_directory(suite_id, model_key, mode, repeat)
    run_dir.mkdir(parents=True, exist_ok=True)
    final_metrics = run_dir / "metrics.json"
    existing_db = db["test_case_optimizations"].find_one({"process_title": identifier})
    if final_metrics.exists() and existing_db:
        prior = json.loads(final_metrics.read_text(encoding="utf-8"))
        tag = (((existing_db.get("optimization_results") or {}).get("revision_metadata") or {}).get("experiment_id"))
        if prior.get("status") == "COMPLETE" and tag == EXPERIMENT_ID:
            print(f"SKIP COMPLETE {identifier}", flush=True)
            return prior
    if existing_db:
        raise RuntimeError(f"Refusing to overwrite existing DB process_title: {identifier}")
    attempt = next_attempt(run_dir)
    base_seed = BASE_SEED + repeat - 1
    config = {
        "experiment_id": EXPERIMENT_ID, "run_id": identifier, "suite_id": suite_id,
        "suite_hash": suite["suite_content_hash"], "source_artifact": suite["source_artifact"],
        "source_hash": suite["source_artifact_hash"], "model_key": model_key, "model_display": model["display"],
        "model_api_name": model["api_model"], "model_alias": model["alias"], "model_path": str(model["path"]),
        "model_sha256": model_hash, "model_size_bytes": model["path"].stat().st_size,
        "quantization": model["quantization"], "parameter_class": model["parameter_class"],
        "mode": "Local Bulk" if mode == "bulk" else "Controlled Local Parallel", "repeat": repeat,
        "temperature": TEMPERATURE, "top_p": TOP_P, "top_k": TOP_K, "seed_policy": f"base={base_seed}; request seed=base+deterministic call index",
        "server_context": SERVER_CONTEXT, "server_parallel_slots": SERVER_PARALLEL, "per_request_context_budget": PER_REQUEST_CONTEXT,
        "max_output_tokens": model["max_output_tokens"], "reasoning_effort": "low", "enable_thinking": False,
        "structured_output": "strict JSON Schema", "input_ordering": "fixed suite order", "preprocessing": "none; IDs omitted from semantic prompt",
        "postprocessing": "validated JSON; deterministic union-find", "parser": "strict expected-ID JSON validation with bounded retries",
        "retry_behavior": f"up to {MAX_RETRIES} attempts per missing/malformed batch", "decision_schema": "Unique/Similar",
        "scenario_identity": "artifact_type::source_file::local_scenario_id", "system_prompt": SYSTEM_PROMPT,
        "semantic_criteria": SEMANTIC_CRITERIA, "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "comparison_prompt_template_sha256": hashlib.sha256((BULK_TEMPLATE if mode == "bulk" else PAIR_TEMPLATE).encode()).hexdigest(),
        "unsupported_parameters": [], "created_at": datetime.now().astimezone().isoformat(),
    }
    config["configuration_hash"] = stable_json_hash(config)
    (attempt / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (attempt / "suite_manifest.json").write_text(json.dumps({k: v for k, v in suite.items() if k != "cases"}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    started = time.time()
    try:
        if mode == "bulk":
            pair_rows, raw, uf = await run_bulk(suite["cases"], model, base_seed)
            conflicts = 0
        else:
            pair_rows, raw, uf, conflicts = await run_parallel(suite["cases"], model, base_seed)
        elapsed = time.time() - started
        retained, removed, decisions = classifications(suite["cases"], uf)
        computed = metrics(suite["cases"], retained, len(pair_rows), elapsed, conflicts)
        record = {**config, **computed, "status": "COMPLETE"}
        write_csv(attempt / "classified_pairs.csv", pair_rows, list(pair_rows[0]))
        write_csv(attempt / "case_classifications.csv", decisions, list(decisions[0]))
        (attempt / "retained_cases.json").write_text(json.dumps(retained, ensure_ascii=False, indent=2), encoding="utf-8")
        (attempt / "removed_cases.json").write_text(json.dumps(removed, ensure_ascii=False, indent=2), encoding="utf-8")
        (attempt / "raw_output.json").write_text(json.dumps({"run_id": identifier, "responses": raw}, ensure_ascii=False, indent=2), encoding="utf-8")
        persistence = {
            "success": True, "optimization_type": "local_bulk_partitioned" if mode == "bulk" else "controlled_local_parallel",
            "used_model": model["api_model"], "unique_test_cases": retained, "similar_test_cases": removed,
            "comparison_logs": pair_rows, "revision_metadata": record,
        }
        if not service.save_optimization_results(identifier, persistence, model["api_model"]):
            raise RuntimeError("Application persistence layer returned false")
        db_doc = db["test_case_optimizations"].find_one({"process_title": identifier}, {"_id": 1, "optimization_results.revision_metadata.experiment_id": 1})
        if not db_doc:
            raise RuntimeError("Database record missing after persistence")
        record["database_record_id"] = str(db_doc["_id"])
        (attempt / "database_record_ids.txt").write_text(record["database_record_id"] + "\n", encoding="utf-8")
        (attempt / "metrics.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        (attempt / "execution_log.txt").write_text(f"COMPLETE\nrun_id={identifier}\nruntime_seconds={elapsed:.6f}\npairs={len(pair_rows)}\ndb_id={record['database_record_id']}\n", encoding="utf-8")
        promote_attempt(attempt, run_dir)
        print(f"COMPLETE {identifier} unique={record['unique_count']} similar={record['similar_count']} runtime={elapsed:.1f}s", flush=True)
        return record
    except Exception as exc:
        elapsed = time.time() - started
        failure = {**config, "status": "FAILED", "runtime_seconds": elapsed, "error": str(exc), "traceback": traceback.format_exc()}
        (attempt / "metrics.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8")
        (attempt / "execution_log.txt").write_text(failure["traceback"], encoding="utf-8")
        print(f"FAILED {identifier}: {exc}", flush=True)
        raise


def update_aggregate(records: list[dict[str, Any]]) -> None:
    path = ROOT / "07_variability_analysis" / "aggregated_results.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict[str, Any]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            existing = {row["run_id"]: row for row in csv.DictReader(handle)}
    for record in records:
        existing[record["run_id"]] = record
    rows = [existing[key] for key in sorted(existing)]
    fields = sorted({key for row in rows for key in row})
    write_csv(path, rows, fields)


async def main_async(args: argparse.Namespace) -> int:
    client = MongoClient("mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=5000)
    db = client["stlc_database"]
    db.command("ping")
    service = setup_service()
    selected_models = args.models or list(MODELS)
    selected_suites = args.suites or list(SUITES)
    selected_modes = args.modes or ["bulk", "parallel"]
    all_records: list[dict[str, Any]] = []
    for model_key in selected_models:
        model = MODELS[model_key]
        if not model["path"].exists():
            raise FileNotFoundError(model["path"])
        print(f"HASHING MODEL {model_key}", flush=True)
        model_hash = sha256_file(model["path"])
        hash_dir = ROOT / "04_full_suite_design" / "model_hashes"
        hash_dir.mkdir(parents=True, exist_ok=True)
        (hash_dir / f"{model_key}.sha256").write_text(f"{model_hash}  {model['path']}\n", encoding="utf-8")
        process: subprocess.Popen[str] | None = None
        try:
            process = start_server(model, ROOT / "01_environment" / f"llama_server_{model_key}.log")
            for suite_id in selected_suites:
                suite = load_suite(suite_id)
                for mode in selected_modes:
                    for repeat in range(args.start_repeat, args.repeats + 1):
                        attempts = 0
                        while True:
                            attempts += 1
                            try:
                                record = await run_one(service, db, suite, suite_id, model_key, model, mode, repeat, model_hash)
                                all_records.append(record)
                                update_aggregate(all_records)
                                break
                            except Exception:
                                if attempts >= args.run_attempts:
                                    raise
                                print(f"RETRY RUN {run_id(suite_id, model_key, mode, repeat)} attempt={attempts + 1}", flush=True)
        finally:
            stop_server(process)
    update_aggregate(all_records)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", choices=list(MODELS))
    parser.add_argument("--suites", nargs="*", choices=list(SUITES))
    parser.add_argument("--modes", nargs="*", choices=["bulk", "parallel"])
    parser.add_argument("--start-repeat", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--run-attempts", type=int, default=3)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(parse_args())))
