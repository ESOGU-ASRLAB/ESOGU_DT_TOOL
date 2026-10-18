"""
Debug script to check test_code_generation and test_execution data in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

async def check_data():
    """Check test_code_generation and test_execution data"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["stlc_database"]  # Changed from stlc_db to stlc_database
    collection = db["session_history"]
    
    print("=" * 80)
    print("CHECKING TEST_CODE_GENERATION AND TEST_EXECUTION DATA")
    print("=" * 80)
    
    # Find sessions with test_code_generation
    print("\n" + "=" * 80)
    print("SESSIONS WITH test_code_generation:")
    print("=" * 80)
    
    async for session in collection.find({"processes.test_code_generation": {"$exists": True}}):
        session_id = session.get("_id")
        created_at = session.get("created_at", "Unknown")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        print(f"\nSession ID: {session_id}")
        print(f"Created: {created_at}")
        
        test_code_gen = session.get("processes", {}).get("test_code_generation", {})
        print(f"\ntest_code_generation structure:")
        print(f"  Keys: {list(test_code_gen.keys())}")
        
        # Check input
        input_data = test_code_gen.get("input", {})
        if input_data:
            print(f"\n  Input keys: {list(input_data.keys())}")
            print(f"    process_title: {input_data.get('process_title')}")
            print(f"    model_name: {input_data.get('model_name')}")
        
        # Check output
        output_data = test_code_gen.get("output", {})
        if output_data:
            print(f"\n  Output keys: {list(output_data.keys())}")
            
            # Check for generated_tests
            generated_tests = output_data.get("generated_tests", [])
            if generated_tests:
                print(f"    generated_tests: {len(generated_tests)} items")
            
            # Check for data.generated_tests
            data = output_data.get("data", {})
            if data:
                print(f"    data keys: {list(data.keys())}")
                data_generated_tests = data.get("generated_tests", [])
                if data_generated_tests:
                    print(f"    data.generated_tests: {len(data_generated_tests)} items")
            
            # Check environment_info
            env_info = output_data.get("environment_info", {})
            if env_info:
                print(f"    environment_info: {env_info}")
        
        # Check status
        status = test_code_gen.get("status")
        model_used = test_code_gen.get("model_used")
        print(f"\n  status: {status}")
        print(f"  model_used: {model_used}")
    
    # Find sessions with test_execution
    print("\n" + "=" * 80)
    print("SESSIONS WITH test_execution:")
    print("=" * 80)
    
    async for session in collection.find({"processes.test_execution": {"$exists": True}}):
        session_id = session.get("_id")
        created_at = session.get("created_at", "Unknown")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        print(f"\nSession ID: {session_id}")
        print(f"Created: {created_at}")
        
        test_exec = session.get("processes", {}).get("test_execution", {})
        print(f"\ntest_execution structure:")
        print(f"  Keys: {list(test_exec.keys())}")
        
        # Check input
        input_data = test_exec.get("input", {})
        if input_data:
            print(f"\n  Input keys: {list(input_data.keys())}")
            print(f"    code_generation_process_name: {input_data.get('code_generation_process_name')}")
        
        # Check output
        output_data = test_exec.get("output", {})
        if output_data:
            print(f"\n  Output keys: {list(output_data.keys())}")
            
            # Check execution_results
            exec_results = output_data.get("execution_results", {})
            if exec_results:
                print(f"    execution_results:")
                print(f"      total_tests: {exec_results.get('total_tests')}")
                print(f"      passed: {exec_results.get('passed')}")
                print(f"      failed: {exec_results.get('failed')}")
                print(f"      success_rate: {exec_results.get('success_rate')}")
            
            # Check terminal_output
            terminal_output = output_data.get("terminal_output", "")
            if terminal_output:
                print(f"    terminal_output length: {len(terminal_output)} chars")
            
            # Check test_results
            test_results = output_data.get("test_results", [])
            if test_results:
                print(f"    test_results: {len(test_results)} items")
            
            # Check success
            success = output_data.get("success")
            print(f"    success: {success}")
        
        # Check status
        status = test_exec.get("status")
        model_used = test_exec.get("model_used")
        print(f"\n  status: {status}")
        print(f"  model_used: {model_used}")
    
    # Count total sessions
    total_sessions = await collection.count_documents({})
    with_test_code_gen = await collection.count_documents({"processes.test_code_generation": {"$exists": True}})
    with_test_exec = await collection.count_documents({"processes.test_execution": {"$exists": True}})
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total sessions: {total_sessions}")
    print(f"Sessions with test_code_generation: {with_test_code_gen}")
    print(f"Sessions with test_execution: {with_test_exec}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_data())
