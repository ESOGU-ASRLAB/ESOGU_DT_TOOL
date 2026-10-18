#!/usr/bin/env python3
"""
Initialize Test Scenario Generation Database Collections
-------------------------------------------------------
Creates enhanced database schema for comprehensive Test Scenario Generation tracking
"""

from pymongo import MongoClient
from datetime import datetime
import json

def initialize_test_scenario_collections():
    """Initialize enhanced collections for Test Scenario Generation tracking"""
    
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017')
    db = client['stlc_database']
    
    print("🗄️ Initializing Test Scenario Generation Database Collections...")
    
    # 1. Enhanced Session History (already exists, but ensuring indexes)
    print("📊 Setting up session_history indexes...")
    session_collection = db['session_history']
    
    # Create indexes for better query performance
    session_collection.create_index("session_id")
    session_collection.create_index("processes.test_scenario_generation.timestamp")
    session_collection.create_index([("processes.test_scenario_generation.output.metadata.test_type", 1)])
    
    # 2. Test Scenario Generation Analytics Collection
    print("📈 Creating test_scenario_analytics collection...")
    analytics_collection = db['test_scenario_analytics']
    
    # Sample analytics document structure
    analytics_sample = {
        "session_id": "example_session_123",
        "process_type": "test_scenario_generation",
        "timestamp": datetime.now(),
        "test_metadata": {
            "test_type": "Functional Testing",
            "test_category": "Functional",
            "scoring_elements": ["Test Coverage", "Risk Assessment"],
            "instruction_elements": ["Follow ISTQB Standards"]
        },
        "generation_analytics": {
            "total_scenarios_generated": 8,
            "generation_method": "json_parse",
            "model_used": "llama3.2:3b",
            "model_fallback_required": False,
            "processing_time_seconds": 45.2,
            "token_usage": {
                "input_tokens": 1250,
                "output_tokens": 2800,
                "total_tokens": 4050
            }
        },
        "file_analysis": {
            "files_processed": 3,
            "total_file_size": 15000,
            "file_types": ["python", "requirements", "documentation"],
            "context_included": True
        },
        "quality_metrics": {
            "response_quality_score": 0.95,
            "json_parse_success": True,
            "scenario_completeness_score": 0.88,
            "coverage_score": 0.92
        },
        "prompt_metadata": {
            "prompt_generation_session_id": "prompt_session_456",
            "base_prompt_modified": False,
            "custom_prompt_generated": True,
            "final_prompt_length": 2500
        }
    }
    
    # Insert sample document if collection is empty
    if analytics_collection.count_documents({}) == 0:
        analytics_collection.insert_one(analytics_sample)
        print("✅ Sample analytics document inserted")
    
    # Create indexes for analytics
    analytics_collection.create_index("session_id")
    analytics_collection.create_index("test_metadata.test_type")
    analytics_collection.create_index("timestamp")
    analytics_collection.create_index("generation_analytics.total_scenarios_generated")
    
    # 3. Test Scenario Quality Tracking Collection
    print("🎯 Creating test_scenario_quality collection...")
    quality_collection = db['test_scenario_quality']
    
    quality_sample = {
        "session_id": "example_session_123",
        "scenario_id": "TS_001",
        "timestamp": datetime.now(),
        "scenario_data": {
            "title": "User Login Functionality Test",
            "description": "Comprehensive test for user authentication",
            "category": "Functional",
            "test_type": "Integration Testing"
        },
        "quality_assessment": {
            "completeness_score": 0.9,
            "clarity_score": 0.85,
            "testability_score": 0.92,
            "istqb_compliance_score": 0.88
        },
        "validation_flags": {
            "has_clear_objective": True,
            "has_prerequisites": True,
            "has_test_steps": True,
            "has_expected_results": True,
            "follows_naming_convention": True
        }
    }
    
    if quality_collection.count_documents({}) == 0:
        quality_collection.insert_one(quality_sample)
        print("✅ Sample quality document inserted")
    
    # Create indexes for quality collection
    quality_collection.create_index("session_id")
    quality_collection.create_index("scenario_id")
    quality_collection.create_index("timestamp")
    
    # 4. Enhanced Prompt Generation Sessions (extending existing)
    print("🧠 Enhancing prompt_generation_sessions collection...")
    prompt_collection = db['prompt_generation_sessions']
    
    # Create additional indexes
    prompt_collection.create_index("test_type")
    prompt_collection.create_index("test_category")
    prompt_collection.create_index("files_analyzed.file_type")
    
    # 5. File Processing History for Test Scenarios
    print("📁 Creating test_scenario_file_history collection...")
    file_history_collection = db['test_scenario_file_history']
    
    file_history_sample = {
        "session_id": "example_session_123",
        "timestamp": datetime.now(),
        "files_processed": [
            {
                "file_name": "main.py",
                "file_type": "python",
                "file_size": 2500,
                "content_analyzed": True,
                "tokens_extracted": 450,
                "analysis_quality": 0.85
            },
            {
                "file_name": "requirements.txt",
                "file_type": "requirements",
                "file_size": 500,
                "content_analyzed": True,
                "tokens_extracted": 100,
                "analysis_quality": 0.90
            }
        ],
        "processing_summary": {
            "total_files": 2,
            "successful_processing": 2,
            "total_tokens_extracted": 550,
            "total_content_size": 3000,
            "context_relevance_score": 0.87
        }
    }
    
    if file_history_collection.count_documents({}) == 0:
        file_history_collection.insert_one(file_history_sample)
        print("✅ Sample file history document inserted")
    
    file_history_collection.create_index("session_id")
    file_history_collection.create_index("timestamp")
    
    print("🎉 Test Scenario Generation Database Collections Initialized Successfully!")
    
    # Summary
    print("\n📋 SUMMARY OF COLLECTIONS:")
    print("1. session_history - Main process execution records (enhanced indexes)")
    print("2. test_scenario_analytics - Comprehensive generation analytics")
    print("3. test_scenario_quality - Individual scenario quality metrics")
    print("4. prompt_generation_sessions - Enhanced prompt generation tracking")
    print("5. test_scenario_file_history - File processing and analysis tracking")
    
    print(f"\n📊 Current Collection Counts:")
    print(f"session_history: {db['session_history'].count_documents({})}")
    print(f"test_scenario_analytics: {analytics_collection.count_documents({})}")
    print(f"test_scenario_quality: {quality_collection.count_documents({})}")
    print(f"prompt_generation_sessions: {db['prompt_generation_sessions'].count_documents({})}")
    print(f"test_scenario_file_history: {file_history_collection.count_documents({})}")
    
    client.close()

if __name__ == "__main__":
    initialize_test_scenario_collections()
