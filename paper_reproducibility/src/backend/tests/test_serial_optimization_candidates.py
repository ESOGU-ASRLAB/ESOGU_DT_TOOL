from services.test_case_optimization_service import (
    TestCase,
    _normalized_case_fingerprint,
)
from services import semantic_similarity_service


def _case(case_id: str, title: str, description: str, scenario: str = "TS-1") -> TestCase:
    return TestCase(
        ScenarioID=scenario,
        TestCaseID=case_id,
        Title=title,
        Description=description,
        Objective=description,
    )


def test_sbert_candidates_are_ranked_by_cosine_similarity(monkeypatch):
    related = _case("TC-1", "Safe home position", "Execute safe home motion and verify success")
    unrelated = _case("TC-2", "Configuration parsing", "Reject an invalid YAML configuration", "TS-2")
    source = _case("TC-3", "Verify safe home execution", "Execute safe home motion and assert success")
    monkeypatch.setattr(
        semantic_similarity_service,
        "_embed_texts",
        lambda _texts: [
            [1.0, 0.0],  # source
            [0.0, 1.0],  # unrelated
            [0.9, 0.1],  # related
        ],
    )

    ranked = semantic_similarity_service.rank_semantic_candidates(
        source, [unrelated, related], limit=2
    )

    assert [candidate.TestCaseID for candidate, _score in ranked] == ["TC-1", "TC-2"]
    assert ranked[0][1] > ranked[1][1]


def test_normalized_fingerprint_ignores_case_and_spacing():
    first = _case("TC-1", "Safe Home", "Execute   motion")
    second = _case("TC-2", " safe home ", "execute motion")

    assert _normalized_case_fingerprint(first) == _normalized_case_fingerprint(second)
