"""
test_closure_quality.py
-----------------------
Test script for Test Closure Report Quality Evaluation
Tests the new quality evaluation functionality
"""

import asyncio
import logging
from services.test_closure_service import test_closure_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample closure report for testing
SAMPLE_CLOSURE_REPORT = """
# 📋 Test Closure Report

## 🎯 Executive Summary
This test closure report provides a comprehensive analysis of the test cycle executed between 2025-11-01 and 2025-12-31. The testing activities spanned across 15 sessions, covering requirement analysis, test scenario generation, test case optimization, and test execution phases.

## 📊 Test Execution Metrics
- **Total Test Cases**: 245
- **Test Cases Passed**: 198 (80.8%)
- **Test Cases Failed**: 32 (13.1%)
- **Test Cases Blocked**: 15 (6.1%)
- **Pass Rate**: 80.8%
- **Code Coverage**: 78%

## 🏆 Quality Assessment
The overall quality of the test execution demonstrates strong adherence to STLC methodology. The pass rate of 80.8% indicates that the application meets the majority of functional requirements. However, the 13.1% failure rate requires attention before final release.

**Key Quality Indicators:**
- Test coverage is comprehensive across all critical modules
- Test case design follows IEEE 829 standards
- Traceability matrix is complete and accurate
- Defect detection rate is above industry average

## 🐛 Defect Analysis
A total of 32 defects were identified during the test execution phase:
- **Critical**: 5 defects (15.6%)
- **Major**: 12 defects (37.5%)
- **Minor**: 15 defects (46.9%)

**Root Cause Analysis:**
The critical defects are primarily related to database transaction handling and API timeout issues. Major defects stem from UI responsiveness and validation logic. Minor defects are cosmetic and documentation-related.

**Defect Trends:**
- Early test cycles had higher defect density
- Defect detection improved after test case optimization
- Regression defects decreased significantly after code review

## 📈 Coverage Analysis
Test coverage analysis reveals thorough examination of system functionality:
- **Functional Coverage**: 85%
- **Requirement Coverage**: 92%
- **Code Coverage**: 78%
- **API Coverage**: 88%

All critical business flows have been tested. Edge cases and error scenarios are adequately covered.

## ⚠️ Risk Assessment
**Residual Risks:**
1. **High Risk**: 5 critical defects remain unresolved - potential production impact
2. **Medium Risk**: Database performance under high load conditions not fully tested
3. **Low Risk**: Minor UI inconsistencies may affect user experience

**Risk Mitigation:**
- Critical defects must be resolved before release
- Additional performance testing recommended
- UI issues can be addressed in post-release patches

## 💡 Recommendations
Based on the test closure analysis, the following recommendations are made:

1. **Critical Defect Resolution**: All 5 critical defects must be fixed and retested before production deployment
2. **Performance Testing**: Conduct additional load testing for database operations
3. **Regression Testing**: Execute full regression suite after critical defect fixes
4. **Documentation**: Update user documentation to reflect current system behavior
5. **Training**: Provide training for support team on known issues and workarounds

## ✅ Test Closure Decision
**Status**: **CONDITIONAL GO**

The application demonstrates acceptable quality levels but requires resolution of critical defects before production release. The pass rate of 80.8% is within acceptable thresholds, but the 5 critical defects pose significant risk.

**Closure Criteria Status:**
- ✅ All planned test cases executed
- ✅ Test coverage targets met (>75%)
- ❌ Critical defects outstanding (5 remain)
- ✅ Test documentation complete
- ✅ Traceability matrix validated

**Decision Rationale:**
The testing demonstrates that the application is functionally sound with 80.8% pass rate. However, due to 5 outstanding critical defects that could impact core business functionality, a conditional go decision is made. These defects must be resolved, verified, and retested before production deployment. Once resolved, a final go decision can be issued.

## 📘 Lessons Learned
**What Went Well:**
- Early test scenario generation improved overall test coverage
- Automated test code generation accelerated test execution
- Continuous integration of test reporting provided real-time visibility
- Cross-functional collaboration enhanced defect resolution speed

**Areas for Improvement:**
- Test data preparation took longer than estimated
- Environment configuration issues caused delays
- Better upfront requirement analysis could reduce requirement-related defects
- Test automation coverage should be increased to 90%

**Process Improvements:**
- Implement test data management strategy
- Establish dedicated test environment earlier in cycle
- Enhance requirement review process
- Invest in test automation infrastructure

## 🔄 Post-Closure Actions
1. **Immediate**: Fix and verify 5 critical defects
2. **Short-term**: Address 12 major defects in next sprint
3. **Long-term**: Implement process improvements identified in lessons learned
4. **Continuous**: Monitor production metrics for 30 days post-release

---
**Report Generated**: 2025-12-31  
**Test Manager**: STLC Manager AI  
**Approved By**: [Pending]  
**Next Review Date**: [Post Defect Resolution]
"""


# Sample metrics for testing
SAMPLE_METRICS = {
    "total_sessions": 15,
    "date_range": {
        "start": "2025-11-01",
        "end": "2025-12-31"
    },
    "models_used": ["gemini-1.5-flash", "llama3.2:3b", "qwen2.5:7b"],
    "test_scenarios": {
        "total": 58,
        "by_category": {
            "functional": 35,
            "security": 12,
            "performance": 11
        },
        "by_type": {
            "positive": 42,
            "negative": 16
        }
    },
    "test_cases": {
        "total_generated": 245,
        "total_optimized": 198,
        "optimization_rate": 0.808
    },
    "test_execution": {
        "total_executed": 245,
        "passed": 198,
        "failed": 32,
        "blocked": 15,
        "pass_rate": 0.808,
        "code_coverage": 0.78
    }
}


def test_quality_evaluation():
    """Test the quality evaluation functionality"""
    logger.info("=" * 80)
    logger.info("TESTING TEST CLOSURE REPORT QUALITY EVALUATION")
    logger.info("=" * 80)
    
    # Test the quality evaluation
    logger.info("\n[1/3] Evaluating sample closure report...")
    quality_result = test_closure_service.evaluate_closure_report_quality(
        report_content=SAMPLE_CLOSURE_REPORT,
        metrics=SAMPLE_METRICS
    )
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("QUALITY EVALUATION RESULTS")
    logger.info("=" * 80)
    
    logger.info(f"\n📊 Overall Score: {quality_result['overall_score']:.4f} ({quality_result['overall_score']*100:.2f}%)")
    logger.info("\n📋 Individual Metrics:")
    logger.info(f"  ✓ Completeness:  {quality_result['completeness']:.4f} ({quality_result['completeness']*100:.2f}%)")
    logger.info(f"  ✓ Coverage:      {quality_result['coverage']:.4f} ({quality_result['coverage']*100:.2f}%)")
    logger.info(f"  ✓ Clarity:       {quality_result['clarity']:.4f} ({quality_result['clarity']*100:.2f}%)")
    logger.info(f"  ✓ Depth:         {quality_result['depth']:.4f} ({quality_result['depth']*100:.2f}%)")
    logger.info(f"  ✓ Consistency:   {quality_result['consistency']:.4f} ({quality_result['consistency']*100:.2f}%)")
    
    logger.info("\n⚖️  Weights Used:")
    weights = quality_result['weights_used']
    for metric, weight in weights.items():
        logger.info(f"  • {metric.capitalize()}: {weight:.2f}")
    
    logger.info("\n📈 Calculation Details:")
    details = quality_result['calculation_details']
    logger.info(f"  • Total Sentences: {details.get('total_sentences', 'N/A')}")
    logger.info(f"  • Sections Required: {details.get('sections_required', 'N/A')}")
    logger.info(f"  • Sections Present: {details.get('sections_present', 'N/A')}")
    logger.info(f"  • Sections Detected: {', '.join(details.get('sections_detected', []))}")
    
    # Quality assessment
    logger.info("\n" + "=" * 80)
    logger.info("QUALITY ASSESSMENT")
    logger.info("=" * 80)
    
    overall = quality_result['overall_score']
    if overall >= 0.85:
        logger.info("✅ EXCELLENT: Report quality is outstanding")
    elif overall >= 0.70:
        logger.info("✅ GOOD: Report quality is acceptable")
    elif overall >= 0.50:
        logger.info("⚠️  FAIR: Report needs improvement")
    else:
        logger.info("❌ POOR: Report quality is insufficient")
    
    # Specific recommendations
    logger.info("\n💡 Recommendations:")
    if quality_result['completeness'] < 0.80:
        logger.info("  • Add missing sections to improve completeness")
    if quality_result['coverage'] < 0.70:
        logger.info("  • Include more references to test execution data")
    if quality_result['clarity'] < 0.70:
        logger.info("  • Reduce ambiguous language and improve readability")
    if quality_result['depth'] < 0.70:
        logger.info("  • Add more analytical content with root cause analysis")
    if quality_result['consistency'] < 0.80:
        logger.info("  • Ensure numeric values are consistent and accurate")
    
    if all(v >= 0.70 for v in [
        quality_result['completeness'],
        quality_result['coverage'],
        quality_result['clarity'],
        quality_result['depth'],
        quality_result['consistency']
    ]):
        logger.info("  ✅ All metrics are within acceptable ranges!")
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    
    return quality_result


if __name__ == "__main__":
    try:
        result = test_quality_evaluation()
        print(f"\n✅ Test completed. Overall quality score: {result['overall_score']:.4f}")
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
