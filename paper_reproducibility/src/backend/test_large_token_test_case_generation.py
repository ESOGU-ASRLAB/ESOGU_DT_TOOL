#!/usr/bin/env python3
"""
Test script for Test Case Generation with large token count to test model switching.
This tests the enhanced Test Case Generation with token-aware model selection.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_large_token_test_case_generation():
    """Test Test Case Generation with large content that exceeds token limits"""
    
    print("Testing Large Token Test Case Generation with Model Switching...")
    
    # Create large content that exceeds 4000 tokens
    large_content = """
    """
    
    # Repeat content to exceed token limit
    large_file_content = ""
    for i in range(50):  # Create substantial content
        large_file_content += f"""
        
        // Module {i+1}: Advanced Data Processing System
        class DataProcessor{i+1} {{
            private Map<String, Object> dataCache = new HashMap<>();
            private List<ValidationRule> validationRules = new ArrayList<>();
            private ExecutorService threadPool = Executors.newFixedThreadPool(10);
            
            /**
             * Complex data processing method with multiple validation layers
             * This method handles various data types and applies sophisticated algorithms
             */
            public ProcessingResult processData(DataInput input) {{
                // Step 1: Validate input data structure
                if (!validateInputStructure(input)) {{
                    throw new InvalidDataException("Input data structure validation failed");
                }}
                
                // Step 2: Apply preprocessing transformations
                DataTransformer transformer = new DataTransformer();
                TransformedData transformed = transformer.transform(input);
                
                // Step 3: Execute business logic rules
                BusinessRuleEngine ruleEngine = new BusinessRuleEngine();
                ValidationResult validationResult = ruleEngine.validate(transformed);
                
                if (!validationResult.isValid()) {{
                    logValidationFailure(validationResult);
                    return ProcessingResult.failure(validationResult.getErrors());
                }}
                
                // Step 4: Apply complex calculations
                CalculationEngine calculator = new CalculationEngine();
                CalculatedData calculated = calculator.compute(transformed);
                
                // Step 5: Store in cache for future use
                cacheData(input.getId(), calculated);
                
                // Step 6: Generate detailed processing report
                ProcessingReport report = generateDetailedReport(calculated);
                
                return ProcessingResult.success(calculated, report);
            }}
            
            private boolean validateInputStructure(DataInput input) {{
                return input != null && 
                       input.getId() != null && 
                       input.getData() != null &&
                       input.getMetadata() != null;
            }}
            
            private void logValidationFailure(ValidationResult result) {{
                Logger logger = LoggerFactory.getLogger(DataProcessor{i+1}.class);
                logger.error("Validation failed: {{}}", result.getErrors());
            }}
            
            private void cacheData(String id, CalculatedData data) {{
                dataCache.put(id, data);
                // Implement cache expiration logic
                scheduleCleanup(id);
            }}
            
            private ProcessingReport generateDetailedReport(CalculatedData data) {{
                ProcessingReport report = new ProcessingReport();
                report.setProcessingTime(System.currentTimeMillis());
                report.setDataQualityScore(calculateQualityScore(data));
                report.setRecommendations(generateRecommendations(data));
                return report;
            }}
        }}
        
        // Associated test scenarios and validation logic
        public class DataProcessor{i+1}Test {{
            @Test
            public void testValidDataProcessing() {{
                // Test with valid input data
                DataInput input = createValidInput();
                DataProcessor{i+1} processor = new DataProcessor{i+1}();
                ProcessingResult result = processor.processData(input);
                assertTrue(result.isSuccess());
            }}
            
            @Test
            public void testInvalidDataHandling() {{
                // Test with invalid input data
                DataInput input = createInvalidInput();
                DataProcessor{i+1} processor = new DataProcessor{i+1}();
                assertThrows(InvalidDataException.class, () -> {{
                    processor.processData(input);
                }});
            }}
        }}
        """
    
    # Test scenarios for test case generation  
    test_scenarios = [
        {
            "scenario_id": "TS_LARGE_001",
            "scenario": "Large Scale Data Processing and Validation",
            "description": "Test comprehensive data processing system with multiple validation layers and complex business rules",
            "objective": "Verify that the data processing system can handle large volumes of data while maintaining data integrity and performance",
            "category": "Performance"
        },
        {
            "scenario_id": "TS_LARGE_002", 
            "scenario": "Concurrent Data Processing and Error Handling",
            "description": "Test system behavior under concurrent load with various error conditions and recovery mechanisms",
            "objective": "Ensure system stability and proper error handling during high-load concurrent operations",
            "category": "Stress Testing"
        }
    ]
    
    # Files to include (large content)
    selected_files = [
        {
            "name": "DataProcessingSystem.java",
            "content": large_file_content
        },
        {
            "name": "ValidationEngine.java", 
            "content": large_file_content  # Duplicate to increase token count
        }
    ]
    
    # Count estimated tokens
    estimated_tokens = len(large_file_content.split()) * 2  # Approximate token count
    print(f"Estimated total tokens: {estimated_tokens}")
    
    # Request payload
    payload = {
        "selected_scenarios": test_scenarios,
        "process_prompt": "Generate comprehensive test cases for a large-scale data processing system. Focus on data validation, error handling, performance testing, and concurrent operations. Each test case should include detailed steps for testing complex business logic and data transformations.",
        "selected_files": selected_files,
        "ai_model": "llama3.2:3b",  # Start with normal model
        "session_id": f"test_large_token_{int(time.time())}",
        "selected_process_title": "Large Scale Data Processing Testing"
    }
    
    url = "http://localhost:8000/api/processes/test-scenario-generation/generate-test-cases"
    
    print(f"URL: {url}")
    print(f"Processing {len(test_scenarios)} scenarios")
    print(f"Files: {len(selected_files)} files with large content")
    print(f"AI Model: {payload['ai_model']}")
    print(f"Estimated total tokens: {estimated_tokens}")
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            
            async with session.post(url, json=payload) as response:
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"Response keys: {list(result.keys())}")
                    
                    if result.get('status') == 'success':
                        print("=== LARGE TOKEN TEST CASE RESULTS ===")
                        
                        test_case_results = result.get('test_case_results', [])
                        summary = result.get('summary', {})
                        
                        print(f"Total scenarios processed: {summary.get('scenarios_processed', 0)}")
                        print(f"Successful scenarios: {summary.get('successful_scenarios', 0)}")
                        print(f"Failed scenarios: {summary.get('failed_scenarios', 0)}")
                        print(f"Total test cases: {summary.get('total_test_cases', 0)}")
                        print(f"Model used: {summary.get('model_used', 'Unknown')}")
                        print(f"Processing time: {processing_time:.2f} seconds")
                        
                        # Check if model was switched due to token limit
                        if summary.get('model_used') == 'qwen2.5-7b-instruct-1m':
                            print("✅ Model automatically switched to high-capacity due to large content")
                        else:
                            print("⚠️ Model was not switched - check token limit logic")
                        
                        print("\n=== DETAILED RESULTS ===")
                        for i, scenario_result in enumerate(test_case_results):
                            print(f"\nScenario {i+1}: {scenario_result.get('scenario_id', 'Unknown')}")
                            print(f"  Title: {scenario_result.get('scenario_title', 'Unknown')}")
                            print(f"  Status: {scenario_result.get('status', 'Unknown')}")
                            
                            if scenario_result.get('status') == 'success':
                                test_cases = scenario_result.get('test_cases', [])
                                print(f"  Generated: {len(test_cases)} test cases")
                                
                                # Show first test case details
                                if test_cases:
                                    tc = test_cases[0]
                                    print(f"    TC1: {tc.get('Title', 'No title')}")
                                    print(f"         Category: {tc.get('Category', 'N/A')} | Priority: {tc.get('Priority', 'N/A')}")
                                    print(f"         Test Steps: {len(tc.get('TestSteps', []))} steps")
                                    
                                    # Check enhanced structure
                                    required_fields = ['ScenarioID', 'TestCaseID', 'Title', 'Description', 'Objective', 'Category', 'Comments']
                                    has_all_fields = all(field in tc for field in required_fields)
                                    print(f"         Enhanced Structure: {'✅' if has_all_fields else '❌'}")
                            else:
                                print(f"  Error: {scenario_result.get('error', 'Unknown error')}")
                        
                        # Token limit verification
                        TOKEN_LIMIT = 4000
                        if estimated_tokens > TOKEN_LIMIT:
                            print(f"\n✅ Large content test successful - exceeded {TOKEN_LIMIT} token limit")
                        else:
                            print(f"\n⚠️ Content was smaller than expected - {estimated_tokens} tokens")
                            
                    else:
                        print(f"❌ Request failed: {result.get('message', 'Unknown error')}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_large_token_test_case_generation())
