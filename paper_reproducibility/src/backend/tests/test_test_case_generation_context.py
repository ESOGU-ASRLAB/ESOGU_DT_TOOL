import asyncio
import json
import sys
import types

import routers.test_scenario_generation_router as generation_router
from routers.test_scenario_generation_router import (
    TEST_CASE_CONTEXT_SWITCH_THRESHOLD,
    TEST_CASE_LARGE_CONTEXT_MODEL,
    _group_cases_by_scenario,
    _parse_test_case_json,
    _select_test_case_model,
    _unsupported_test_case,
)


class _Request:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


def _case(scenario_id, test_case_id):
    return {
        "ScenarioID": scenario_id,
        "TestCaseID": test_case_id,
        "Title": "Grounded case",
        "TargetSymbols": ["robot.home"],
        "ExecutionStatus": "executable",
    }


def _response(scenario_id=None):
    results = [] if scenario_id is None else [{
        "ScenarioID": scenario_id,
        "TestCases": [_case(scenario_id, f"{scenario_id}_TC_001")],
    }]
    return json.dumps({"ScenarioResults": results, "Summary": {"Coverage": "coverage"}})


class _FakeLLMClient:
    responses = []
    calls = []

    def __init__(self, model_name=None, **_kwargs):
        self.model_name = model_name

    def get_model_identifier(self, model_name):
        return model_name

    async def get_model_context_length(self, _model_name):
        return 32768

    async def generate_response(self, prompt, **_kwargs):
        self.__class__.calls.append(prompt)
        return self.__class__.responses.pop(0)


def test_selected_model_is_kept_through_64000_tokens():
    assert _select_test_case_model("llama3.2:3b", TEST_CASE_CONTEXT_SWITCH_THRESHOLD) == "llama3.2:3b"


def test_large_local_context_switches_only_after_64000_tokens():
    assert _select_test_case_model("llama3.2:3b", TEST_CASE_CONTEXT_SWITCH_THRESHOLD + 1) == TEST_CASE_LARGE_CONTEXT_MODEL


def test_gemini_is_not_silently_replaced_for_large_context():
    assert _select_test_case_model("gemini-2.5-pro", 100_000) == "gemini-2.5-pro"


def test_single_response_parser_accepts_fenced_json():
    parsed = _parse_test_case_json('```json\n{"TestCases": [], "Summary": {}}\n```')
    assert parsed["ScenarioResults"] == []


def test_grouped_response_preserves_scenario_ownership():
    parsed = _parse_test_case_json(
        '{"ScenarioResults":[{"ScenarioID":"TS_007","TestCases":[{"TestCaseID":"TC_1"}]}]}'
    )
    grouped = _group_cases_by_scenario(parsed, ["TS_007", "TS_008"])

    assert grouped["TS_007"][0]["TestCaseID"] == "TC_1"
    assert grouped["TS_008"] == []


def test_legacy_flat_response_is_normalized_by_scenario_id():
    parsed = _parse_test_case_json(
        '{"TestCases":[{"ScenarioID":"TS_007","TestCaseID":"TC_1"}]}'
    )
    assert parsed["ScenarioResults"][0]["ScenarioID"] == "TS_007"


def test_snake_case_small_model_response_is_normalized():
    parsed = _parse_test_case_json(
        '{"scenario_results":[{"scenario_id":"TS_007",'
        '"test_cases":[{"scenario_id":"TS_007","TestCaseID":"TC_1"}]}],'
        '"summary":{"Coverage":"source"}}'
    )

    assert parsed["ScenarioResults"][0]["ScenarioID"] == "TS_007"
    assert parsed["ScenarioResults"][0]["TestCases"][0]["TestCaseID"] == "TC_1"
    assert parsed["Summary"]["Coverage"] == "source"


def test_bare_test_case_array_is_normalized():
    parsed = _parse_test_case_json(
        '[{"ScenarioID":"TS_007","TestCaseID":"TC_1"}]'
    )

    assert parsed["ScenarioResults"][0]["ScenarioID"] == "TS_007"


def test_unsupported_placeholder_is_diagnostic_and_not_executable():
    case = _unsupported_test_case("TS_007", "Safe Home", "Missing source")

    assert case["ExecutionStatus"] == "unsupported"
    assert case["IsDiagnostic"] is True
    assert case["TargetSymbols"] == []


def test_missing_scenario_is_recovered_by_one_coverage_repair(monkeypatch):
    _FakeLLMClient.responses = [_response("TS_008"), _response("TS_007")]
    _FakeLLMClient.calls = []
    monkeypatch.setattr(generation_router, "LLMClient", _FakeLLMClient)
    monkeypatch.setitem(
        sys.modules,
        "utils.text_splitter",
        types.SimpleNamespace(count_tokens=lambda text: len(text.split())),
    )
    request = _Request({
        "selected_scenarios": [
            {"scenario_id": "TS_007", "scenario": "Safe Home"},
            {"scenario_id": "TS_008", "scenario": "Emergency Stop"},
        ],
        "process_prompt": "Generate grounded cases",
        "selected_files": [],
        "project_structure": {"project_files": [{"path": "robot.py"}], "files": []},
        "ai_model": "llama3.2:3b",
    })

    result = asyncio.run(asyncio.wait_for(
        generation_router._generate_test_cases_for_scenarios_impl(request), timeout=3
    ))

    by_id = {item["scenario_id"]: item for item in result["test_case_results"]}
    assert len(_FakeLLMClient.calls) == 2
    assert by_id["TS_007"]["status"] == "success"
    assert by_id["TS_007"]["repair_applied"] is True
    assert result["summary"]["repair_succeeded_ids"] == ["TS_007"]


def test_grounded_but_unsupported_result_is_regenerated_with_test_doubles(monkeypatch):
    unsupported = {
        "ScenarioID": "TS_005",
        "TestCases": [{
            **_case("TS_005", "TC_UNSUPPORTED"),
            "ExecutionStatus": "unsupported",
            "UnsupportedReason": "Logger output cannot be observed.",
        }],
    }
    repaired_cases = [_case("TS_005", f"TS_005_TC_{index:03d}") for index in range(1, 8)]
    _FakeLLMClient.responses = [
        json.dumps({"ScenarioResults": [unsupported], "Summary": {}}),
        json.dumps({
            "ScenarioResults": [{"ScenarioID": "TS_005", "TestCases": repaired_cases}],
            "Summary": {},
        }),
    ]
    _FakeLLMClient.calls = []
    monkeypatch.setattr(generation_router, "LLMClient", _FakeLLMClient)
    monkeypatch.setitem(
        sys.modules,
        "utils.text_splitter",
        types.SimpleNamespace(count_tokens=lambda text: len(text.split())),
    )
    request = _Request({
        "selected_scenarios": [{
            "scenario_id": "TS_005",
            "scenario": "Planning failure",
            "TargetSymbols": ["robot.home"],
            "ExecutionStatus": "executable",
        }],
        "process_prompt": "Generate grounded cases",
        "selected_files": [],
        "project_structure": {
            "project_files": [{"path": "robot.py"}],
            "files": [],
            "symbol_index": ["robot.home"],
        },
        "ai_model": "llama3.2:3b",
    })

    result = asyncio.run(asyncio.wait_for(
        generation_router._generate_test_cases_for_scenarios_impl(request), timeout=3
    ))

    scenario = result["test_case_results"][0]
    assert len(_FakeLLMClient.calls) == 2
    assert scenario["status"] == "success"
    assert scenario["repair_applied"] is True
    assert scenario["test_cases_count"] == 7
    assert result["summary"]["underfilled_before_repair"] == ["TS_005"]
    assert "mocks/spies" in _FakeLLMClient.calls[1]


def test_invalid_scenario_echo_is_retried_with_schema_repair(monkeypatch):
    _FakeLLMClient.responses = [
        json.dumps({"scenario_id": "TS_007", "scenario": "Safe Home"}),
        json.dumps({
            "TestCases": [_case("TS_007", "TS_007_TC_001")],
            "Summary": {"Coverage": "source"},
        }),
    ]
    _FakeLLMClient.calls = []
    monkeypatch.setattr(generation_router, "LLMClient", _FakeLLMClient)
    monkeypatch.setitem(
        sys.modules,
        "utils.text_splitter",
        types.SimpleNamespace(count_tokens=lambda text: len(text.split())),
    )
    request = _Request({
        "selected_scenarios": [{"scenario_id": "TS_007", "scenario": "Safe Home"}],
        "process_prompt": "Generate grounded cases",
        "selected_files": [],
        "project_structure": {"project_files": [{"path": "robot.py"}], "files": []},
        "ai_model": "llama3.2:3b",
    })

    result = asyncio.run(asyncio.wait_for(
        generation_router._generate_test_cases_for_scenarios_impl(request), timeout=3
    ))

    assert len(_FakeLLMClient.calls) == 2
    assert result["summary"]["schema_repair_attempted"] is True
    assert result["summary"]["schema_repair_succeeded"] is True
    assert result["test_case_results"][0]["test_cases_count"] == 1


def test_unrepaired_scenario_becomes_visible_unsupported_diagnostic(monkeypatch):
    _FakeLLMClient.responses = [_response(), _response()]
    _FakeLLMClient.calls = []
    monkeypatch.setattr(generation_router, "LLMClient", _FakeLLMClient)
    monkeypatch.setitem(
        sys.modules,
        "utils.text_splitter",
        types.SimpleNamespace(count_tokens=lambda text: len(text.split())),
    )
    request = _Request({
        "selected_scenarios": [{"scenario_id": "TS_007", "scenario": "Safe Home"}],
        "process_prompt": "Generate grounded cases",
        "selected_files": [],
        "project_structure": {"project_files": [{"path": "robot.py"}], "files": []},
        "ai_model": "llama3.2:3b",
    })

    result = asyncio.run(asyncio.wait_for(
        generation_router._generate_test_cases_for_scenarios_impl(request), timeout=3
    ))
    scenario = result["test_case_results"][0]

    assert scenario["status"] == "unsupported"
    assert scenario["test_cases_count"] == 1
    assert scenario["test_cases"][0]["IsDiagnostic"] is True
    assert result["summary"]["failed_scenarios"] == 0
    assert result["summary"]["unsupported_scenarios"] == 1
