"""
Comprehensive Session Validation
Validates all specified sessions for:
1. STLC Process completeness (10 steps)
2. Data availability for Test Reporting
3. Data availability for Test Closure
"""

import asyncio
import json
from core.database import get_database
from services.test_reporting_service import TestReportingService
from services.test_closure_service import TestClosureService

# STLC Manager 10 Steps
STLC_PROCESSES = [
    "requirement_analysis",
    "test_planning",
    "test_scenario_generation",
    "test_case_generation",
    "test_case_optimization",
    "test_code_generation",
    "environment_setup",
    "test_execution",
    "test_reporting",
    "test_closure"
]

# Session ID patterns to search
SESSION_ID_PATTERNS = [
    "8507a7f2",
    "cb196397",
    "841c8cb4",
    "129793d5",
    "bd39408b",
    "project.xml",
    "f9928335",
    "test-exe",
    "07d9af28",
    "d25dc5b4"
]


async def find_sessions_by_patterns(patterns):
    """Find all sessions matching the given patterns"""
    db = await get_database()
    collection = db["session_history"]
    
    sessions = []
    for pattern in patterns:
        cursor = collection.find({"session_id": {"$regex": pattern}})
        found = await cursor.to_list(length=None)
        sessions.extend(found)
    
    # Remove duplicates based on session_id
    unique_sessions = {}
    for session in sessions:
        session_id = session.get("session_id")
        if session_id not in unique_sessions:
            unique_sessions[session_id] = session
    
    return list(unique_sessions.values())


async def validate_session(session, reporting_service, closure_service):
    """
    Validate a single session
    
    Returns:
        dict with validation results
    """
    session_id = session.get("session_id", "unknown")
    processes = session.get("processes", {})
    
    validation = {
        "session_id": session_id,
        "created_at": str(session.get("created_at", "N/A")),
        "processes_found": list(processes.keys()),
        "processes_count": len(processes),
        "missing_processes": [],
        "stlc_completeness": 0,
        "test_scenario_count": 0,
        "test_case_count": 0,
        "test_case_optimized_count": 0,
        "test_execution_count": 0,
        "has_test_reporting_data": False,
        "has_test_closure_data": False,
        "details": {}
    }
    
    # Check STLC completeness
    for process in STLC_PROCESSES:
        if process in processes:
            validation["stlc_completeness"] += 1
        else:
            validation["missing_processes"].append(process)
    
    # Count test scenarios
    if "test_scenario_generation" in processes:
        tsg = processes["test_scenario_generation"]
        output = tsg.get("output", {})
        count = reporting_service._count_process_items("test_scenario_generation", output)
        validation["test_scenario_count"] = count
        validation["has_test_reporting_data"] = True
        validation["has_test_closure_data"] = True
    
    # Count test cases
    if "test_case_generation" in processes:
        tcg = processes["test_case_generation"]
        output = tcg.get("output", {})
        count = reporting_service._count_process_items("test_case_generation", output)
        validation["test_case_count"] = count
        
        # Check data format
        test_case_results = output.get("test_case_results", [])
        data = output.get("data", {})
        test_case_results_nested = data.get("test_case_results", [])
        
        if test_case_results:
            validation["details"]["test_case_format"] = "output.test_case_results (direct)"
        elif test_case_results_nested:
            validation["details"]["test_case_format"] = "output.data.test_case_results (nested)"
        else:
            test_cases = output.get("test_cases", [])
            if test_cases:
                validation["details"]["test_case_format"] = "output.test_cases (flat)"
    
    # Count optimized test cases
    if "test_case_optimization" in processes:
        tco = processes["test_case_optimization"]
        output = tco.get("output", {})
        optimized_cases = output.get("optimized_test_cases", [])
        validation["test_case_optimized_count"] = len(optimized_cases)
    
    # Count test execution
    if "test_execution" in processes:
        te = processes["test_execution"]
        output = te.get("output", {})
        terminal_output = output.get("terminal_output", "")
        
        # Parse execution results
        import re
        passed_match = re.search(r'(\d+)\s+passed', terminal_output)
        failed_match = re.search(r'(\d+)\s+failed', terminal_output)
        skipped_match = re.search(r'(\d+)\s+skipped', terminal_output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        total = passed + failed + skipped
        
        validation["test_execution_count"] = total
        validation["details"]["execution"] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round((passed / total * 100), 2) if total > 0 else 0
        }
    
    return validation


async def main():
    """Main validation function"""
    print(f"\n{'='*100}")
    print("🔍 COMPREHENSIVE SESSION VALIDATION")
    print(f"{'='*100}\n")
    
    # Initialize services
    reporting_service = TestReportingService()
    await reporting_service.initialize()
    
    closure_service = TestClosureService()
    await closure_service.initialize()
    
    # Find all sessions
    print("📦 Searching for sessions matching patterns...")
    sessions = await find_sessions_by_patterns(SESSION_ID_PATTERNS)
    
    print(f"✅ Found {len(sessions)} unique sessions\n")
    
    if not sessions:
        print("❌ No sessions found matching the patterns")
        return
    
    # Validate each session
    validations = []
    for i, session in enumerate(sessions, 1):
        print(f"\n{'='*100}")
        print(f"[{i}/{len(sessions)}] Validating session...")
        print(f"{'='*100}")
        
        validation = await validate_session(session, reporting_service, closure_service)
        validations.append(validation)
        
        # Print summary
        session_id = validation["session_id"]
        print(f"\n📊 Session ID: {session_id}")
        print(f"   Created: {validation['created_at']}")
        print(f"\n   🔄 STLC Completeness: {validation['stlc_completeness']}/10 processes")
        
        if validation['missing_processes']:
            print(f"   ❌ Missing Processes ({len(validation['missing_processes'])}):")
            for mp in validation['missing_processes']:
                print(f"      - {mp}")
        else:
            print(f"   ✅ All 10 STLC processes present!")
        
        print(f"\n   📈 Data Counts:")
        print(f"      - Test Scenarios: {validation['test_scenario_count']}")
        print(f"      - Test Cases: {validation['test_case_count']}")
        print(f"      - Optimized Test Cases: {validation['test_case_optimized_count']}")
        print(f"      - Test Executions: {validation['test_execution_count']}")
        
        if validation.get('details', {}).get('test_case_format'):
            print(f"\n   📦 Test Case Format: {validation['details']['test_case_format']}")
        
        if validation.get('details', {}).get('execution'):
            exec_data = validation['details']['execution']
            print(f"\n   🧪 Execution Details:")
            print(f"      - Passed: {exec_data['passed']}")
            print(f"      - Failed: {exec_data['failed']}")
            print(f"      - Skipped: {exec_data['skipped']}")
            print(f"      - Pass Rate: {exec_data['pass_rate']}%")
        
        print(f"\n   ✅ Test Reporting Compatible: {validation['has_test_reporting_data']}")
        print(f"   ✅ Test Closure Compatible: {validation['has_test_closure_data']}")
    
    # Overall Summary
    print(f"\n\n{'='*100}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*100}\n")
    
    total_sessions = len(validations)
    complete_sessions = sum(1 for v in validations if v['stlc_completeness'] == 10)
    has_scenarios = sum(1 for v in validations if v['test_scenario_count'] > 0)
    has_test_cases = sum(1 for v in validations if v['test_case_count'] > 0)
    has_optimized = sum(1 for v in validations if v['test_case_optimized_count'] > 0)
    has_execution = sum(1 for v in validations if v['test_execution_count'] > 0)
    
    print(f"Total Sessions Analyzed: {total_sessions}")
    print(f"Complete STLC (10/10): {complete_sessions} ({round(complete_sessions/total_sessions*100, 1)}%)")
    print(f"Has Test Scenarios: {has_scenarios} ({round(has_scenarios/total_sessions*100, 1)}%)")
    print(f"Has Test Cases: {has_test_cases} ({round(has_test_cases/total_sessions*100, 1)}%)")
    print(f"Has Optimized Cases: {has_optimized} ({round(has_optimized/total_sessions*100, 1)}%)")
    print(f"Has Test Execution: {has_execution} ({round(has_execution/total_sessions*100, 1)}%)")
    
    # Data availability summary
    print(f"\n📋 Data Availability:")
    total_scenarios = sum(v['test_scenario_count'] for v in validations)
    total_test_cases = sum(v['test_case_count'] for v in validations)
    total_optimized = sum(v['test_case_optimized_count'] for v in validations)
    total_executed = sum(v['test_execution_count'] for v in validations)
    
    print(f"   Total Test Scenarios: {total_scenarios}")
    print(f"   Total Test Cases: {total_test_cases}")
    print(f"   Total Optimized: {total_optimized}")
    print(f"   Total Executed: {total_executed}")
    
    # Test Reporting & Closure readiness
    reporting_ready = sum(1 for v in validations if v['has_test_reporting_data'])
    closure_ready = sum(1 for v in validations if v['has_test_closure_data'])
    
    print(f"\n🎯 Service Compatibility:")
    print(f"   Test Reporting Ready: {reporting_ready}/{total_sessions}")
    print(f"   Test Closure Ready: {closure_ready}/{total_sessions}")
    
    # Session details table
    print(f"\n\n{'='*100}")
    print("📋 DETAILED SESSION TABLE")
    print(f"{'='*100}\n")
    print(f"{'Session ID':<50} {'STLC':<8} {'Scenarios':<10} {'Cases':<8} {'Optimized':<10} {'Executed':<10}")
    print(f"{'-'*50} {'-'*8} {'-'*10} {'-'*8} {'-'*10} {'-'*10}")
    
    for v in validations:
        session_id_short = v['session_id'][:47] + "..." if len(v['session_id']) > 50 else v['session_id']
        stlc = f"{v['stlc_completeness']}/10"
        print(f"{session_id_short:<50} {stlc:<8} {v['test_scenario_count']:<10} {v['test_case_count']:<8} {v['test_case_optimized_count']:<10} {v['test_execution_count']:<10}")
    
    print(f"\n{'='*100}\n")
    
    # Export to JSON
    output_file = "session_validation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(validations, f, indent=2, default=str)
    
    print(f"✅ Detailed validation results exported to: {output_file}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
