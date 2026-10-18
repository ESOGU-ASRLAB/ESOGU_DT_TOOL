"""
check_closure_sessions.py
--------------------------
Quick script to check test_closure sessions in MongoDB
"""

import asyncio
from core.database import get_database
import json

async def check_closure_sessions():
    db = await get_database()
    collection = db["session_history"]
    
    print("\n" + "=" * 80)
    print("TEST CLOSURE SESSIONS IN DATABASE")
    print("=" * 80)
    
    # Find all test_closure sessions
    closure_sessions = await collection.find({"session_type": "test_closure"}).to_list(length=100)
    
    print(f"\n📊 Total test_closure sessions: {len(closure_sessions)}\n")
    
    for idx, session in enumerate(closure_sessions, 1):
        print(f"{idx}. Session ID: {session['session_id']}")
        print(f"   Created: {session['created_at']}")
        print(f"   Process: {session['process_name']}")
        
        metadata = session.get('closure_metadata', {})
        print(f"   Model: {metadata.get('model_used', 'N/A')}")
        print(f"   Provider: {metadata.get('provider', 'N/A')}")
        print(f"   Sessions Analyzed: {metadata.get('session_count', 0)}")
        
        # Quality evaluation
        processes = session.get('processes', {})
        if 'test_closure' in processes:
            output = processes['test_closure'].get('output', {})
            quality = output.get('quality_evaluation', {})
            print(f"   Quality Score: {quality.get('overall_score', 0):.4f}")
            print(f"   - Completeness: {quality.get('completeness', 0):.4f}")
            print(f"   - Depth: {quality.get('depth', 0):.4f}")
            print(f"   - Clarity: {quality.get('clarity', 0):.4f}")
            print(f"   Report Length: {output.get('report_length', 0)} chars")
        
        print()
    
    # Show detailed view of latest session
    if closure_sessions:
        print("=" * 80)
        print("LATEST SESSION DETAILS (JSON)")
        print("=" * 80)
        latest = closure_sessions[-1]
        # Remove large content for readability
        if 'processes' in latest and 'test_closure' in latest['processes']:
            if 'output' in latest['processes']['test_closure']:
                latest['processes']['test_closure']['output']['report_content'] = "[...truncated...]"
            if 'input' in latest['processes']['test_closure']:
                if 'aggregated_metrics' in latest['processes']['test_closure']['input']:
                    latest['processes']['test_closure']['input']['aggregated_metrics'] = "[...truncated...]"
        
        print(json.dumps(latest, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("✅ Check completed")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(check_closure_sessions())
