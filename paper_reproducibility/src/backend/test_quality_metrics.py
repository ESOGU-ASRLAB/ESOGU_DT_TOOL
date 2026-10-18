"""
Test Quality Metrics Calculator
--------------------------------
Verify that quality scores are calculated from quantitative data
"""

import sys
sys.path.append('.')

from services.quality_metrics_calculator import quality_calculator
import json


def test_scenario_quality():
    """Test Test Scenario Generation quality calculation"""
    print("\n" + "="*60)
    print("TEST: Test Scenario Generation Quality Metrics")
    print("="*60)
    
    # Sample scenario data
    output = {
        "test_scenarios": {
            "TestScenarios": [
                {
                    "ScenarioID": "TS_001",
                    "Title": "User Login - Valid Credentials",
                    "Description": "Test user login with valid credentials. Precondition: User exists. Step 1: Enter username. Step 2: Enter password. Step 3: Click login. Expected result: User logged in successfully.",
                    "Objective": "Verify login functionality",
                    "Category": "Functional"
                },
                {
                    "ScenarioID": "TS_002",
                    "Title": "User Login - Invalid Password Edge Case",
                    "Description": "Test edge case with maximum length password that is invalid.",
                    "Objective": "Test boundary conditions",
                    "Category": "Edge Case"
                },
                {
                    "ScenarioID": "TS_003",
                    "Title": "User Login - Negative Test with Empty Fields",
                    "Description": "Negative test case. Expected: Error message shown.",
                    "Objective": "Verify error handling",
                    "Category": "Negative"
                },
                {
                    "ScenarioID": "TS_004",
                    "Title": "Load Test - Multiple Concurrent Logins",
                    "Description": "Performance test with 100 concurrent users. Expected: Response time < 2s.",
                    "Objective": "Test system performance",
                    "Category": "Performance"
                },
                {
                    "ScenarioID": "",  # Incomplete
                    "Title": "Test without ID",
                    "Description": "Short desc",
                    "Objective": ""
                }
            ]
        }
    }
    
    quality = quality_calculator.calculate_process_quality(
        "test_scenario_generation", 
        output
    )
    
    print("\nQuality Metrics:")
    print(json.dumps(quality, indent=2))
    
    print("\n📊 Analysis:")
    print(f"- Overall Score: {quality['score']}/10")
    print(f"- Completeness: {quality['completeness']}/10 (4/5 scenarios have all required fields)")
    print(f"- Clarity: {quality['clarity']}/10 (Based on avg description length and structure)")
    print(f"- Coverage: {quality['coverage']}/10 (4 different test types detected)")
    print(f"- Depth: {quality['depth']}/10 (Scenarios have preconditions, steps, expected results)")
    
    assert quality['completeness'] > 5, "Completeness should be > 5 (80% complete scenarios)"
    assert quality['coverage'] > 5, "Coverage should be > 5 (good diversity)"
    
    print("\n✅ Test Scenario Quality: PASSED")
    return quality


def test_test_case_quality():
    """Test Test Case Generation quality calculation"""
    print("\n" + "="*60)
    print("TEST: Test Case Generation Quality Metrics")
    print("="*60)
    
    output = {
        "data": {
            "test_case_results": [
                {
                    "test_cases": [
                        {
                            "Title": "Valid login test",
                            "Steps": ["Open app", "Enter username", "Enter password", "Click login"],
                            "TestData": "username: test@test.com, password: Test123",
                            "ExpectedResult": "User successfully logged in"
                        },
                        {
                            "Title": "Invalid password test - negative",
                            "Steps": ["Open app", "Enter username", "Enter wrong password"],
                            "TestData": "username: test@test.com, password: WrongPass",
                            "ExpectedResult": "Error message displayed"
                        },
                        {
                            "Title": "Empty fields test - negative",
                            "Steps": ["Open app", "Click login"],
                            "TestData": "",
                            "ExpectedResult": "Validation error"
                        },
                        {
                            "Title": "Valid registration",
                            "Steps": ["Open registration", "Fill all fields", "Submit"],
                            "TestData": "Full user data",
                            "ExpectedResult": "Account created"
                        }
                    ]
                }
            ]
        }
    }
    
    quality = quality_calculator.calculate_process_quality(
        "test_case_generation", 
        output
    )
    
    print("\nQuality Metrics:")
    print(json.dumps(quality, indent=2))
    
    print("\n📊 Analysis:")
    print(f"- Overall Score: {quality['score']}/10")
    print(f"- Completeness: {quality['completeness']}/10 (All cases have steps and expected results)")
    print(f"- Clarity: {quality['clarity']}/10 (Avg {quality['calculation_details']['avg_steps_per_case']} steps, test data specified)")
    print(f"- Coverage: {quality['coverage']}/10 (Ratio: {quality['calculation_details']['positive_negative_ratio']})")
    print(f"- Depth: {quality['depth']}/10 (Cases have detailed steps)")
    
    assert quality['completeness'] >= 8, "Completeness should be high (all required fields)"
    
    print("\n✅ Test Case Quality: PASSED")
    return quality


def test_optimization_quality():
    """Test Test Case Optimization quality calculation"""
    print("\n" + "="*60)
    print("TEST: Test Case Optimization Quality Metrics")
    print("="*60)
    
    output = {
        "data": {
            "optimized_results": [
                {
                    "test_id": "TC_001",
                    "optimization_rationale": "This test case covers the core login functionality and should be retained for comprehensive coverage."
                },
                {
                    "test_id": "TC_002",
                    "optimization_rationale": "Edge case scenario for boundary value testing, critical for quality assurance."
                },
                {
                    "test_id": "TC_003",
                    "optimization_rationale": "Negative test case essential for error handling validation."
                }
            ]
        },
        "metadata": {
            "original_count": 10,
            "optimized_count": 7  # 30% reduction
        }
    }
    
    quality = quality_calculator.calculate_process_quality(
        "test_case_optimization", 
        output
    )
    
    print("\nQuality Metrics:")
    print(json.dumps(quality, indent=2))
    
    print("\n📊 Analysis:")
    print(f"- Overall Score: {quality['score']}/10")
    print(f"- Completeness: {quality['completeness']}/10 (All optimized cases have justification)")
    print(f"- Clarity: {quality['clarity']}/10 (Rationale quality)")
    print(f"- Coverage: {quality['coverage']}/10 (Optimization rate: {quality['calculation_details']['optimization_rate']})")
    print(f"- Depth: {quality['depth']}/10")
    
    assert quality['completeness'] >= 9, "All cases should have justification"
    
    print("\n✅ Optimization Quality: PASSED")
    return quality


def test_reproducibility():
    """Verify that same input produces same output (reproducibility)"""
    print("\n" + "="*60)
    print("TEST: Reproducibility Check")
    print("="*60)
    
    output = {
        "test_scenarios": {
            "TestScenarios": [
                {
                    "ScenarioID": "TS_001",
                    "Title": "Test",
                    "Description": "Test description with some steps and expected results",
                    "Objective": "Test objective",
                    "Category": "Functional"
                }
            ]
        }
    }
    
    # Calculate twice
    quality1 = quality_calculator.calculate_process_quality("test_scenario_generation", output)
    quality2 = quality_calculator.calculate_process_quality("test_scenario_generation", output)
    
    print(f"\nFirst calculation: {quality1['score']}")
    print(f"Second calculation: {quality2['score']}")
    
    assert quality1 == quality2, "Quality scores must be reproducible!"
    
    print("\n✅ Reproducibility: PASSED - Same input produces same output")


if __name__ == "__main__":
    print("\n" + "🔬 QUALITY METRICS CALCULATOR TESTS 🔬".center(60))
    print("Verifying objective, data-driven quality scoring\n")
    
    try:
        test_scenario_quality()
        test_test_case_quality()
        test_optimization_quality()
        test_reproducibility()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\n📊 Quality metrics are now:")
        print("  ✓ Objective (formula-based)")
        print("  ✓ Reproducible (deterministic)")
        print("  ✓ Data-driven (from quantitative metrics)")
        print("  ✓ Academically defensible (calculable)")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
