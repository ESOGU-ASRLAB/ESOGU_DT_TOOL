#!/usr/bin/env python3
"""Check E2E test session data in MongoDB"""

import sys
import json
from core.database import get_database

async def check_session():
    db = await get_database()
    
    # Find session by ID
    session_id = "00f19689-6ae0-4eda-bceb-2c476b084534"
    session = await db.session_history.find_one({"session_id": session_id})
    
    if not session:
        print(f"❌ Session {session_id} not found")
        return
    
    print(f"✅ Session found: {session_id}")
    print(f"\n📊 Session structure:")
    print(json.dumps(session, indent=2, default=str))
    
    # Check processes
    if "processes" in session:
        print(f"\n🔍 Processes in session:")
        for proc_type, proc_data in session["processes"].items():
            print(f"   - {proc_type}: {type(proc_data)}")
            if isinstance(proc_data, dict):
                for key in proc_data.keys():
                    print(f"     - {key}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_session())
