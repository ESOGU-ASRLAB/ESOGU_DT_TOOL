"""
Test with a session that has test scenario or test case data
"""
import asyncio
import sys
sys.path.append('.')

from services.test_reporting_service import TestReportingService


async def test_with_data_rich_session():
    """Test quality metrics with a session containing actual test data"""
    print("\n" + "="*70)
    print("🔍 Finding Sessions with Test Scenario/Case Data")
    print("="*70)
    
    service = TestReportingService()
    await service.initialize()
    
    sessions = await service.fetch_available_sessions()
    
    # Find sessions with test_scenario_generation or test_case_generation
    target_processes = ['test_scenario_generation', 'test_case_generation']
    
    good_sessions = []
    for session in sessions:
        processes = session.get('processes', {})
        for target in target_processes:
            if target in processes:
                good_sessions.append((session, target))
                break
    
    if not good_sessions:
        print("❌ No sessions found with test scenario or test case data")
        return
    
    print(f"✅ Found {len(good_sessions)} sessions with test data\n")
    
    # Test first 3 sessions with data
    for i, (session, process_type) in enumerate(good_sessions[:3], 1):
        print("\n" + "="*70)
        print(f"Session {i}: {session.get('process_name', 'Unnamed')}")
        print("="*70)
        print(f"ID: {session['session_id'][:30]}...")
        print(f"Date: {session.get('timestamp', 'N/A')}")
        print(f"Contains: {process_type}")
        
        # Fetch and display quality metrics
        session_data = await service.fetch_session_data(session['session_id'])
        
        for proc_name, proc_data in session_data['processes'].items():
            if proc_name not in target_processes:
                continue
            
            quality = proc_data.get('quality_metrics', {})
            output = proc_data.get('output', {})
            
            if not quality or quality.get('score') == 5.0:
                print(f"\n⚠️  {proc_name}: Default score (no processable data)")
                continue
            
            print(f"\n📊 {proc_name.replace('_', ' ').title()}")
            print("-" * 70)
            print(f"✨ Overall Quality Score: {quality.get('score')}/10")
            print(f"\n   📈 Quality Breakdown:")
            print(f"      Completeness: {quality.get('completeness')}/10 ⭐")
            print(f"      Clarity:      {quality.get('clarity')}/10 ⭐")
            print(f"      Coverage:     {quality.get('coverage')}/10 ⭐")
            print(f"      Depth:        {quality.get('depth')}/10 ⭐")
            
            calc_details = quality.get('calculation_details', {})
            if calc_details:
                print(f"\n   🔬 Calculation Evidence:")
                for key, value in calc_details.items():
                    if isinstance(value, dict):
                        print(f"      • {key}:")
                        for k, v in value.items():
                            print(f"         - {k}: {v}")
                    else:
                        print(f"      • {key}: {value}")
            
            # Show data source
            if proc_name == 'test_scenario_generation':
                scenarios = output.get('test_scenarios', {}).get('TestScenarios', [])
                print(f"\n   📁 Data Source: {len(scenarios)} test scenarios")
                if scenarios:
                    print(f"      Sample: {scenarios[0].get('Title', 'N/A')[:50]}...")
            
            elif proc_name == 'test_case_generation':
                results = output.get('data', {}).get('test_case_results', [])
                total_cases = sum(len(r.get('test_cases', [])) for r in results)
                print(f"\n   📁 Data Source: {total_cases} test cases")
        
        print("\n" + "-"*70)
        input("\nPress Enter to see next session (or Ctrl+C to exit)...")


if __name__ == "__main__":
    try:
        asyncio.run(test_with_data_rich_session())
    except KeyboardInterrupt:
        print("\n\n✅ Test completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
