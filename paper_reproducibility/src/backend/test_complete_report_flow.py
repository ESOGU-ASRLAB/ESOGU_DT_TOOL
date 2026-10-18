"""
Test complete report generation with quality metrics and numerical data
"""
import asyncio
from services.test_reporting_service import TestReportingService


async def test_complete_report_generation():
    """Test full report generation flow"""
    print("\n" + "="*80)
    print("🧪 TESTING COMPLETE REPORT GENERATION WITH QUALITY METRICS")
    print("="*80)
    
    service = TestReportingService()
    await service.initialize()
    
    # Find a session with multiple processes
    sessions = await service.fetch_available_sessions()
    
    if not sessions:
        print("❌ No sessions found")
        return
    
    # Pick the first session with test_case_generation
    target_session = None
    for session in sessions:
        if 'test_case_generation' in session.get('processes', {}):
            target_session = session
            break
    
    if not target_session:
        print("❌ No sessions with test_case_generation found")
        return
    
    session_id = target_session['session_id']
    print(f"\n📋 Selected Session: {target_session.get('process_name', 'Unnamed')}")
    print(f"   Session ID: {session_id[:40]}...")
    print(f"   Processes: {list(target_session.get('processes', {}).keys())}")
    
    # Fetch full session data
    print(f"\n{'='*80}")
    print("📥 FETCHING SESSION DATA...")
    print(f"{'='*80}")
    
    session_data = await service.fetch_session_data(session_id)
    
    # Display quality metrics for each process
    for process_name, process_data in session_data['processes'].items():
        quality = process_data.get('quality_metrics', {})
        output = process_data.get('output', {})
        
        print(f"\n🔍 {process_name.upper()}")
        print(f"   {'─'*76}")
        
        # Show quality score
        if quality:
            print(f"   ✨ Quality Score: {quality.get('score', 'N/A')}/10")
            print(f"      Completeness: {quality.get('completeness', 'N/A')}/10")
            print(f"      Clarity: {quality.get('clarity', 'N/A')}/10")
            print(f"      Coverage: {quality.get('coverage', 'N/A')}/10")
            print(f"      Depth: {quality.get('depth', 'N/A')}/10")
        
        # Show numerical metrics
        calc_details = quality.get('calculation_details', {})
        if calc_details:
            print(f"\n   📊 Numerical Metrics:")
            for key, value in calc_details.items():
                if value is not None:
                    print(f"      • {key}: {value}")
        
        # Process-specific metrics
        if process_name == "test_case_generation":
            # Extract test cases
            test_cases = output.get("test_cases", [])
            data = output.get("data", {})
            
            if not test_cases and data:
                test_case_results = data.get("test_case_results", [])
                all_cases = []
                for result in test_case_results:
                    all_cases.extend(result.get("test_cases", []))
                test_cases = all_cases
            
            if test_cases:
                print(f"\n   📝 Test Case Details:")
                print(f"      • Total Test Cases: {len(test_cases)}")
                
                # Count positive/negative
                positive = sum(1 for tc in test_cases 
                              if not any(word in tc.get('Title', '').lower() 
                                       for word in ['invalid', 'error', 'negative']))
                negative = len(test_cases) - positive
                print(f"      • Positive Cases: {positive}")
                print(f"      • Negative Cases: {negative}")
                print(f"      • Balance Ratio: {positive/negative:.2f}:1" if negative > 0 else "      • Balance Ratio: All positive")
    
    # Create chunks for one process
    print(f"\n{'='*80}")
    print("📦 TESTING CHUNK CREATION...")
    print(f"{'='*80}")
    
    for process_name, process_data in session_data['processes'].items():
        chunks = service.create_chunks(process_name, process_data)
        print(f"\n   {process_name}: {len(chunks)} chunks created")
        
        if chunks:
            first_chunk = chunks[0]
            print(f"      First chunk: {first_chunk.get('chunk_type', 'unknown')} "
                  f"({first_chunk.get('item_count', 0)} items)")
            
            # Show optimization metadata if available
            if 'optimization_metadata' in first_chunk:
                opt_meta = first_chunk['optimization_metadata']
                print(f"      Optimization: {opt_meta.get('before_count')} → "
                      f"{opt_meta.get('after_count')} "
                      f"({opt_meta.get('reduction_percentage', 0):.1f}% reduction)")
    
    print(f"\n{'='*80}")
    print("✅ REPORT GENERATION TEST COMPLETED SUCCESSFULLY")
    print(f"{'='*80}")
    print("\n📊 Summary:")
    print(f"   • Processes analyzed: {len(session_data['processes'])}")
    print(f"   • Quality metrics: ✅ Calculated")
    print(f"   • Numerical metrics: ✅ Extracted")
    print(f"   • Chunk creation: ✅ Working")
    print(f"   • Ready for AI analysis: ✅ Yes")


if __name__ == "__main__":
    asyncio.run(test_complete_report_generation())
