"""
Test parse_execution_stats function with real terminal output
"""
import re

def parse_execution_stats(terminal_output: str) -> dict:
    """
    Parse execution statistics from terminal output
    
    Returns:
        Dictionary with total_tests, passed, failed, skipped, success_rate
    """
    stats = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "success_rate": 0.0
    }
    
    try:
        # Parse Total Tests
        total_match = re.search(r'Total Tests:\s*(\d+)', terminal_output)
        if total_match:
            stats["total_tests"] = int(total_match.group(1))
        
        # Parse Successful
        passed_match = re.search(r'✅\s*Successful:\s*(\d+)', terminal_output)
        if passed_match:
            stats["passed"] = int(passed_match.group(1))
        
        # Parse Failed
        failed_match = re.search(r'❌\s*Failed:\s*(\d+)', terminal_output)
        if failed_match:
            stats["failed"] = int(failed_match.group(1))
        
        # Calculate success rate
        if stats["total_tests"] > 0:
            stats["success_rate"] = round((stats["passed"] / stats["total_tests"]) * 100, 1)
        
        print(f"📊 Parsed execution stats: {stats}")
        
    except Exception as e:
        print(f"⚠️ Error parsing execution stats: {str(e)}")
    
    return stats


# Test with the actual format
test_output = """
================================================================================
BATCH TEST EXECUTION RESULTS
================================================================================

CONTEXT-AWARE EXECUTION:
  ✅ Source code context extracted from database
  ✅ AI received both test code and source code
  ✅ Each test executed with full understanding of context

SUMMARY:
  Total Tests: 92
  ✅ Successful: 92
  ❌ Failed: 0
  Success Rate: 100.0%

================================================================================
"""

print("Testing parse_execution_stats function...")
print("=" * 80)
result = parse_execution_stats(test_output)
print("\nResult:")
print(f"  Total Tests: {result['total_tests']}")
print(f"  Passed: {result['passed']}")
print(f"  Failed: {result['failed']}")
print(f"  Skipped: {result['skipped']}")
print(f"  Success Rate: {result['success_rate']}%")

print("\n" + "=" * 80)
if result['total_tests'] == 92 and result['passed'] == 92 and result['failed'] == 0:
    print("✅ TEST PASSED - Function works correctly!")
else:
    print("❌ TEST FAILED - Function did not parse correctly")
