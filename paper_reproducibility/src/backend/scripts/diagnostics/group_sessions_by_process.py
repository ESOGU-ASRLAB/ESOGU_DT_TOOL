"""
Group Sessions by Process Title
Finds which sessions belong to the same test process
"""

import asyncio
import json
from core.database import get_database

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

async def find_and_group_sessions():
    """Find sessions and group by process_title or related metadata"""
    db = await get_database()
    collection = db["session_history"]
    
    sessions = []
    for pattern in SESSION_ID_PATTERNS:
        cursor = collection.find({"session_id": {"$regex": pattern}})
        found = await cursor.to_list(length=None)
        sessions.extend(found)
    
    # Remove duplicates
    unique_sessions = {}
    for session in sessions:
        session_id = session.get("session_id")
        if session_id not in unique_sessions:
            unique_sessions[session_id] = session
    
    sessions = list(unique_sessions.values())
    
    print(f"\n{'='*100}")
    print(f"📦 SESSION GROUPING ANALYSIS")
    print(f"{'='*100}\n")
    
    # Group by process_title
    by_process_title = {}
    orphans = []
    
    for session in sessions:
        session_id = session.get("session_id")
        process_title = session.get("process_title")
        processes = session.get("processes", {})
        
        print(f"\n{'='*100}")
        print(f"Session: {session_id}")
        print(f"{'='*100}")
        print(f"Process Title: {process_title}")
        print(f"Processes: {list(processes.keys())}")
        
        # Check for metadata that might link sessions
        metadata_keys = []
        for proc_name, proc_data in processes.items():
            if isinstance(proc_data, dict):
                if "selected_process_title" in proc_data:
                    spt = proc_data["selected_process_title"]
                    print(f"   {proc_name} -> selected_process_title: {spt}")
                    metadata_keys.append(spt)
                
                output = proc_data.get("output", {})
                if isinstance(output, dict):
                    meta = output.get("metadata", {})
                    if isinstance(meta, dict):
                        if "session_id" in meta:
                            print(f"   {proc_name} -> metadata.session_id: {meta['session_id']}")
        
        if process_title:
            if process_title not in by_process_title:
                by_process_title[process_title] = []
            by_process_title[process_title].append(session_id)
        else:
            orphans.append(session_id)
    
    # Print groupings
    print(f"\n\n{'='*100}")
    print(f"📊 GROUPING RESULTS")
    print(f"{'='*100}\n")
    
    if by_process_title:
        print(f"✅ Sessions Grouped by Process Title:\n")
        for title, session_ids in by_process_title.items():
            print(f"   📁 {title}")
            print(f"      Sessions: {len(session_ids)}")
            for sid in session_ids:
                print(f"         - {sid}")
            print()
    
    if orphans:
        print(f"⚠️  Orphan Sessions (no process_title): {len(orphans)}\n")
        for sid in orphans:
            print(f"   - {sid}")
    
    # Analysis
    print(f"\n{'='*100}")
    print(f"💡 ANALYSIS & RECOMMENDATIONS")
    print(f"{'='*100}\n")
    
    print("These sessions appear to be individual STLC steps, not complete workflows.")
    print("For comprehensive Test Reporting and Test Closure, you should:")
    print()
    print("1. ✅ Select sessions that belong to the same process_title")
    print("2. ✅ Or manually select complementary sessions that form a complete flow:")
    print("      - Test Scenario Generation session(s)")
    print("      - Test Case Generation session(s)")
    print("      - Test Case Optimization session(s)")
    print("      - Test Execution session(s)")
    print()
    print("3. 📊 Current compatible sessions for reporting/closure:")
    print("      - 129793d5 (has test scenarios)")
    print("      - bd39408b (has test scenarios)")
    print("      - project.xml (has test scenarios + test cases)")
    print()
    print("4. 🔄 To get a complete STLC view, combine multiple sessions:")
    print("      Example: Use project.xml + test-exec-20260111 together")
    print()

async def main():
    await find_and_group_sessions()

if __name__ == "__main__":
    asyncio.run(main())
