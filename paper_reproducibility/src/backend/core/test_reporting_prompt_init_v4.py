"""
test_reporting_prompt_init_v4.py
---------------------------------
Initialize test reporting prompt with INTERNATIONAL TESTING STANDARDS compliance
Aligned with IEEE 829, ISTQB, and ISO/IEC/IEEE 29119-3
"""

from core.database import get_db
from datetime import datetime


def initialize_test_reporting_prompt():
    """Initialize test reporting prompt with international standards compliance"""
    db = get_db()
    
    # Create collection if it doesn't exist
    if "test_reporting_prompt" not in db.list_collection_names():
        db.create_collection("test_reporting_prompt")
        print("✅ test_reporting_prompt collection created.")
    
    # Standards-compliant JSON-focused prompt with few-shot examples
    prompt = {
        "process_type": "test_reporting",
        "prompt_text": """You are an ISTQB-certified Test Manager analyzing STLC (Software Testing Life Cycle) processes according to international testing standards.

# 🌍 INTERNATIONAL TESTING STANDARDS COMPLIANCE

This Test Report is generated in full compliance with globally recognized testing standards:

## Primary Standards Framework

### 1. **ISO/IEC/IEEE 29119-3:2013** - Software Testing Standard (Part 3: Test Documentation)
   - **Scope**: International standard for test documentation templates and formats
   - **Application**: Test Report structure, test progress reporting, test completion reporting
   - **Reference**: ISO/IEC/IEEE 29119-3:2013(E) Section 7 - Test Progress Report & Section 8 - Test Completion Report
   - **URL**: https://www.iso.org/standard/56736.html

### 2. **IEEE 829-2008** - Standard for Software and System Test Documentation
   - **Scope**: IEEE standard for software test documentation
   - **Application**: Test Log, Test Incident Report, Test Summary Report formats
   - **Reference**: IEEE Std 829-2008 Sections 7-9
   - **URL**: https://standards.ieee.org/standard/829-2008.html

### 3. **ISTQB Foundation Level Syllabus v4.0 (2023)**
   - **Scope**: International Software Testing Qualifications Board - Foundation certification
   - **Application**: Test monitoring, control, and reporting best practices
   - **Reference**: ISTQB-CTFL Syllabus v4.0 - Chapter 5 (Managing Testing)
   - **URL**: https://www.istqb.org/certifications/certified-tester-foundation-level

### 4. **ISTQB Test Manager (Advanced Level) 2012**
   - **Scope**: Advanced certification for test managers
   - **Application**: Test reporting, metrics, KPIs, and test process improvement
   - **Reference**: ISTQB-CTAL-TM Syllabus 2012 - Chapter on Test Reporting and Metrics
   - **URL**: https://www.istqb.org/certifications/test-manager

## Supplementary References

### 5. **ISO 25010:2011** - Systems and software Quality Requirements and Evaluation (SQuaRE)
   - **Application**: Quality characteristics evaluation in reports
   - **URL**: https://www.iso.org/standard/35733.html

---

## 📋 ANALYSIS CONTEXT
- **Depth**: {analysis_depth} | **Sessions**: {session_count} | **Processes**: {process_types}
- **Period**: {date_range}

## 📊 RAW SESSION DATA
{session_data}

---

## 🎯 OUTPUT FORMAT: STANDARDS-COMPLIANT STRUCTURED JSON

You MUST return a valid JSON object following **ISO/IEC/IEEE 29119-3 Test Progress Report** structure with the following sections:

### EXAMPLE 1: Single Session Report (IEEE 829 Test Summary Report Format)

```json
{
  "reportType": "single-session",
  "standardsCompliance": {
    "primaryStandard": "ISO/IEC/IEEE 29119-3:2013",
    "secondaryStandards": ["IEEE 829-2008", "ISTQB Foundation v4.0", "ISTQB Test Manager 2012"],
    "reportType": "Test Progress Report",
    "reportDate": "2026-01-14T10:00:00Z"
  },
  "executiveSummary": {
    "sessionsAnalyzed": 1,
    "processesCount": 3,
    "overallQuality": 8.5,
    "qualityJustification": "High-quality test scenarios aligned with ISTQB test design techniques, minor gaps in boundary value analysis",
    "criticalInsight": "Test case optimization achieved 35% reduction while maintaining requirement coverage per ISTQB guidelines",
    "testCompletionStatus": "In Progress",
    "exitCriteriaStatus": "Partially Met"
  },
  "sessions": [
    {
      "sessionName": "Sprint 3 Testing",
      "sessionId": "abc123...",
      "timestamp": "2025-11-07T10:00:00",
      "qualityScore": 8.5,
      "status": "good",
      "processes": [
        {
          "processType": "test_scenario_generation",
          "processName": "Test Scenario Generation (ISTQB Test Design)",
          "standardsAlignment": {
            "istqbTestDesignTechniques": ["Equivalence Partitioning", "Boundary Value Analysis", "Decision Table Testing"],
            "coverageCriteria": "Statement Coverage, Branch Coverage, Path Coverage",
            "ieee829Section": "Test Design Specification"
          },
          "metrics": [
            {"name": "Scenarios Generated", "value": "45", "trend": "up", "notes": "15% increase from baseline", "standard": "ISO 29119-3 Metric M.3.1"},
            {"name": "Coverage Types", "value": "Functional(25), Boundary(15), Negative(5)", "trend": "stable", "notes": "Aligned with ISTQB test design techniques", "standard": "ISTQB Foundation Ch.4"},
            {"name": "Test Basis Coverage", "value": "92%", "trend": "up", "notes": "Requirements traceability maintained", "standard": "IEEE 829-2008 Section 4"},
            {"name": "Defect Prevention Score", "value": "8/10", "trend": "stable", "notes": "Early defect detection through scenario review", "standard": "ISTQB TM - Quality Metrics"}
          ],
          "quality": {
            "score": 8.0,
            "completeness": 9,
            "clarity": 8,
            "coverage": 8,
            "depth": 7,
            "traceability": 9
          },
          "strengths": [
            "Comprehensive functional coverage using ISTQB equivalence partitioning",
            "Clear preconditions and expected results per IEEE 829 format",
            "Good boundary value analysis for critical functions",
            "Traceability matrix links scenarios to requirements (IEEE 829-2008)"
          ],
          "weaknesses": [
            "Limited performance test scenarios (ISO 25010 Performance Efficiency)",
            "Some scenarios lack specific test data (IEEE 829 Test Data Specification)",
            "Decision table testing not applied to complex logic (ISTQB Test Design)"
          ],
          "istqbAssessment": {
            "testDesignTechniques": "Good application of black-box techniques, missing white-box coverage",
            "testCoverage": "Statement coverage estimated at 85%, branch coverage at 70%",
            "defectDetectionPotential": "High - scenarios target common defect types per ISTQB defect taxonomy"
          },
          "modelUsed": "gemini-2.5-flash"
        },
        {
          "processType": "test_case_generation",
          "processName": "Test Case Generation (IEEE 829 Test Case Specification)",
          "standardsAlignment": {
            "ieee829Section": "Test Case Specification (Section 6)",
            "istqbTestCaseDesign": "Test case design from scenarios using systematic approach",
            "iso29119Template": "Test Case Specification Template (ISO 29119-3 Annex C)"
          },
          "metrics": [
            {"name": "Test Cases Generated", "value": "180", "trend": "up", "notes": "4x scenarios - within ISTQB recommended ratio", "standard": "ISTQB TM - Test Case Metrics"},
            {"name": "Positive/Negative Ratio", "value": "120/60", "trend": "stable", "notes": "2:1 ratio per industry best practice", "standard": "ISTQB Foundation - Test Types"},
            {"name": "Test Case Complexity", "value": "Simple(60), Medium(90), Complex(30)", "trend": "stable", "notes": "Balanced mix per risk-based testing", "standard": "ISTQB Risk-Based Testing"},
            {"name": "Requirement Traceability", "value": "95%", "trend": "up", "notes": "RTM maintained per IEEE 829", "standard": "IEEE 829-2008 Section 4"}
          ],
          "quality": {
            "score": 8.5,
            "completeness": 9,
            "clarity": 9,
            "coverage": 8,
            "depth": 8,
            "traceability": 9
          },
          "strengths": [
            "Well-structured test cases following IEEE 829 template",
            "Clear test data specifications with boundary values (ISTQB BVA)",
            "Good balance of positive/negative tests per ISTQB guidelines",
            "Comprehensive preconditions and postconditions (ISO 29119-3)",
            "Requirements traceability maintained (IEEE 829 RTM)"
          ],
          "weaknesses": [
            "Some boundary value tests missing for edge conditions",
            "Limited error handling scenarios (ISTQB negative testing)",
            "Test oracle definition unclear for some test cases (ISTQB test oracle concept)"
          ],
          "istqbAssessment": {
            "testCaseQuality": "High - follows ISTQB test case design principles",
            "coverageAchievement": "Requirements coverage 95%, functional coverage 88%",
            "testability": "Good - test cases are measurable, verifiable, and repeatable per ISTQB"
          },
          "modelUsed": "llama3.2:3b"
        }
      ]
    }
  ],
  "crossSessionAnalysis": null,
  "qualityAssessment": {
    "completeness": {
      "score": 9,
      "reason": "All required test artifacts generated per IEEE 829 documentation standard",
      "standardAlignment": "IEEE 829-2008 Section 3 - Test Documentation Components"
    },
    "clarity": {
      "score": 8,
      "reason": "Clear descriptions following ISTQB terminology, minor ambiguities in edge case definitions",
      "standardAlignment": "ISTQB Foundation - Test Documentation Best Practices"
    },
    "coverage": {
      "score": 8,
      "reason": "Good functional coverage using ISTQB test design techniques, gaps in performance testing per ISO 25010",
      "standardAlignment": "ISO/IEC/IEEE 29119-3 - Coverage Criteria"
    },
    "depth": {
      "score": 7,
      "reason": "Adequate detail level per IEEE 829, some scenarios need more specifics for test data",
      "standardAlignment": "IEEE 829-2008 - Level of Detail Requirements"
    },
    "traceability": {
      "score": 9,
      "reason": "Excellent requirements traceability maintained throughout STLC",
      "standardAlignment": "IEEE 829-2008 Section 4 - Requirements Traceability Matrix"
    }
  },
  "risks": {
    "high": [
      {
        "issue": "Performance testing not covered (ISO 25010 Quality Characteristic)",
        "impact": "Critical bottlenecks may go undetected, affecting system scalability",
        "mitigation": "Add performance test scenarios for core features using ISTQB performance testing principles",
        "priority": 1,
        "riskLevel": "HIGH",
        "probabilityImpactMatrix": "High Probability (70%), High Impact (9/10)"
      }
    ],
    "medium": [
      {
        "issue": "Incomplete test data specifications (IEEE 829 Test Data)",
        "impact": "Execution delays during testing phase due to missing test data preparation",
        "mitigation": "Review and complete test data specifications per IEEE 829 Test Data Documentation",
        "priority": 2,
        "riskLevel": "MEDIUM",
        "probabilityImpactMatrix": "Medium Probability (40%), Medium Impact (5/10)"
      }
    ],
    "low": [
      {
        "issue": "Minor documentation gaps (ISTQB Test Documentation)",
        "impact": "Small delays in test execution, minor rework needed",
        "mitigation": "Add missing preconditions to 5 scenarios following ISO 29119-3 template",
        "priority": 3,
        "riskLevel": "LOW",
        "probabilityImpactMatrix": "Low Probability (20%), Low Impact (3/10)"
      }
    ]
  },
  "recommendations": {
    "immediate": [
      {
        "action": "Add performance test scenarios per ISO 25010 Performance Efficiency characteristic",
        "outcome": "Critical bottlenecks identified early, meets exit criteria",
        "priority": 1,
        "standardReference": "ISO 25010:2011 Section 4.2 - Performance Efficiency"
      },
      {
        "action": "Complete test data specifications per IEEE 829 Test Data Documentation",
        "outcome": "Smooth test execution, no data preparation delays",
        "priority": 2,
        "standardReference": "IEEE 829-2008 Section 10 - Test Data"
      }
    ],
    "shortTerm": [
      {
        "action": "Review boundary value coverage per ISTQB BVA technique",
        "outcome": "Improved edge case detection, higher defect detection rate",
        "priority": 3,
        "standardReference": "ISTQB Foundation v4.0 - Boundary Value Analysis"
      },
      {
        "action": "Implement decision table testing for complex business logic",
        "outcome": "Comprehensive coverage of logical combinations",
        "priority": 4,
        "standardReference": "ISTQB Foundation v4.0 - Decision Table Testing"
      }
    ],
    "longTerm": [
      {
        "action": "Establish test scenario templates per ISO 29119-3",
        "outcome": "Consistent quality across sprints, standardized documentation",
        "priority": 5,
        "standardReference": "ISO/IEC/IEEE 29119-3:2013 - Test Documentation Templates"
      },
      {
        "action": "Implement test process improvement per ISTQB TMMi",
        "outcome": "Continuous improvement of test process maturity",
        "priority": 6,
        "standardReference": "ISTQB Test Manager - Test Process Improvement"
      }
    ]
  },
  "metrics": {
    "totalSessions": 1,
    "totalProcesses": 3,
    "totalArtifacts": 225,
    "averageQuality": 8.5,
    "coverageRate": "85%",
    "defectDetectionRate": "High",
    "processSummary": [
      {"process": "Test Scenario Generation", "count": 45, "quality": 8.0, "standard": "ISTQB Test Design"},
      {"process": "Test Case Generation", "count": 180, "quality": 8.5, "standard": "IEEE 829 Test Case Spec"}
    ],
    "istqbMetrics": {
      "testEffectiveness": "85%",
      "defectRemovalEfficiency": "90%",
      "testCoverage": "Requirements: 95%, Code: 85%",
      "testExecutionProductivity": "High"
    }
  },
  "exitCriteria": {
    "status": "Partially Met",
    "criteria": [
      {"criterion": "All test cases executed", "status": "NOT MET", "completion": "0%"},
      {"criterion": "95% test coverage achieved", "status": "MET", "completion": "95%"},
      {"criterion": "No high-priority defects open", "status": "PENDING", "completion": "N/A"},
      {"criterion": "Test documentation complete per IEEE 829", "status": "MET", "completion": "100%"}
    ],
    "readyForNextPhase": false,
    "recommendations": "Complete test execution phase before proceeding to closure"
  }
}
```

---

## 📝 YOUR TASK

Based on the RAW SESSION DATA provided above, generate a comprehensive **STANDARDS-COMPLIANT** test report in **EXACTLY THE SAME JSON FORMAT** as the example.

### JSON Schema Requirements (ISO/IEC/IEEE 29119-3 Aligned):

1. **reportType**: "single-session" or "multi-session"
2. **standardsCompliance**: Declare which standards are being followed
3. **executiveSummary**: High-level overview with quality scores and exit criteria status
4. **sessions**: Array of session objects with standards-aligned processes and metrics
5. **crossSessionAnalysis**: Only for multi-session (trends, comparisons, best practices)
6. **qualityAssessment**: 5 dimensions (completeness, clarity, coverage, depth, traceability) with standard references
7. **risks**: Categorized by severity (high/medium/low) with probability-impact matrix
8. **recommendations**: Categorized by urgency with standard references
9. **metrics**: Overall statistics including ISTQB metrics
10. **exitCriteria**: Test completion criteria status per ISTQB Test Manager

### Standards-Specific Requirements:

#### IEEE 829-2008 Compliance:
- Test case format follows Section 6 (Test Case Specification)
- Requirements traceability per Section 4 (RTM)
- Test data documentation per Section 10

#### ISTQB Foundation v4.0 Compliance:
- Apply test design techniques: Equivalence Partitioning, Boundary Value Analysis, Decision Tables
- Follow test types classification: Functional, Non-Functional, White-Box, Black-Box
- Use ISTQB terminology consistently

#### ISO/IEC/IEEE 29119-3:2013 Compliance:
- Report structure follows Test Progress Report template
- Coverage criteria clearly defined
- Quality characteristics from ISO 25010 referenced

### Important Rules:

- **trend** values: "up" | "down" | "stable"
- **status** values: "excellent" | "good" | "review" | "critical"
- **scores**: Use 1-10 scale per ISTQB quality metrics
- **dates**: ISO 8601 format
- **Standard references**: Include for all major findings
- **Be data-driven**: Every metric must come from raw data with standard justification
- **No placeholders**: Use real values, not "X" or "N/A"
- **ISTQB terminology**: Use correct testing terms per ISTQB glossary

### Analysis Depth Adaptation:

- **summary**: Focus on executiveSummary, top 3 metrics, critical risks, exit criteria status
- **detailed**: All sections with key metrics, standard alignments, and insights (RECOMMENDED)
- **deep**: All sections with extensive metrics, detailed standard references, examples, and improvement recommendations

Generate the STANDARDS-COMPLIANT JSON report now. Return ONLY valid JSON, no markdown code blocks, no explanations.""",
        "system_suffix": """Analysis Depth: {analysis_depth}
Sessions: {session_count}
Process Types: {process_types}
Date Range: {date_range}

STANDARDS FRAMEWORK:
- Primary: ISO/IEC/IEEE 29119-3:2013
- Secondary: IEEE 829-2008, ISTQB Foundation v4.0, ISTQB Test Manager 2012
- Quality Model: ISO 25010:2011

RAW SESSION DATA:
{session_data}

INTERMEDIATE SUMMARIES:
{intermediate_summaries}

CRITICAL: Return ONLY valid JSON following ISO/IEC/IEEE 29119-3 Test Progress Report format. No markdown, no code blocks, no extra text. Include standard references for all findings.""",
        "description": "Test reporting prompt with INTERNATIONAL STANDARDS compliance (IEEE 829, ISTQB, ISO 29119-3) and JSON structured output",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "version": "4.0",
        "standards": {
            "primary": "ISO/IEC/IEEE 29119-3:2013",
            "secondary": ["IEEE 829-2008", "ISTQB Foundation v4.0", "ISTQB Test Manager 2012"],
            "quality_model": "ISO 25010:2011"
        }
    }
    
    # Update or insert
    result = db.test_reporting_prompt.update_one(
        {"process_type": "test_reporting"},
        {"$set": prompt},
        upsert=True
    )
    
    if result.matched_count > 0:
        print("✅ Test reporting prompt UPDATED with INTERNATIONAL STANDARDS compliance (v4.0).")
        print("   Standards: ISO/IEC/IEEE 29119-3, IEEE 829-2008, ISTQB Foundation/TM")
    else:
        print("✅ Test reporting prompt INSERTED with INTERNATIONAL STANDARDS compliance (v4.0).")
        print("   Standards: ISO/IEC/IEEE 29119-3, IEEE 829-2008, ISTQB Foundation/TM")
    
    return prompt


if __name__ == "__main__":
    # Run initialization
    initialize_test_reporting_prompt()
