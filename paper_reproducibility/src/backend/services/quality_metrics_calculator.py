"""
quality_metrics_calculator.py
-----------------------------
Objective Quality Metrics Calculator for Test Reporting
Calculates 4-dimensional quality assessment from quantitative data

Based on:
- ISTQB quality characteristics
- ISO 25010 quality model
- IEEE 829 metrics standards
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class QualityMetricsCalculator:
    """
    Calculate objective quality metrics for STLC processes
    
    Quality Dimensions (1-10 scale):
    1. Completeness - Are all required elements present?
    2. Clarity - Is the output clear and unambiguous?
    3. Coverage - Are all relevant areas addressed?
    4. Depth - Is the analysis sufficiently detailed?
    """
    
    def calculate_process_quality(
        self, 
        process_name: str, 
        output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for a specific STLC process
        
        Args:
            process_name: Name of the STLC process
            output: Process output data
            
        Returns:
            Dictionary with quality scores and overall score
        """
        if process_name == "test_scenario_generation":
            return self._calculate_scenario_quality(output)
        elif process_name == "test_case_generation":
            return self._calculate_test_case_quality(output)
        elif process_name == "test_case_optimization":
            return self._calculate_optimization_quality(output)
        elif process_name == "requirement_analysis":
            return self._calculate_requirement_quality(output)
        elif process_name == "test_execution":
            return self._calculate_execution_quality(output)
        else:
            return self._default_quality_score()
    
    def _calculate_scenario_quality(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality for Test Scenario Generation
        
        Completeness: % of scenarios with all required fields
        Clarity: Average description length and structure
        Coverage: Diversity of test types and categories
        Depth: Presence of preconditions, steps, expected results
        """
        scenarios = output.get("test_scenarios", {}).get("TestScenarios", [])
        
        if not scenarios:
            return self._default_quality_score()
        
        total_scenarios = len(scenarios)
        
        # 1. COMPLETENESS (1-10)
        # Based on required field presence
        required_fields = ["ScenarioID", "Title", "Description", "Objective"]
        complete_count = 0
        
        for scenario in scenarios:
            if all(field in scenario and scenario[field] for field in required_fields):
                complete_count += 1
        
        completeness_ratio = complete_count / total_scenarios
        completeness_score = round(1 + (completeness_ratio * 9), 1)  # Scale to 1-10
        
        # 2. CLARITY (1-10)
        # Based on description quality and length
        total_desc_words = 0
        structured_count = 0  # Has clear structure (steps, expected results)
        
        for scenario in scenarios:
            desc = scenario.get("Description", "")
            total_desc_words += len(desc.split())
            
            # Check for structure indicators
            if any(keyword in desc.lower() for keyword in ["step", "expected", "precondition", "result"]):
                structured_count += 1
        
        avg_desc_length = total_desc_words / total_scenarios
        structure_ratio = structured_count / total_scenarios
        
        # Optimal description length: 30-100 words
        length_score = min(avg_desc_length / 50, 1.0) if avg_desc_length < 100 else max(1.0 - (avg_desc_length - 100) / 200, 0.5)
        clarity_raw = (0.5 * length_score) + (0.5 * structure_ratio)
        clarity_score = round(1 + (clarity_raw * 9), 1)
        
        # 3. COVERAGE (1-10)
        # Diversity of test types and categories
        categories = set()
        test_types = {"functional": 0, "edge": 0, "negative": 0, "performance": 0, "security": 0}
        
        for scenario in scenarios:
            cat = scenario.get("Category", "")
            if cat:
                categories.add(cat)
            
            # Detect test type from title/description
            text = (scenario.get("Title", "") + " " + scenario.get("Description", "")).lower()
            if any(word in text for word in ["edge", "boundary", "limit"]):
                test_types["edge"] += 1
            elif any(word in text for word in ["negative", "error", "invalid", "fail"]):
                test_types["negative"] += 1
            elif any(word in text for word in ["performance", "load", "stress", "speed"]):
                test_types["performance"] += 1
            elif any(word in text for word in ["security", "authentication", "authorization"]):
                test_types["security"] += 1
            else:
                test_types["functional"] += 1
        
        # Score based on diversity
        category_diversity = min(len(categories) / 3, 1.0)  # Target: 3+ categories
        type_diversity = sum(1 for count in test_types.values() if count > 0) / len(test_types)
        
        coverage_raw = (0.5 * category_diversity) + (0.5 * type_diversity)
        coverage_score = round(1 + (coverage_raw * 9), 1)
        
        # 4. DEPTH (1-10)
        # Presence of detailed elements
        with_preconditions = 0
        with_steps = 0
        with_expected_results = 0
        
        for scenario in scenarios:
            desc = scenario.get("Description", "").lower()
            if "precondition" in desc or "prerequisite" in desc:
                with_preconditions += 1
            if "step" in desc:
                with_steps += 1
            if "expect" in desc or "result" in desc:
                with_expected_results += 1
        
        precond_ratio = with_preconditions / total_scenarios
        steps_ratio = with_steps / total_scenarios
        expected_ratio = with_expected_results / total_scenarios
        
        depth_raw = (0.3 * precond_ratio) + (0.4 * steps_ratio) + (0.3 * expected_ratio)
        depth_score = round(1 + (depth_raw * 9), 1)
        
        # Overall score (weighted average)
        overall_score = round(
            (0.25 * completeness_score) + 
            (0.25 * clarity_score) + 
            (0.25 * coverage_score) + 
            (0.25 * depth_score), 
            1
        )
        
        return {
            "score": overall_score,
            "completeness": int(completeness_score),
            "clarity": int(clarity_score),
            "coverage": int(coverage_score),
            "depth": int(depth_score),
            "calculation_details": {
                "total_scenarios": total_scenarios,
                "complete_scenarios": complete_count,
                "avg_description_length": round(avg_desc_length, 1),
                "categories_found": len(categories),
                "test_type_distribution": test_types
            }
        }
    
    def _calculate_test_case_quality(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality for Test Case Generation
        
        Completeness: % with all fields (steps, test data, expected results)
        Clarity: Step clarity and test data specificity
        Coverage: Positive/negative ratio, complexity distribution
        Depth: Number of steps, detail level
        """
        # Try direct format first: output.test_case_results
        test_case_results = output.get("test_case_results", [])
        
        # Try nested format: output.data.test_case_results
        if not test_case_results:
            test_case_results = output.get("data", {}).get("test_case_results", [])
        
        # Try old format: output.test_cases
        if not test_case_results:
            old_cases = output.get("test_cases", [])
            if old_cases:
                test_case_results = [{"test_cases": old_cases}]
        
        if not test_case_results:
            return self._default_quality_score()
        
        all_test_cases = []
        for result in test_case_results:
            all_test_cases.extend(result.get("test_cases", []))
        
        if not all_test_cases:
            return self._default_quality_score()
        
        total_cases = len(all_test_cases)
        
        # 1. COMPLETENESS - Check for required fields
        complete_count = 0
        for tc in all_test_cases:
            # Support both formats
            has_steps = bool(tc.get("Steps") or tc.get("test_steps"))
            has_expected = bool(tc.get("ExpectedResult") or tc.get("expected_results") or tc.get("expected_result"))
            has_description = bool(tc.get("Description"))
            has_objective = bool(tc.get("Objective"))
            
            # Old format: needs Steps + ExpectedResult
            # New format: needs Description + Objective
            if (has_steps and has_expected) or (has_description and has_objective):
                complete_count += 1
        
        completeness_ratio = complete_count / total_cases
        completeness_score = round(1 + (completeness_ratio * 9), 1)
        
        # 2. CLARITY - Average description/objective length and test data presence
        total_description_words = 0
        with_test_data = 0
        total_steps = 0
        
        for tc in all_test_cases:
            # Check description/objective length
            description = tc.get("Description", "") + " " + tc.get("Objective", "")
            total_description_words += len(description.split())
            
            # Check for steps (old format)
            steps = tc.get("Steps") or tc.get("test_steps", [])
            if isinstance(steps, list):
                total_steps += len(steps)
            elif steps:
                total_steps += 1
            
            # Check for specific test data
            test_data = tc.get("TestData") or tc.get("test_data", "")
            if test_data and str(test_data).lower() not in ["n/a", "none", ""]:
                with_test_data += 1
        
        avg_desc_length = total_description_words / total_cases
        test_data_ratio = with_test_data / total_cases
        avg_steps = total_steps / total_cases if total_steps > 0 else 0
        
        # Optimal: 30-100 words for description OR 3-7 steps
        if avg_steps > 0:
            # Old format with steps
            steps_score = min(avg_steps / 5, 1.0) if avg_steps < 10 else max(1.0 - (avg_steps - 10) / 20, 0.5)
            clarity_raw = (0.5 * steps_score) + (0.5 * test_data_ratio)
        else:
            # New format with description
            desc_score = min(avg_desc_length / 65, 1.0) if avg_desc_length < 130 else max(1.0 - (avg_desc_length - 130) / 100, 0.5)
            clarity_raw = desc_score
        
        clarity_score = round(1 + (clarity_raw * 9), 1)
        
        # 3. COVERAGE
        positive_count = 0
        negative_count = 0
        
        for tc in all_test_cases:
            title = tc.get("Title", "").lower()
            if any(word in title for word in ["invalid", "error", "negative", "fail"]):
                negative_count += 1
            else:
                positive_count += 1
        
        # Target ratio: 2:1 positive to negative
        ratio_score = 1.0 - abs((positive_count / max(negative_count, 1)) - 2) / 4
        ratio_score = max(0.5, min(ratio_score, 1.0))
        
        coverage_score = round(1 + (ratio_score * 9), 1)
        
        # 4. DEPTH - Detailed steps or objectives
        detailed_count = 0
        for tc in all_test_cases:
            # Check for detailed steps (old format)
            steps = tc.get("Steps") or tc.get("test_steps", [])
            if isinstance(steps, list) and len(steps) >= 3:
                detailed_count += 1
            # Check for detailed objectives (new format)
            elif tc.get("Objective") and len(tc.get("Objective", "").split()) >= 15:
                detailed_count += 1
        
        depth_ratio = detailed_count / total_cases
        depth_score = round(1 + (depth_ratio * 9), 1)
        
        overall_score = round(
            (0.25 * completeness_score) + 
            (0.25 * clarity_score) + 
            (0.25 * coverage_score) + 
            (0.25 * depth_score), 
            1
        )
        
        return {
            "score": overall_score,
            "completeness": int(completeness_score),
            "clarity": int(clarity_score),
            "coverage": int(coverage_score),
            "depth": int(depth_score),
            "calculation_details": {
                "total_test_cases": total_cases,
                "complete_cases": complete_count,
                "avg_steps_per_case": round(avg_steps, 1) if avg_steps > 0 else None,
                "avg_description_words": round(avg_desc_length, 1) if avg_desc_length > 0 else None,
                "positive_negative_ratio": f"{positive_count}:{negative_count}",
                "with_test_data": with_test_data if with_test_data > 0 else None
            }
        }
    
    def _calculate_optimization_quality(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality for Test Case Optimization
        
        Completeness: All optimized cases have justifications
        Clarity: Clear optimization rationale
        Coverage: Coverage preservation rate
        Depth: Detailed analysis of each optimization
        """
        # Try new format first
        data = output.get("data", {})
        metadata = output.get("metadata", {})
        
        optimized_results = data.get("optimized_results", [])
        
        # Try old format if new format not found
        if not optimized_results:
            # Old format: unique_test_cases + similar_test_cases
            unique_cases = output.get("unique_test_cases", [])
            similar_cases = output.get("similar_test_cases", [])
            
            if unique_cases:
                # Treat unique cases as optimized results
                optimized_results = unique_cases
        
        if not optimized_results:
            return self._default_quality_score()
        
        # Get counts
        original_count = metadata.get("original_count", output.get("total_test_cases", 0))
        optimized_count = metadata.get("optimized_count", len(optimized_results))
        
        # Try old format for counts
        if original_count == 0:
            unique = output.get("unique_test_cases", [])
            similar = output.get("similar_test_cases", [])
            if unique or similar:
                original_count = len(unique) + len(similar)
                optimized_count = len(unique)
        
        if original_count == 0:
            return self._default_quality_score()
        
        # 1. COMPLETENESS - All optimized cases have justification
        with_justification = 0
        for result in optimized_results:
            if result.get("optimization_rationale"):
                with_justification += 1
        
        completeness_ratio = with_justification / len(optimized_results) if optimized_results else 0
        completeness_score = round(1 + (completeness_ratio * 9), 1)
        
        # 2. CLARITY - Rationale quality
        avg_rationale_length = 0
        for result in optimized_results:
            rationale = result.get("optimization_rationale", "")
            avg_rationale_length += len(rationale.split())
        
        avg_rationale_length /= len(optimized_results) if optimized_results else 1
        
        # Optimal: 10-30 words
        clarity_raw = min(avg_rationale_length / 20, 1.0) if avg_rationale_length < 40 else 0.7
        clarity_score = round(1 + (clarity_raw * 9), 1)
        
        # 3. COVERAGE - Preservation rate
        optimization_rate = (original_count - optimized_count) / original_count
        
        # Good optimization: 20-40% reduction
        if 0.2 <= optimization_rate <= 0.4:
            coverage_raw = 1.0
        elif optimization_rate < 0.2:
            coverage_raw = optimization_rate / 0.2
        else:
            coverage_raw = max(0.6, 1.0 - (optimization_rate - 0.4) / 0.3)
        
        coverage_score = round(1 + (coverage_raw * 9), 1)
        
        # 4. DEPTH - Detailed optimization metadata
        depth_score = 7  # Default for optimization (process-specific)
        
        overall_score = round(
            (0.3 * completeness_score) + 
            (0.3 * clarity_score) + 
            (0.3 * coverage_score) + 
            (0.1 * depth_score), 
            1
        )
        
        return {
            "score": overall_score,
            "completeness": int(completeness_score),
            "clarity": int(clarity_score),
            "coverage": int(coverage_score),
            "depth": int(depth_score),
            "calculation_details": {
                "original_count": original_count,
                "optimized_count": optimized_count,
                "optimization_rate": f"{round(optimization_rate * 100, 1)}%"
            }
        }
    
    def _calculate_requirement_quality(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality for Requirement Analysis"""
        requirements = output.get("requirements", [])
        
        if not requirements:
            return self._default_quality_score()
        
        total_req = len(requirements)
        
        # Completeness: Has ID, description, type
        complete_count = sum(1 for req in requirements 
                           if req.get("id") and req.get("description") and req.get("type"))
        completeness_score = round(1 + ((complete_count / total_req) * 9), 1)
        
        # Other dimensions use default heuristics
        clarity_score = 7
        coverage_score = 7
        depth_score = 7
        
        overall_score = round(
            (0.4 * completeness_score) + (0.2 * clarity_score) + 
            (0.2 * coverage_score) + (0.2 * depth_score), 1
        )
        
        return {
            "score": overall_score,
            "completeness": int(completeness_score),
            "clarity": int(clarity_score),
            "coverage": int(coverage_score),
            "depth": int(depth_score),
            "calculation_details": {"total_requirements": total_req}
        }
    
    def _calculate_execution_quality(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality for Test Execution"""
        terminal_output = output.get("terminal_output", "")
        
        # Parse pass/fail from output
        passed = terminal_output.lower().count("passed")
        failed = terminal_output.lower().count("failed")
        total = passed + failed
        
        if total == 0:
            return self._default_quality_score()
        
        pass_rate = passed / total
        
        # Quality based on pass rate
        completeness_score = 9 if total > 0 else 1
        clarity_score = 8  # Execution output is generally clear
        coverage_score = round(1 + (pass_rate * 9), 1)
        depth_score = 7
        
        overall_score = round(
            (0.2 * completeness_score) + (0.2 * clarity_score) + 
            (0.4 * coverage_score) + (0.2 * depth_score), 1
        )
        
        return {
            "score": overall_score,
            "completeness": int(completeness_score),
            "clarity": int(clarity_score),
            "coverage": int(coverage_score),
            "depth": int(depth_score),
            "calculation_details": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{round(pass_rate * 100, 1)}%"
            }
        }
    
    def _default_quality_score(self) -> Dict[str, Any]:
        """Default quality score when calculation not possible"""
        return {
            "score": 5.0,
            "completeness": 5,
            "clarity": 5,
            "coverage": 5,
            "depth": 5,
            "calculation_details": {"note": "Default score - insufficient data"}
        }


# Singleton instance
quality_calculator = QualityMetricsCalculator()
