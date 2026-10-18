"""
pipeline_controller.py
----------------------
Dependency graph and ordering for the STLC pipeline.
Validates that required steps are present before dependent steps are allowed.
"""

from typing import List, Dict, Set, Tuple

# Full STLC dependency graph — mirrors frontend processes.js
PIPELINE_DEPENDENCIES: Dict[str, List[str]] = {
    "code-review":              [],
    "requirement-analysis":     [],
    "test-planning":            ["code-review", "requirement-analysis"],
    "environment-setup":        [],
    "test-scenario-generation": ["test-planning"],
    "test-case-generation":     ["test-scenario-generation"],
    "test-case-optimization":   ["test-case-generation"],
    "test-code-generation":     ["test-case-optimization", "environment-setup"],
    "test-execution":           ["test-code-generation"],
    "test-reporting":           ["test-execution"],
    "test-closure":             ["test-reporting"],
}

# Canonical STLC execution order
PIPELINE_ORDER: List[str] = [
    "code-review",
    "requirement-analysis",
    "test-planning",
    "environment-setup",
    "test-scenario-generation",
    "test-case-generation",
    "test-case-optimization",
    "test-code-generation",
    "test-execution",
    "test-reporting",
    "test-closure",
]


def sort_steps(selected_steps: List[str]) -> List[str]:
    """
    Return *selected_steps* sorted in canonical STLC execution order.
    Steps not in PIPELINE_ORDER are appended at the end in their original order.
    """
    ordered = [s for s in PIPELINE_ORDER if s in selected_steps]
    extras = [s for s in selected_steps if s not in PIPELINE_ORDER]
    return ordered + extras


def check_dependencies(selected_steps: List[str]) -> List[Dict]:
    """
    Check that all dependencies of the selected steps are also selected.
    Returns a list of violation dicts:
        { "step": step_id, "missing": [dep_id, ...] }
    An empty list means no violations.
    """
    selected_set: Set[str] = set(selected_steps)
    violations = []
    for step in selected_steps:
        missing = [
            dep for dep in PIPELINE_DEPENDENCIES.get(step, [])
            if dep not in selected_set
        ]
        if missing:
            violations.append({"step": step, "missing": missing})
    return violations


def validate_pipeline(selected_steps: List[str]) -> Tuple[bool, List[Dict]]:
    """
    Returns (is_valid, violations).
    A pipeline is valid when all dependency rules are satisfied.
    """
    violations = check_dependencies(selected_steps)
    return (len(violations) == 0, violations)


# Backwards-compat shim kept for any legacy imports
def determine_pipeline(steps_selected: List[str]) -> List[str]:
    return sort_steps(steps_selected)
