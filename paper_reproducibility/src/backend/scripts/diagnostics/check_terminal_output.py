"""
Check the terminal output from test execution to understand the format
"""
import asyncio
from core.database import get_database
from bson import ObjectId

async def check_terminal_output():
    """Check terminal output from a test execution record"""
    db = await get_database()
    collection = db["session_history"]
    
    # Get the specific record
    record = await collection.find_one({"_id": ObjectId("6963c4f0d903317b64cb00c1")})
    
    if record:
        print("=" * 80)
        print("RECORD FOUND")
        print("=" * 80)
        print(f"\nSession ID: {record.get('session_id')}")
        print(f"Timestamp: {record.get('timestamp')}")
        
        processes = record.get("processes", {})
        test_exec = processes.get("test_execution", {})
        
        print(f"\nTest Execution Status: {test_exec.get('status')}")
        print(f"Process Name: {test_exec.get('process_name')}")
        print(f"Model Used: {test_exec.get('model_used')}")
        
        output = test_exec.get("output", {})
        print(f"\nOutput Success: {output.get('success')}")
        print(f"Provider: {output.get('provider')}")
        
        # Print execution results
        exec_results = output.get("execution_results", {})
        print("\n" + "=" * 80)
        print("EXECUTION RESULTS (PARSED)")
        print("=" * 80)
        print(f"Total Tests: {exec_results.get('total_tests')}")
        print(f"Passed: {exec_results.get('passed')}")
        print(f"Failed: {exec_results.get('failed')}")
        print(f"Skipped: {exec_results.get('skipped')}")
        print(f"Success Rate: {exec_results.get('success_rate')}")
        
        # Print terminal output
        terminal_output = output.get("terminal_output", "")
        print("\n" + "=" * 80)
        print("TERMINAL OUTPUT (RAW)")
        print("=" * 80)
        print(terminal_output)
        
        # Try to find the pattern
        print("\n" + "=" * 80)
        print("PATTERN SEARCH")
        print("=" * 80)
        
        import re
        
        # Check if patterns exist
        total_match = re.search(r'Total Tests:\s*(\d+)', terminal_output)
        passed_match = re.search(r'✅\s*Successful:\s*(\d+)', terminal_output)
        failed_match = re.search(r'❌\s*Failed:\s*(\d+)', terminal_output)
        
        print(f"Total Tests pattern found: {bool(total_match)}")
        if total_match:
            print(f"  - Value: {total_match.group(1)}")
        
        print(f"Successful pattern found: {bool(passed_match)}")
        if passed_match:
            print(f"  - Value: {passed_match.group(1)}")
        
        print(f"Failed pattern found: {bool(failed_match)}")
        if failed_match:
            print(f"  - Value: {failed_match.group(1)}")
        
        # Show first 500 characters to see the format
        print("\n" + "=" * 80)
        print("FIRST 500 CHARACTERS")
        print("=" * 80)
        print(repr(terminal_output[:500]))
        
    else:
        print("Record not found!")

if __name__ == "__main__":
    asyncio.run(check_terminal_output())
