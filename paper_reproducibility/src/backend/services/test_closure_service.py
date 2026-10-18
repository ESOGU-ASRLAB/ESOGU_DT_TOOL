"""
test_closure_service.py
-----------------------
Test Closure Service - AI-Powered Test Cycle Closure Report Generation
Aggregates all STLC process data and generates comprehensive closure reports
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from core.database import get_database
from services.report_quality_evaluator import ReportQualityEvaluator

logger = logging.getLogger(__name__)


class TestClosureService:
    """
    Service for generating AI-powered test closure reports
    Aggregates data from all STLC processes and creates comprehensive closure analysis
    Includes chunking support for large datasets
    """
    
    # Chunk sizes for large data aggregation
    CHUNK_SIZES = {
        "test_scenarios": 50,
        "test_cases": 100,
        "test_execution": 50,
        "defects": 30,
        "default": 50
    }
    
    MAX_CHUNK_CHARS = 80000  # Maximum characters per chunk
    
    def __init__(self):
        self.db = None
    
    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()
    
    def _should_chunk_data(self, metrics: Dict[str, Any]) -> bool:
        """
        Determine if data should be chunked based on size
        
        Args:
            metrics: Aggregated metrics dictionary
            
        Returns:
            True if chunking is needed, False otherwise
        """
        # Check total sessions
        if metrics.get("total_sessions", 0) > 10:
            return True
        
        # Check test scenarios count
        if metrics.get("test_scenarios", {}).get("total", 0) > self.CHUNK_SIZES["test_scenarios"]:
            return True
        
        # Check test cases count
        if metrics.get("test_cases", {}).get("total_generated", 0) > self.CHUNK_SIZES["test_cases"]:
            return True
        
        # Check test execution count
        if metrics.get("test_execution", {}).get("total_executed", 0) > self.CHUNK_SIZES["test_execution"]:
            return True
        
        # Check failed tests (potential defects)
        if len(metrics.get("defects", {}).get("from_failed_tests", [])) > self.CHUNK_SIZES["defects"]:
            return True
        
        return False
    
    def _create_chunked_summary(self, metrics: Dict[str, Any]) -> str:
        """
        Create a summarized version of metrics for chunked data
        
        Args:
            metrics: Full metrics dictionary
            
        Returns:
            Summarized text suitable for AI processing
        """
        summary = f"""# CHUNKED DATA SUMMARY (Large Dataset)
        
**Note**: Due to the large volume of data, detailed information has been aggregated and summarized.

## Overview
- Total Sessions: {metrics['total_sessions']}
- Date Range: {metrics['date_range']['start']} to {metrics['date_range']['end']}
- Models Used: {', '.join(metrics['models_used'])}

## Test Scenarios Summary
- Total Scenarios: {metrics['test_scenarios']['total']}
- Top Categories: {', '.join(list(metrics['test_scenarios']['by_category'].keys())[:5])}
- Top Types: {', '.join(list(metrics['test_scenarios']['by_type'].keys())[:5])}

## Test Cases Summary
- Total Generated: {metrics['test_cases']['total_generated']}
- Total Optimized: {metrics['test_cases']['total_optimized']}
- Optimization Rate: {metrics['test_cases']['optimization_rate']}%

## Test Execution Summary
- Total Executed: {metrics['test_execution']['total_executed']}
- Passed: {metrics['test_execution']['passed']} ({metrics['test_execution']['pass_rate']}%)
- Failed: {metrics['test_execution']['failed']}
- Skipped: {metrics['test_execution']['skipped']}

## Defect Summary
- Total Defects: {metrics['defects']['total']}
- Critical: {metrics['defects']['critical']}
- Major: {metrics['defects']['major']}
- Minor: {metrics['defects']['minor']}
- Sample Failed Tests: {len(metrics['defects']['from_failed_tests'][:10])} shown out of {len(metrics['defects']['from_failed_tests'])} total

**Analysis Focus**: This large-scale test cycle requires high-level analysis focusing on:
1. Overall trends and patterns across {metrics['total_sessions']} sessions
2. Statistical significance of pass rate ({metrics['test_execution']['pass_rate']}%)
3. Defect clustering and criticality assessment
4. Coverage and optimization effectiveness at scale
5. Resource utilization and efficiency metrics
"""
        return summary
    
    async def fetch_sessions_for_closure(
        self,
        session_ids: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch sessions for test closure analysis
        
        Args:
            session_ids: Specific session IDs to include
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            
        Returns:
            List of session documents
        """
        await self.initialize()
        collection = self.db["session_history"]
        
        # Build query
        query = {}
        
        if session_ids:
            query["session_id"] = {"$in": session_ids}
        
        if date_from or date_to:
            query["created_at"] = {}
            if date_from:
                query["created_at"]["$gte"] = date_from
            if date_to:
                query["created_at"]["$lte"] = date_to
        
        # Fetch sessions
        cursor = collection.find(query).sort("created_at", -1)
        sessions = await cursor.to_list(length=None)
        
        return sessions
    
    def aggregate_test_metrics(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate test execution metrics from sessions
        
        Returns comprehensive metrics including:
        - Test scenario counts
        - Test case counts
        - Execution results (pass/fail)
        - Coverage metrics
        - Defect analysis
        """
        metrics = {
            "total_sessions": len(sessions),
            "test_scenarios": {
                "total": 0,
                "by_type": {},
                "by_category": {}
            },
            "test_cases": {
                "total_generated": 0,
                "total_optimized": 0,
                "optimization_rate": 0,
                "by_scenario": {}
            },
            "test_execution": {
                "total_executed": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "pass_rate": 0,
                "execution_time": 0
            },
            "coverage": {
                "scenario_coverage": 0,
                "requirement_coverage": 0,
                "code_coverage": "N/A"
            },
            "defects": {
                "total": 0,
                "critical": 0,
                "major": 0,
                "minor": 0,
                "from_failed_tests": []
            },
            "effort": {
                "test_planning": 0,
                "test_design": 0,
                "test_execution": 0,
                "total_hours": 0
            },
            "models_used": set(),
            "session_ids": [],
            "date_range": {
                "start": None,
                "end": None
            }
        }
        
        # Process each session
        for session in sessions:
            session_id = session.get("session_id", "unknown")
            metrics["session_ids"].append(session_id)
            
            # Update date range
            created_at = session.get("created_at")
            if created_at:
                # Normalize created_at to string for consistent comparison
                if isinstance(created_at, datetime):
                    created_at = created_at.isoformat()
                elif not isinstance(created_at, str):
                    created_at = str(created_at)
                
                if not metrics["date_range"]["start"] or created_at < metrics["date_range"]["start"]:
                    metrics["date_range"]["start"] = created_at
                if not metrics["date_range"]["end"] or created_at > metrics["date_range"]["end"]:
                    metrics["date_range"]["end"] = created_at
            
            processes = session.get("processes", {})
            
            # Aggregate Test Scenario Generation
            if "test_scenario_generation" in processes:
                tsg = processes["test_scenario_generation"]
                output = tsg.get("output", {})
                
                # Track model used
                model = tsg.get("used_model")
                if model:
                    metrics["models_used"].add(model)
                
                # Count scenarios
                test_scenarios = output.get("test_scenarios", {})
                scenarios = test_scenarios.get("TestScenarios", [])
                metrics["test_scenarios"]["total"] += len(scenarios)
                
                # Count by type and category
                test_type = output.get("metadata", {}).get("test_type", "Unknown")
                test_category = output.get("metadata", {}).get("test_category", "Unknown")
                
                metrics["test_scenarios"]["by_type"][test_type] = \
                    metrics["test_scenarios"]["by_type"].get(test_type, 0) + len(scenarios)
                
                for scenario in scenarios:
                    category = scenario.get("Category", "Unknown")
                    metrics["test_scenarios"]["by_category"][category] = \
                        metrics["test_scenarios"]["by_category"].get(category, 0) + 1
            
            # Aggregate Test Case Generation
            if "test_case_generation" in processes:
                tcg = processes["test_case_generation"]
                output = tcg.get("output", {})
                
                # Track model used
                model = tcg.get("used_model")
                if model:
                    metrics["models_used"].add(model)
                
                # Count test cases - support multiple data structures
                # Structure 1: output['test_case_results'] (direct)
                test_case_results = output.get("test_case_results", [])
                
                # Structure 2: output['data']['test_case_results'] (nested in data)
                if not test_case_results:
                    data = output.get("data", {})
                    test_case_results = data.get("test_case_results", [])
                
                for result in test_case_results:
                    test_cases = result.get("test_cases", [])
                    metrics["test_cases"]["total_generated"] += len(test_cases)
                    
                    # Track by scenario
                    scenario_id = result.get("scenario_id", "unknown")
                    if scenario_id not in metrics["test_cases"]["by_scenario"]:
                        metrics["test_cases"]["by_scenario"][scenario_id] = {
                            "generated": 0,
                            "optimized": 0
                        }
                    metrics["test_cases"]["by_scenario"][scenario_id]["generated"] += len(test_cases)
            
            # Aggregate Test Case Optimization
            if "test_case_optimization" in processes:
                tco = processes["test_case_optimization"]
                output = tco.get("output", {})
                
                # Track model used
                model = tco.get("used_model")
                if model:
                    metrics["models_used"].add(model)
                
                # Count optimized test cases
                optimized_test_cases = output.get("optimized_test_cases", [])
                metrics["test_cases"]["total_optimized"] += len(optimized_test_cases)
            
            # Aggregate Test Code Generation
            if "test_code_generation" in processes:
                tcg = processes["test_code_generation"]
                
                # Track model used
                model = tcg.get("used_model")
                if model:
                    metrics["models_used"].add(model)
            
            # Aggregate Test Execution
            if "test_execution" in processes:
                te = processes["test_execution"]
                output = te.get("output", {})
                
                # Track model used
                model = te.get("used_model")
                if model:
                    metrics["models_used"].add(model)
                
                # Parse execution results
                terminal_output = output.get("terminal_output", "")
                execution_results = self._parse_execution_results(terminal_output)
                
                metrics["test_execution"]["total_executed"] += execution_results["total"]
                metrics["test_execution"]["passed"] += execution_results["passed"]
                metrics["test_execution"]["failed"] += execution_results["failed"]
                metrics["test_execution"]["skipped"] += execution_results["skipped"]
                
                # Track failed tests as defects
                for failed_test in execution_results["failed_tests"]:
                    metrics["defects"]["from_failed_tests"].append({
                        "session_id": session_id,
                        "test_name": failed_test,
                        "severity": "major"  # Default severity
                    })
            
            # Aggregate Test Reporting
            if "test_reporting" in processes:
                tr = processes["test_reporting"]
                
                # Track model used
                model = tr.get("used_model")
                if model:
                    metrics["models_used"].add(model)
        
        # Calculate derived metrics
        if metrics["test_cases"]["total_generated"] > 0:
            metrics["test_cases"]["optimization_rate"] = round(
                (metrics["test_cases"]["total_optimized"] / metrics["test_cases"]["total_generated"]) * 100, 
                2
            )
        
        if metrics["test_execution"]["total_executed"] > 0:
            metrics["test_execution"]["pass_rate"] = round(
                (metrics["test_execution"]["passed"] / metrics["test_execution"]["total_executed"]) * 100,
                2
            )
        
        # Defect counts from failed tests
        metrics["defects"]["total"] = len(metrics["defects"]["from_failed_tests"])
        metrics["defects"]["major"] = len(metrics["defects"]["from_failed_tests"])  # All failures as major by default
        
        # Coverage calculation
        if metrics["test_scenarios"]["total"] > 0:
            metrics["coverage"]["scenario_coverage"] = 100  # Assuming all scenarios are covered
        
        # Convert set to list for JSON serialization
        metrics["models_used"] = list(metrics["models_used"])
        
        return metrics
    
    def _parse_execution_results(self, terminal_output: str) -> Dict[str, Any]:
        """
        Parse test execution terminal output to extract results
        
        Returns:
            Dictionary with execution statistics
        """
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "failed_tests": []
        }
        
        if not terminal_output:
            return results
        
        # Try to parse pytest output
        import re
        
        # Look for pytest summary line: "X passed, Y failed, Z skipped"
        summary_pattern = r'(\d+)\s+passed'
        failed_pattern = r'(\d+)\s+failed'
        skipped_pattern = r'(\d+)\s+skipped'
        
        passed_match = re.search(summary_pattern, terminal_output)
        failed_match = re.search(failed_pattern, terminal_output)
        skipped_match = re.search(skipped_pattern, terminal_output)
        
        if passed_match:
            results["passed"] = int(passed_match.group(1))
        if failed_match:
            results["failed"] = int(failed_match.group(1))
        if skipped_match:
            results["skipped"] = int(skipped_match.group(1))
        
        results["total"] = results["passed"] + results["failed"] + results["skipped"]
        
        # Extract failed test names
        failed_test_pattern = r'FAILED\s+([\w\.\:\/]+)'
        failed_tests = re.findall(failed_test_pattern, terminal_output)
        results["failed_tests"] = failed_tests
        
        return results
    
    def generate_closure_prompt(self, metrics: Dict[str, Any]) -> str:
        """
        Generate AI prompt for test closure report with standards compliance
        Includes intelligent chunking for large datasets
        
        Args:
            metrics: Aggregated test metrics
            
        Returns:
            Formatted prompt string
        """
        # Check if data should be chunked
        use_chunking = self._should_chunk_data(metrics)
        
        if use_chunking:
            logger.info(f"[TestClosure] Large dataset detected, using chunked summary approach")
            data_summary = self._create_chunked_summary(metrics)
        else:
            logger.info(f"[TestClosure] Standard dataset size, using full detail approach")
            data_summary = f"""# TEST EXECUTION SUMMARY (IEEE 829-2008 Aligned)

## Test Scenarios (ISTQB Test Design)
- Total Scenarios Generated: {metrics['test_scenarios']['total']}
- Scenarios by Type: {json.dumps(metrics['test_scenarios']['by_type'], indent=2)}
- Scenarios by Category: {json.dumps(metrics['test_scenarios']['by_category'], indent=2)}

## Test Cases (ISTQB Foundation - Test Design Techniques)
- Total Test Cases Generated: {metrics['test_cases']['total_generated']}
- Total Test Cases Optimized: {metrics['test_cases']['total_optimized']}
- Optimization Rate: {metrics['test_cases']['optimization_rate']}%

## Test Execution Results (IEEE 829 Test Summary Report)
- Total Tests Executed: {metrics['test_execution']['total_executed']}
- Passed: {metrics['test_execution']['passed']} ({metrics['test_execution']['pass_rate']}%)
- Failed: {metrics['test_execution']['failed']}
- Skipped: {metrics['test_execution']['skipped']}

## Coverage Analysis (ISTQB Test Manager - Coverage Criteria)
- Scenario Coverage: {metrics['coverage']['scenario_coverage']}%
- Requirement Coverage: {metrics['coverage']['requirement_coverage']}%

## Defect Summary (ISTQB Defect Management)
- Total Defects Identified: {metrics['defects']['total']}
- Critical: {metrics['defects']['critical']}
- Major: {metrics['defects']['major']}
- Minor: {metrics['defects']['minor']}

# FAILED TESTS (Potential Defects)
{json.dumps(metrics['defects']['from_failed_tests'][:10], indent=2)}
"""
        
        prompt = f"""You are an ISTQB-certified Test Manager generating a comprehensive Test Closure Report aligned with international testing standards.

# INTERNATIONAL TESTING STANDARDS COMPLIANCE

This Test Closure Report is generated in full compliance with the following globally recognized testing standards and best practices:

## Primary Standards Framework

### 1. **ISO/IEC/IEEE 29119-3:2013** - Software Testing Standard (Part 3: Test Documentation)
   - **Scope**: International standard for test documentation templates and formats
   - **Application**: Test Closure Report structure, content organization, and quality criteria
   - **Reference**: ISO/IEC/IEEE 29119-3:2013(E) Section 8 - Test Completion Report Template
   - **URL**: https://www.iso.org/standard/56736.html

### 2. **IEEE 829-2008** - Standard for Software and System Test Documentation
   - **Scope**: IEEE standard for software test documentation (superseded by IEEE 29119 but still widely referenced)
   - **Application**: Test Summary Report format, metrics definition, and anomaly reporting
   - **Reference**: IEEE Std 829-2008 Section 9 - Test Summary Report
   - **URL**: https://standards.ieee.org/standard/829-2008.html

### 3. **ISTQB Foundation Level Syllabus v4.0 (2023)**
   - **Scope**: International Software Testing Qualifications Board - Foundation certification
   - **Application**: Fundamental testing principles, test design techniques, and test process best practices
   - **Reference**: ISTQB-CTFL Syllabus v4.0 - Chapters 4 (Test Analysis & Design) and 5 (Managing Testing)
   - **URL**: https://www.istqb.org/certifications/certified-tester-foundation-level

### 4. **ISTQB Test Manager (Advanced Level) 2012**
   - **Scope**: Advanced certification for test managers and test leads
   - **Application**: Test planning, monitoring, control, reporting, and risk-based testing
   - **Reference**: ISTQB-CTAL-TM Syllabus 2012 - Chapters on Test Process Improvement and Metrics
   - **URL**: https://www.istqb.org/certifications/test-manager

## Supplementary References

### 5. **ISTQB Agile Tester Extension**
   - **Application**: Agile testing principles where applicable
   - **URL**: https://www.istqb.org/certifications/agile-tester

### 6. **ISO 25010:2011** - Systems and software Quality Requirements and Evaluation (SQuaRE)
   - **Application**: Quality characteristics and software quality model
   - **URL**: https://www.iso.org/standard/35733.html

---

## Standards Alignment Table

| Standard | Version | Purpose | Report Sections Aligned |
|----------|---------|---------|-------------------------|
| **ISO/IEC/IEEE 29119-3** | 2013 | Test Documentation | All sections (Overall structure) |
| **IEEE 829** | 2008 | Test Summary Report | Executive Summary, Test Execution Analysis, Defect Analysis |
| **ISTQB Foundation** | v4.0 (2023) | Testing Fundamentals | Test Scenarios, Test Cases, Coverage Metrics |
| **ISTQB Test Manager** | 2012 | Test Management | Quality Assessment, Exit Criteria, Recommendations |
| **ISO 25010** | 2011 | Quality Model | Quality Assessment, Production Readiness |

---

# TEST CYCLE INFORMATION
- Total Sessions Analyzed: {metrics['total_sessions']}
- Session IDs: {', '.join(metrics['session_ids'][:5])}{'...' if len(metrics['session_ids']) > 5 else ''}
- Date Range: {metrics['date_range']['start']} to {metrics['date_range']['end']}
- Models Used: {', '.join(metrics['models_used'])}

{data_summary}

---

# YOUR TASK: Generate Standards-Compliant Test Closure Report

Generate a comprehensive Test Closure Report following the **ISO/IEC/IEEE 29119-3 Test Completion Report Template** with the following sections:
- Date Range: {metrics['date_range']['start']} to {metrics['date_range']['end']}
- Models Used: {', '.join(metrics['models_used'])}

# TEST EXECUTION SUMMARY (IEEE 829-2008 Aligned)

## Test Scenarios (ISTQB Test Design)
- Total Scenarios Generated: {metrics['test_scenarios']['total']}
- Scenarios by Type: {json.dumps(metrics['test_scenarios']['by_type'], indent=2)}
- Scenarios by Category: {json.dumps(metrics['test_scenarios']['by_category'], indent=2)}

## Test Cases (ISTQB Foundation - Test Design Techniques)
- Total Test Cases Generated: {metrics['test_cases']['total_generated']}
- Total Test Cases Optimized: {metrics['test_cases']['total_optimized']}
- Optimization Rate: {metrics['test_cases']['optimization_rate']}%

## Test Execution Results (IEEE 829 Test Summary Report)
- Total Tests Executed: {metrics['test_execution']['total_executed']}
- Passed: {metrics['test_execution']['passed']} ({metrics['test_execution']['pass_rate']}%)
- Failed: {metrics['test_execution']['failed']}
- Skipped: {metrics['test_execution']['skipped']}

## Coverage Analysis (ISTQB Test Manager - Coverage Criteria)
- Scenario Coverage: {metrics['coverage']['scenario_coverage']}%
- Requirement Coverage: {metrics['coverage']['requirement_coverage']}%

## Defect Summary (ISTQB Defect Management)
- Total Defects Identified: {metrics['defects']['total']}
- Critical: {metrics['defects']['critical']}
- Major: {metrics['defects']['major']}
- Minor: {metrics['defects']['minor']}

# FAILED TESTS (Potential Defects)
{json.dumps(metrics['defects']['from_failed_tests'][:10], indent=2)}

---

# YOUR TASK
Generate a comprehensive Test Closure Report following **ISO/IEC/IEEE 29119-3** Test Closure Report template with the following sections:

## 1. Executive Summary (IEEE 829 - Test Summary Report)
   - Overall test cycle assessment
   - Key achievements and challenges
   - Final recommendation (Ready for Production / Needs More Testing)
   - Alignment with project quality objectives

## 2. Test Execution Analysis (ISTQB Test Manager - Monitoring & Control)
   - Analysis of test scenario and case generation effectiveness
   - Test optimization effectiveness and ROI
   - Execution results interpretation with trend analysis
   - Coverage assessment against requirements

## 3. Quality Assessment (ISTQB Foundation - Test Metrics)
   - Pass rate analysis (Is {metrics['test_execution']['pass_rate']}% acceptable for production?)
   - Defect severity analysis and impact assessment
   - Risk areas identified with mitigation strategies
   - Quality gates status (Entry/Exit criteria from ISTQB)

## 4. Defect Analysis (IEEE 829 - Anomaly Report Summary)
   - Critical defects requiring immediate attention
   - Root cause analysis of major failures
   - Defect trends and patterns observed
   - Regression risks assessment

## 5. Coverage & Completeness (ISO/IEC/IEEE 29119-3)
   - Requirements coverage analysis
   - Test scenario coverage completeness
   - Untested areas and gaps (if any)
   - Traceability matrix summary

## 6. Lessons Learned (ISTQB Test Manager - Process Improvement)
   - What went well in this test cycle
   - Challenges encountered and how they were addressed
   - Process improvements for next cycle
   - Testing efficiency observations

## 7. Recommendations (Actionable)
   - Immediate actions required (defect fixes, retesting)
   - Process improvements aligned with ISTQB best practices
   - Tool/automation enhancement suggestions
   - Training or resource needs identification

## 8. Test Closure Criteria (IEEE 829 Exit Criteria)
   - Exit criteria met? (Yes/No with detailed explanation)
   - Outstanding issues and residual risks
   - Sign-off recommendation with justification
   - Production readiness assessment

---

**IMPORTANT GUIDELINES FOR REPORT GENERATION:**

1. **Standards Compliance**:
   - Structure the report according to ISO/IEC/IEEE 29119-3 Test Completion Report template
   - Reference specific standards where applicable (e.g., "According to ISTQB Foundation Level v4.0...")
   - Include standard identifiers in section headings where relevant

2. **Professional Quality**:
   - Use clear, professional language suitable for stakeholders and management
   - Apply proper markdown formatting with clear headings, tables, and bullet points
   - Maintain consistency with IEEE 829 documentation style

3. **Analytical Depth**:
   - Provide insights and analysis based on standards and best practices, not just data repetition
   - Interpret metrics in context of industry benchmarks and quality standards
   - Connect findings to relevant standard requirements (ISO 25010 quality characteristics)

4. **Global References**:
   - Cite specific standard sections when making recommendations (e.g., "Per IEEE 829 Section 9.2...")
   - Reference ISTQB best practices for test process improvements
   - Include ISO/IEC/IEEE 29119 guidelines for quality gates and exit criteria

5. **Actionable Outputs**:
   - Provide concrete, actionable recommendations aligned with international best practices
   - Prioritize actions based on risk and standard compliance requirements
   - Ensure all recommendations are traceable to specific standards or quality frameworks

6. **Compliance Documentation**:
   - Explicitly state which standard requirements are met or not met
   - Document any deviations from standard practices with justification
   - Include references to quality models (ISO 25010) for production readiness assessment

**Expected Output Format**: Professional, standards-compliant markdown report with clear structure, analytical insights, and actionable recommendations suitable for formal test closure documentation.
"""
        return prompt
    
    async def generate_closure_report(
        self,
        session_ids: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete test closure report with aggregated metrics
        
        Args:
            session_ids: Specific sessions to analyze
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            Dictionary containing metrics, AI prompt, and session data (for quality evaluation)
        """
        # Fetch sessions
        sessions = await self.fetch_sessions_for_closure(
            session_ids=session_ids,
            date_from=date_from,
            date_to=date_to
        )
        
        if not sessions:
            return {
                "success": False,
                "error": "No sessions found for the specified criteria",
                "metrics": None,
                "prompt": None,
                "all_session_data": []
            }
        
        # Aggregate metrics
        metrics = self.aggregate_test_metrics(sessions)
        
        # Generate AI prompt
        prompt = self.generate_closure_prompt(metrics)
        
        return {
            "success": True,
            "metrics": metrics,
            "prompt": prompt,
            "sessions_analyzed": len(sessions),
            "all_session_data": sessions  # Return sessions for quality evaluation
        }
    
    def evaluate_closure_report_quality(
        self,
        report_content: str,
        metrics: Dict[str, Any] = None,
        all_session_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of a generated test closure report using deterministic metrics
        
        This method uses the same evaluation methodology as Test Reporting:
        "Controlled, Model-Agnostic, and Fully Deterministic Evaluation Methodology 
        for LLM-Generated Test Reports and Test Closure"
        
        Note: Unlike Test Reporting, Test Closure focuses on high-level closure decision
        and does NOT calculate process-level quality metrics (those are in Test Reporting).
        
        Quality Dimensions (0-1 normalized scale):
        1. Completeness: Presence of required closure sections
        2. Coverage: Faithfulness to aggregated test data
        3. Clarity: Statistical readability and ambiguity
        4. Depth: Analytical vs descriptive content
        5. Consistency: Numeric constraint validation
        
        Args:
            report_content: The LLM-generated closure report (markdown format)
            metrics: Aggregated test metrics (ground truth data)
            all_session_data: List of session documents (same as Test Reporting)
            
        Returns:
            Dictionary containing:
            - overall_score: Weighted overall quality score (0-1)
            - completeness: Section completeness score (0-1)
            - coverage: Data coverage score (0-1)
            - clarity: Clarity score (0-1)
            - depth: Analysis depth score (0-1)
            - consistency: Numeric consistency score (0-1)
            - calculation_details: Detailed metrics breakdown
        """
        # Initialize evaluator with equal weights (same as Test Reporting)
        # All dimensions are equally important for academic objectivity
        evaluator = ReportQualityEvaluator(weights={
            "completeness": 0.20,  # Equal: All closure sections must be present
            "coverage": 0.20,      # Equal: Coverage of test data
            "clarity": 0.20,       # Equal: Must be clear for stakeholders
            "depth": 0.20,         # Equal: Deep analysis and decision rationale required
            "consistency": 0.20    # Equal: Numeric accuracy
        })
        
        # Prepare execution data from session data (SAME as Test Reporting)
        execution_data = {}
        if all_session_data and len(all_session_data) > 0:
            first_session = all_session_data[0]
            if first_session and isinstance(first_session, dict):
                processes = first_session.get("processes", {})
                if isinstance(processes, dict):
                    # Extract test cases and scenarios for coverage calculation
                    for process_name, process_data in processes.items():
                        output = process_data.get("output", {})
                        if "test_cases" in output or "test_scenarios" in output:
                            if "test_cases" not in execution_data:
                                execution_data = {}
                            execution_data.update({
                                "test_cases": output.get("test_cases", []),
                                "test_scenarios": output.get("test_scenarios", {}).get("TestScenarios", [])
                            })
        
        # Prepare metadata for consistency validation (SAME as Test Reporting)
        metadata = {
            "report_type": "test_closure",
            "total_sessions": metrics.get("total_sessions", 0) if metrics else 0,
            "test_metrics": metrics.get("test_execution", {}) if metrics else {},
            "sessions_analyzed": len(all_session_data) if all_session_data else 0
        }
        
        # Evaluate report quality (SAME as Test Reporting)
        quality_evaluation = evaluator.evaluate_report(
            report_content=report_content,
            execution_data=execution_data,
            metadata=metadata
        )
        
        logger.info(
            f"[Closure Quality] Overall Score: {quality_evaluation['overall_score']:.4f} | "
            f"Completeness: {quality_evaluation['completeness']:.4f} | "
            f"Coverage: {quality_evaluation['coverage']:.4f} | "
            f"Clarity: {quality_evaluation['clarity']:.4f} | "
            f"Depth: {quality_evaluation['depth']:.4f} | "
            f"Consistency: {quality_evaluation['consistency']:.4f}"
        )
        
        return quality_evaluation
    
    async def save_closure_report_to_database(
        self,
        session_ids: List[str],
        report_content: str,
        quality_evaluation: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save generated closure report as a NEW independent session in session_history.
        This allows multiple closure reports for the same sessions with different models/criteria.
        
        Similar to Test Reporting module, each closure report generation creates a new
        independent session record, enabling:
        - Multiple closure reports from same source sessions
        - Iterative closure report refinement
        - Historical tracking of closure decisions
        - Comparison of different AI models for closure analysis
        
        Args:
            session_ids: List of analyzed session IDs (source sessions)
            report_content: Generated closure report markdown
            quality_evaluation: Quality metrics for the report
            metadata: Closure metadata (model, sessions analyzed, etc.)
            
        Returns:
            New session ID for the test closure session
        """
        await self.initialize()
        collection = self.db["session_history"]
        
        # Generate unique session_id for this test closure session
        # Include microseconds to ensure uniqueness even for rapid successive calls
        timestamp = datetime.now()
        session_id = f"test_closure_{timestamp.strftime('%Y%m%d_%H%M%S')}_{timestamp.microsecond}"
        
        # Create descriptive process name
        session_count = len(session_ids) if session_ids else metadata.get("sessions_analyzed", 0)
        model_name = metadata.get("model_used", "Unknown")
        
        process_name = f"Test Closure: {session_count} Session(s) - {model_name}"
        
        # Build the new session document as an INDEPENDENT session
        session_document = {
            "session_id": session_id,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "process_name": process_name,
            "session_type": "test_closure",  # Mark as test closure session
            
            # Metadata about the closure process
            "closure_metadata": {
                "analyzed_session_ids": session_ids,
                "session_count": session_count,
                "model_used": model_name,
                "provider": metadata.get("provider", "Unknown"),
                "report_generated_at": timestamp.isoformat(),
                "date_from": metadata.get("date_from"),
                "date_to": metadata.get("date_to"),
                "total_test_scenarios": metadata.get("total_test_scenarios", 0),
                "total_test_cases": metadata.get("total_test_cases", 0),
                "total_test_execution": metadata.get("total_test_execution", 0)
            },
            
            # Store the closure report as a process output (consistent with other sessions)
            "processes": {
                "test_closure": {
                    "status": "completed",
                    "timestamp": timestamp.isoformat(),
                    "process_name": "Test Closure Report Generation",
                    "model_used": model_name,
                    
                    "input": {
                        "session_ids": session_ids,
                        "session_count": session_count,
                        "date_from": metadata.get("date_from"),
                        "date_to": metadata.get("date_to"),
                        "aggregated_metrics": metadata.get("metrics")
                    },
                    
                    "output": {
                        "success": True,
                        "report_content": report_content,
                        "report_length": len(report_content),
                        "generated_at": timestamp.isoformat(),
                        
                        # Include quality evaluation in output
                        "quality_evaluation": {
                            "overall_score": quality_evaluation.get("overall_score", 0),
                            "completeness": quality_evaluation.get("completeness", 0),
                            "coverage": quality_evaluation.get("coverage", 0),
                            "clarity": quality_evaluation.get("clarity", 0),
                            "depth": quality_evaluation.get("depth", 0),
                            "consistency": quality_evaluation.get("consistency", 0),
                            "weights_used": quality_evaluation.get("weights_used", {}),
                            "calculation_details": quality_evaluation.get("calculation_details", {})
                        }
                    },
                    
                    "metadata": {
                        "model_used": model_name,
                        "provider": metadata.get("provider", "Unknown"),
                        "sessions_analyzed": session_count,
                        "generation_time_seconds": metadata.get("generation_time", 0),
                        
                        # Aggregated test metrics summary
                        "test_summary": {
                            "total_scenarios": metadata.get("total_test_scenarios", 0),
                            "total_test_cases": metadata.get("total_test_cases", 0),
                            "total_executed": metadata.get("total_test_execution", 0),
                            "pass_rate": metadata.get("pass_rate", 0)
                        }
                    }
                }
            }
        }
        
        # Insert as a NEW session document
        await collection.insert_one(session_document)
        
        logger.info(f"✅ Test closure report saved as new independent session: {session_id}")
        logger.info(f"   - Analyzed sessions: {session_count}")
        logger.info(f"   - Model: {model_name}")
        logger.info(f"   - Quality score: {quality_evaluation.get('overall_score', 0):.4f}")
        logger.info(f"   - Report length: {len(report_content)} characters")
        
        return session_id


# Singleton instance
test_closure_service = TestClosureService()
