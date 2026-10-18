"""
test_report_quality_evaluator.py
--------------------------------
Test script for methodology-compliant report quality evaluator
"""

import asyncio
import sys
from services.report_quality_evaluator import report_quality_evaluator, ReportQualityEvaluator

# Sample report with all required sections
COMPLETE_REPORT = """
# Test Report - Product Detection System

## 📋 Test Summary

This comprehensive test report evaluates the ProductDetection class. The analysis shows that 
the system performs well under normal conditions but exhibits issues with edge cases.

Total tests executed: 150
Passed: 120
Failed: 25
Blocked: 5

## 📊 Test Metrics & Results

The test execution metrics demonstrate a pass rate of 80%, which indicates reasonable quality.
This was achieved because the core functionality is robust. However, the failed tests suggest
potential issues in error handling mechanisms.

## 🎯 Quality Assessment

Analysis shows that code quality is generally good. The implementation reveals strong adherence
to design patterns. Assessment indicates room for improvement in exception handling.

## 🐛 Defect Analysis

Total defects found: 25
Critical: 5
Major: 10
Minor: 10

The defects are primarily concentrated in the input validation module, which suggests
a systematic issue that requires attention.

## 📈 Coverage Analysis

Test coverage: 85%
Code coverage: 78%
Requirement coverage: 90%

Coverage statistics demonstrate comprehensive testing across functional areas.

## ⚠️ Risk Assessment

Risk level: Medium

The residual risk stems from incomplete error handling in edge cases. This poses a threat
to system stability under unexpected inputs. Therefore, additional validation is recommended.

## 💡 Recommendations

1. Implement robust input validation for edge cases
2. Add comprehensive error handling in critical paths
3. Increase test coverage for boundary conditions

These actions are necessary due to the identified gaps in error handling.

## ✅ Test Closure Decision

Test readiness: Conditional Pass

The system is ready for deployment with minor fixes. The quality assessment indicates
acceptable risk levels for production release.

## 📝 Lessons Learned

Key improvement: Enhanced error handling strategies needed
Process improvement: Earlier integration of boundary testing
"""

# Sample report with missing sections and ambiguity
INCOMPLETE_REPORT = """
# Test Report

## Test Summary

Maybe the system works, but we're not entirely sure. It seems like there might be some issues,
possibly related to edge cases. Approximately 80% of tests passed, which could be good enough.

## Test Results

Some tests passed, several failed. The results appear unclear and perhaps need more investigation.
"""

# Sample execution data for coverage calculation
EXECUTION_DATA = {
    "test_cases": [
        {"TestCaseID": "TC-001", "Status": "Passed"},
        {"TestCaseID": "TC-002", "Status": "Failed"},
        {"TestCaseID": "TC-003", "Status": "Passed"}
    ],
    "test_scenarios": [
        {"ScenarioID": "TS-001", "Title": "Functional Testing"},
        {"ScenarioID": "TS-002", "Title": "Error Handling"}
    ],
    "processes": [
        {"process_name": "test_scenario_generation"},
        {"process_name": "test_case_generation"}
    ]
}


def print_evaluation_results(results: dict, title: str):
    """Pretty print evaluation results"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    
    print(f"\n📊 Overall Score: {results['overall_score']:.4f}")
    print(f"\n   Individual Metrics (0-1 scale):")
    print(f"   ├─ Completeness: {results['completeness']:.4f}")
    print(f"   ├─ Coverage:     {results['coverage']:.4f}")
    print(f"   ├─ Clarity:      {results['clarity']:.4f}")
    print(f"   ├─ Depth:        {results['depth']:.4f}")
    print(f"   └─ Consistency:  {results['consistency']:.4f}")
    
    print(f"\n   Weights Used:")
    for metric, weight in results['weights_used'].items():
        print(f"   • {metric}: {weight:.2f}")
    
    details = results.get('calculation_details', {})
    print(f"\n   Calculation Details:")
    print(f"   • Sections Required: {details.get('sections_required', 0)}")
    print(f"   • Sections Present:  {details.get('sections_present', 0)}")
    print(f"   • Total Sentences:   {details.get('total_sentences', 0)}")
    print(f"   • Sections Detected: {', '.join(details.get('sections_detected', []))}")


def test_complete_report():
    """Test evaluator with complete, high-quality report"""
    print("\n" + "="*70)
    print("TEST 1: Complete, High-Quality Report")
    print("="*70)
    
    results = report_quality_evaluator.evaluate_report(
        report_content=COMPLETE_REPORT,
        execution_data=EXECUTION_DATA,
        metadata={}
    )
    
    print_evaluation_results(results, "Complete Report Evaluation")
    
    # Assertions
    assert results['completeness'] > 0.8, "Should detect most required sections"
    assert results['clarity'] > 0.7, "Should have few ambiguity markers"
    assert results['depth'] > 0.3, "Should contain analytical content"
    assert results['consistency'] == 1.0, "Numbers should be consistent"
    
    print("\n✅ All assertions passed!")


def test_incomplete_report():
    """Test evaluator with incomplete, low-quality report"""
    print("\n" + "="*70)
    print("TEST 2: Incomplete, Low-Quality Report")
    print("="*70)
    
    results = report_quality_evaluator.evaluate_report(
        report_content=INCOMPLETE_REPORT,
        execution_data=EXECUTION_DATA,
        metadata={}
    )
    
    print_evaluation_results(results, "Incomplete Report Evaluation")
    
    # Assertions
    assert results['completeness'] < 0.4, "Should detect missing sections"
    assert results['clarity'] < 0.5, "Should detect high ambiguity"
    assert results['depth'] < 0.3, "Should detect lack of analysis"
    
    print("\n✅ All assertions passed!")


def test_custom_weights():
    """Test evaluator with custom weights"""
    print("\n" + "="*70)
    print("TEST 3: Custom Weights")
    print("="*70)
    
    # Prioritize completeness and consistency
    custom_weights = {
        "completeness": 0.30,
        "coverage": 0.15,
        "clarity": 0.15,
        "depth": 0.10,
        "consistency": 0.30
    }
    
    evaluator = ReportQualityEvaluator(weights=custom_weights)
    
    results = evaluator.evaluate_report(
        report_content=COMPLETE_REPORT,
        execution_data=EXECUTION_DATA,
        metadata={}
    )
    
    print_evaluation_results(results, "Custom Weights Evaluation")
    
    # Verify weights are applied
    assert results['weights_used']['completeness'] == 0.30
    assert results['weights_used']['consistency'] == 0.30
    
    print("\n✅ Custom weights applied correctly!")


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*70)
    print("TEST 4: Edge Cases")
    print("="*70)
    
    # Empty report
    print("\n   Testing empty report...")
    results = report_quality_evaluator.evaluate_report(
        report_content="",
        execution_data=None,
        metadata={}
    )
    assert results['completeness'] == 0.0
    print("   ✓ Empty report handled correctly")
    
    # No execution data (coverage should default to 0.5)
    print("   Testing no execution data...")
    results = report_quality_evaluator.evaluate_report(
        report_content=COMPLETE_REPORT,
        execution_data=None,
        metadata={}
    )
    assert results['coverage'] == 0.5
    print("   ✓ Missing execution data handled correctly")
    
    # Report with only headers (no content)
    print("   Testing headers-only report...")
    headers_only = "\n".join([
        "## Test Summary",
        "## Test Metrics",
        "## Quality Assessment"
    ])
    results = report_quality_evaluator.evaluate_report(
        report_content=headers_only,
        execution_data=None,
        metadata={}
    )
    assert results['completeness'] > 0.0
    assert results['depth'] == 0.0  # No sentences = no analytical content
    print("   ✓ Headers-only report handled correctly")
    
    print("\n✅ All edge cases handled correctly!")


def compare_methodologies():
    """Compare old vs new methodology"""
    print("\n" + "="*70)
    print("TEST 5: Methodology Comparison")
    print("="*70)
    
    from services.quality_metrics_calculator import quality_calculator
    
    # Create mock process output for old calculator
    mock_output = {
        "test_scenarios": {
            "TestScenarios": [
                {
                    "ScenarioID": "TS-001",
                    "Title": "Functional Test",
                    "Description": "Test core functionality with valid inputs and expected outputs",
                    "Objective": "Verify system behavior"
                }
            ]
        }
    }
    
    # Old methodology (1-10 scale, 4 dimensions)
    old_results = quality_calculator.calculate_process_quality(
        "test_scenario_generation",
        mock_output
    )
    
    # New methodology (0-1 scale, 5 dimensions)
    new_results = report_quality_evaluator.evaluate_report(
        report_content=COMPLETE_REPORT,
        execution_data=EXECUTION_DATA,
        metadata={}
    )
    
    print("\n📊 Old Methodology (1-10 scale, 4D):")
    print(f"   Overall: {old_results['score']}/10")
    print(f"   • Completeness: {old_results['completeness']}/10")
    print(f"   • Clarity: {old_results['clarity']}/10")
    print(f"   • Coverage: {old_results['coverage']}/10")
    print(f"   • Depth: {old_results['depth']}/10")
    
    print("\n📊 New Methodology (0-1 scale, 5D):")
    print(f"   Overall: {new_results['overall_score']:.4f}")
    print(f"   • Completeness: {new_results['completeness']:.4f}")
    print(f"   • Coverage: {new_results['coverage']:.4f}")
    print(f"   • Clarity: {new_results['clarity']:.4f}")
    print(f"   • Depth: {new_results['depth']:.4f}")
    print(f"   • Consistency: {new_results['consistency']:.4f}")
    
    print("\n✅ Both methodologies working!")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  REPORT QUALITY EVALUATOR - METHODOLOGY COMPLIANCE TEST")
    print("="*70)
    
    try:
        test_complete_report()
        test_incomplete_report()
        test_custom_weights()
        test_edge_cases()
        compare_methodologies()
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED - METHODOLOGY COMPLIANT")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
