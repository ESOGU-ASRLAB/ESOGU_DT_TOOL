"""
report_quality_evaluator.py
---------------------------
Model-Agnostic, Deterministic Test Report Quality Evaluator

Implements the methodology from:
"Controlled, Model-Agnostic, and Fully Deterministic Evaluation Methodology 
for LLM-Generated Test Reports and Test Closure"

Quality Dimensions (0-1 normalized scale):
1. Completeness: Presence of required sections
2. Coverage: Faithfulness to execution data
3. Clarity: Statistical readability and ambiguity
4. Depth: Analytical vs descriptive content
5. Consistency: Numeric constraint validation
"""

import re
import logging
from typing import Dict, Any, List, Set, Tuple

logger = logging.getLogger(__name__)


class ReportQualityEvaluator:
    """
    Deterministic evaluator for test report quality
    
    Uses:
    - Structural parsing for section detection
    - Execution-grounded mappings for coverage
    - Statistical text analysis for clarity
    - Rule-based pattern matching for depth
    - Numeric constraint validation for consistency
    """
    
    # Required sections for comprehensive test reporting (IEEE 829 based)
    REQUIRED_SECTIONS = {
        "test_summary",           # Executive summary
        "test_metrics",           # Execution metrics and results
        "quality_assessment",     # Quality analysis
        "defect_analysis",        # Defect status and trends
        "coverage_analysis",      # Coverage statistics
        "risk_assessment",        # Residual risk evaluation
        "recommendations",        # Actionable recommendations
        "test_closure",          # Closure decision and readiness
        "lessons_learned"        # Process improvements
    }
    
    # Ambiguity markers for clarity assessment
    AMBIGUITY_MARKERS = [
        "maybe", "might", "could be", "possibly", "perhaps",
        "seems", "appears", "likely", "probably", "unclear",
        "uncertain", "ambiguous", "vague", "approximately",
        "roughly", "about", "around", "some", "several"
    ]
    
    # Analytical markers for depth assessment
    ANALYTICAL_MARKERS = [
        "because", "therefore", "thus", "consequently", "as a result",
        "due to", "caused by", "indicates", "suggests", "implies",
        "demonstrates", "reveals", "shows that", "evidences",
        "analysis shows", "assessment reveals", "evaluation indicates",
        "root cause", "impact on", "risk of", "quality implication",
        "trend analysis", "pattern suggests", "correlation between"
    ]
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize evaluator with optional custom weights
        
        Args:
            weights: Custom weights for aggregation (default: equal weights)
        """
        self.weights = weights or {
            "completeness": 0.20,
            "coverage": 0.20,
            "clarity": 0.20,
            "depth": 0.20,
            "consistency": 0.20
        }
        
        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            logger.warning(f"Weights sum to {total}, normalizing to 1.0")
            for key in self.weights:
                self.weights[key] /= total
    
    def evaluate_report(
        self,
        report_content: str,
        execution_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive report quality evaluation
        
        Args:
            report_content: Generated report text (markdown)
            execution_data: Ground truth test execution data
            metadata: Additional report metadata
            
        Returns:
            Dictionary with individual metrics and overall score
        """
        # Parse report structure
        sections_present = self._extract_sections(report_content)
        sentences = self._extract_sentences(report_content)
        
        # Calculate individual metrics
        completeness = self._calculate_completeness(sections_present)
        coverage = self._calculate_coverage(report_content, execution_data)
        clarity = self._calculate_clarity(sentences)
        depth = self._calculate_depth(sentences)
        consistency = self._calculate_consistency(report_content, metadata)
        
        # Calculate weighted overall score
        overall_score = (
            self.weights["completeness"] * completeness +
            self.weights["coverage"] * coverage +
            self.weights["clarity"] * clarity +
            self.weights["depth"] * depth +
            self.weights["consistency"] * consistency
        )
        
        return {
            "overall_score": round(overall_score, 4),
            "completeness": round(completeness, 4),
            "coverage": round(coverage, 4),
            "clarity": round(clarity, 4),
            "depth": round(depth, 4),
            "consistency": round(consistency, 4),
            "weights_used": self.weights.copy(),
            "calculation_details": {
                "sections_required": len(self.REQUIRED_SECTIONS),
                "sections_present": len(sections_present),
                "total_sentences": len(sentences),
                "sections_detected": list(sections_present)
            }
        }
    
    def _extract_sections(self, report_content: str) -> Set[str]:
        """
        Extract present sections using structural parsing
        
        Detects markdown headers (## Section Name) and maps to required sections
        
        Returns:
            Set of detected section keys
        """
        sections_found = set()
        
        # Extract all markdown headers (## or #)
        header_pattern = r'^#{1,3}\s+(?:[📋📊🐛🎯⚠️💡📈📉✅❌🔍🚀📝🔄🏆📘💻⚡🧪]+\s*)?(.+)$'
        lines = report_content.split('\n')
        
        for line in lines:
            match = re.match(header_pattern, line.strip())
            if match:
                title = match.group(1).strip().lower()
                
                # Map header text to required sections
                if any(word in title for word in ["summary", "executive"]):
                    sections_found.add("test_summary")
                elif any(word in title for word in ["metric", "result", "execution"]):
                    sections_found.add("test_metrics")
                elif any(word in title for word in ["quality", "assessment"]):
                    sections_found.add("quality_assessment")
                elif any(word in title for word in ["defect", "bug", "issue"]):
                    sections_found.add("defect_analysis")
                elif any(word in title for word in ["coverage", "trace"]):
                    sections_found.add("coverage_analysis")
                elif any(word in title for word in ["risk", "threat", "concern"]):
                    sections_found.add("risk_assessment")
                elif any(word in title for word in ["recommendation", "action", "next step"]):
                    sections_found.add("recommendations")
                elif any(word in title for word in ["closure", "completion", "readiness"]):
                    sections_found.add("test_closure")
                elif any(word in title for word in ["lesson", "improvement", "retrospective"]):
                    sections_found.add("lessons_learned")
        
        return sections_found
    
    def _calculate_completeness(self, sections_present: Set[str]) -> float:
        """
        Calculate completeness metric
        
        Formula: Completeness = |R_present| / |R_required|
        
        Args:
            sections_present: Set of detected sections
            
        Returns:
            Completeness score (0-1)
        """
        required_count = len(self.REQUIRED_SECTIONS)
        present_count = len(sections_present & self.REQUIRED_SECTIONS)
        
        completeness = present_count / required_count if required_count > 0 else 0.0
        
        logger.debug(f"Completeness: {present_count}/{required_count} sections = {completeness:.4f}")
        
        return completeness
    
    def _calculate_coverage(
        self,
        report_content: str,
        execution_data: Dict[str, Any]
    ) -> float:
        """
        Calculate coverage metric (faithfulness to execution data)
        
        Formula: Coverage = |E_reported ∩ E_executed| / |E_executed|
        
        Compares test items mentioned in report vs actually executed
        
        Args:
            report_content: Report text
            execution_data: Ground truth execution data
            
        Returns:
            Coverage score (0-1)
        """
        if not execution_data:
            logger.debug("No execution data provided, using default coverage: 0.5")
            return 0.5
        
        # Extract executed test items
        executed_items = self._extract_executed_items(execution_data)
        
        if not executed_items:
            return 0.5
        
        # Extract reported test items from report
        reported_items = self._extract_reported_items(report_content)
        
        # Calculate intersection
        intersection = executed_items & reported_items
        coverage = len(intersection) / len(executed_items) if executed_items else 0.0
        
        logger.debug(f"Coverage: {len(intersection)}/{len(executed_items)} items = {coverage:.4f}")
        
        return coverage
    
    def _extract_executed_items(self, execution_data: Dict[str, Any]) -> Set[str]:
        """Extract test item IDs from execution data"""
        items = set()
        
        # Extract from test cases
        if "test_cases" in execution_data:
            for tc in execution_data.get("test_cases", []):
                tc_id = tc.get("TestCaseID") or tc.get("id") or tc.get("test_case_id")
                if tc_id:
                    items.add(str(tc_id).lower())
        
        # Extract from scenarios
        if "test_scenarios" in execution_data:
            for ts in execution_data.get("test_scenarios", []):
                ts_id = ts.get("ScenarioID") or ts.get("id")
                if ts_id:
                    items.add(str(ts_id).lower())
        
        # Extract from processes
        if "processes" in execution_data:
            for proc in execution_data.get("processes", []):
                proc_name = proc.get("process_name")
                if proc_name:
                    items.add(proc_name.lower())
        
        return items
    
    def _extract_reported_items(self, report_content: str) -> Set[str]:
        """Extract test item references from report text"""
        items = set()
        
        # Pattern for test IDs: TC-001, TS-001, TEST-123, etc.
        id_pattern = r'\b(TC|TS|TEST|SCENARIO|CASE)[-_]?\d+\b'
        matches = re.findall(id_pattern, report_content, re.IGNORECASE)
        items.update(match.lower() for match in matches)
        
        # Pattern for process names
        process_keywords = [
            "test_scenario_generation", "test_case_generation",
            "test_case_optimization", "test_code_generation",
            "test_execution", "requirement_analysis"
        ]
        
        content_lower = report_content.lower()
        for keyword in process_keywords:
            if keyword in content_lower:
                items.add(keyword)
        
        return items
    
    def _extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text using basic sentence boundary detection
        
        Returns:
            List of sentences
        """
        # Simple sentence splitting (handles . ! ?)
        sentence_pattern = r'[^.!?]+[.!?]+'
        sentences = re.findall(sentence_pattern, text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return sentences
    
    def _calculate_clarity(self, sentences: List[str]) -> float:
        """
        Calculate clarity metric (readability and precision)
        
        Formula: Clarity = 1 - (S_ambiguous / S_total)
        
        Args:
            sentences: List of sentences from report
            
        Returns:
            Clarity score (0-1)
        """
        if not sentences:
            return 0.5
        
        total_sentences = len(sentences)
        ambiguous_count = 0
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Check if sentence contains any ambiguity marker
            if any(marker in sentence_lower for marker in self.AMBIGUITY_MARKERS):
                ambiguous_count += 1
        
        clarity = 1.0 - (ambiguous_count / total_sentences)
        
        logger.debug(f"Clarity: {ambiguous_count}/{total_sentences} ambiguous = {clarity:.4f}")
        
        return clarity
    
    def _calculate_depth(self, sentences: List[str]) -> float:
        """
        Calculate depth metric (analytical content)
        
        Formula: Depth = S_analytical / S_total
        
        Args:
            sentences: List of sentences from report
            
        Returns:
            Depth score (0-1)
        """
        if not sentences:
            return 0.0
        
        total_sentences = len(sentences)
        analytical_count = 0
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Check if sentence contains any analytical marker
            if any(marker in sentence_lower for marker in self.ANALYTICAL_MARKERS):
                analytical_count += 1
        
        depth = analytical_count / total_sentences
        
        logger.debug(f"Depth: {analytical_count}/{total_sentences} analytical = {depth:.4f}")
        
        return depth
    
    def _calculate_consistency(
        self,
        report_content: str,
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate consistency metric (numeric constraint validation)
        
        Formula: Consistency = 1 if all constraints hold, else 0
        
        Validates logical coherence of numerical values:
        - Total = Passed + Failed + Blocked/Skipped
        - Percentages sum to 100%
        - Coverage values in valid range (0-100%)
        
        Args:
            report_content: Report text
            metadata: Report metadata with expected values
            
        Returns:
            Consistency score (0 or 1)
        """
        constraints_valid = True
        
        # Extract numeric values from report
        numbers = self._extract_numeric_values(report_content)
        
        # Constraint 1: Test count consistency (Total = Passed + Failed + Other)
        if "total" in numbers and "passed" in numbers and "failed" in numbers:
            total = numbers["total"]
            passed = numbers["passed"]
            failed = numbers["failed"]
            blocked = numbers.get("blocked", 0)
            skipped = numbers.get("skipped", 0)
            
            expected_total = passed + failed + blocked + skipped
            
            # Allow 5% tolerance for rounding
            if abs(total - expected_total) > (total * 0.05):
                logger.warning(f"Total mismatch: {total} != {expected_total}")
                constraints_valid = False
        
        # Constraint 2: Percentage consistency (should sum to ~100%)
        percentages = []
        for key in ["pass_rate", "fail_rate", "blocked_rate"]:
            if key in numbers:
                percentages.append(numbers[key])
        
        if percentages:
            total_percentage = sum(percentages)
            if abs(total_percentage - 100.0) > 5.0:  # 5% tolerance
                logger.warning(f"Percentage sum: {total_percentage}% != 100%")
                constraints_valid = False
        
        # Constraint 3: Coverage values in valid range (0-100%)
        for key in ["coverage", "code_coverage", "requirement_coverage"]:
            if key in numbers:
                value = numbers[key]
                if value < 0 or value > 100:
                    logger.warning(f"Invalid {key}: {value}%")
                    constraints_valid = False
        
        consistency = 1.0 if constraints_valid else 0.0
        
        logger.debug(f"Consistency: {'Valid' if constraints_valid else 'Invalid'} = {consistency}")
        
        return consistency
    
    def _extract_numeric_values(self, text: str) -> Dict[str, float]:
        """
        Extract numeric values from report text
        
        Returns:
            Dictionary mapping metric names to values
        """
        numbers = {}
        
        # Patterns for common test metrics
        patterns = {
            "total": r'(?:total|all)\s+(?:tests?|cases?):\s*(\d+)',
            "passed": r'(?:passed|success):\s*(\d+)',
            "failed": r'(?:failed|failure):\s*(\d+)',
            "blocked": r'blocked:\s*(\d+)',
            "skipped": r'skipped:\s*(\d+)',
            "pass_rate": r'pass\s+rate:\s*(\d+(?:\.\d+)?)%?',
            "fail_rate": r'fail\s+rate:\s*(\d+(?:\.\d+)?)%?',
            "coverage": r'(?:test\s+)?coverage:\s*(\d+(?:\.\d+)?)%?',
            "code_coverage": r'code\s+coverage:\s*(\d+(?:\.\d+)?)%?'
        }
        
        text_lower = text.lower()
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    numbers[key] = float(match.group(1))
                except ValueError:
                    pass
        
        return numbers


# Singleton instance with default weights
report_quality_evaluator = ReportQualityEvaluator()


def evaluate_report_quality(
    report_content: str,
    execution_data: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None,
    custom_weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Convenience function for report quality evaluation
    
    Args:
        report_content: Generated report text
        execution_data: Ground truth test execution data
        metadata: Report metadata
        custom_weights: Optional custom weights for metrics
        
    Returns:
        Quality evaluation results
    """
    if custom_weights:
        evaluator = ReportQualityEvaluator(weights=custom_weights)
    else:
        evaluator = report_quality_evaluator
    
    return evaluator.evaluate_report(report_content, execution_data, metadata)
