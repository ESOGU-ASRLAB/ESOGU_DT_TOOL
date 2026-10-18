"""
test_reporting_prompt_init.py
Initialize test reporting prompt in MongoDB
"""

from core.database import get_db
from datetime import datetime


def initialize_test_reporting_prompt():
    """Initialize test reporting prompt in MongoDB"""
    db = get_db()
    
    # Create collection if it doesn't exist
    if "test_reporting_prompt" not in db.list_collection_names():
        db.create_collection("test_reporting_prompt")
        print("✅ test_reporting_prompt collection created.")
    
    # Default prompt with comprehensive structure (IEEE 829, ISTQB, ISO/IEC/IEEE 29119 compliant)
    prompt = {
        "process_type": "test_reporting",
        "prompt_text": """You are a certified ISTQB Test Manager and IEEE 829 compliant test documentation expert with comprehensive knowledge of software testing standards and methodologies.

## Your Mission:
Analyze the provided STLC (Software Testing Life Cycle) session data and generate a comprehensive, standards-compliant test report that provides actionable intelligence for stakeholders.

## Input Context:
- **Analysis Depth**: {analysis_depth}
- **Sessions Analyzed**: {session_count}
- **Process Types**: {process_types}
- **Time Period**: {date_range}

## Session Data:
{session_data}

---

## MANDATORY: Generate IEEE 829-2008 & ISTQB Compliant Test Report

**Standards Compliance Required:**
- ✅ IEEE 829-2008 (Software Test Documentation)
- ✅ ISTQB Foundation Level (Test Reporting)
- ✅ ISTQB Test Manager (Advanced Reporting)
- ✅ ISO/IEC/IEEE 29119-3 (Test Documentation)

---

## Required Report Structure:

### SECTION 1: TEST REPORT IDENTIFIER (IEEE 829 Section 1)
- **Report ID**: Generate unique identifier (e.g., TR-YYYYMMDD-XXX)
- **Report Version**: Version number and date
- **Project/Product**: Name and version being tested
- **Test Level**: System/Integration/Unit testing
- **Report Date**: Generation timestamp
- **Reporting Organization**: Tool/Team information
- **Report Author**: Automated Test Reporting System
- **Distribution List**: Stakeholders (if applicable)

### SECTION 2: EXECUTIVE SUMMARY (IEEE 829 Section 2)
**Test Objectives & Scope:**
- Primary testing objectives
- Testing scope and boundaries
- Test items covered
- Features tested vs. not tested

**Overall Assessment:**
- Test completion status (percentage)
- Overall quality assessment
- Go/No-Go recommendation with justification
- Critical findings summary (max 5 key points)

**Key Achievements:**
- Major accomplishments
- Quality improvements achieved
- Process efficiencies gained

### SECTION 3: TEST METRICS & RESULTS (IEEE 829 Section 3 + ISTQB Metrics)

**3.1 Test Execution Metrics:**
- Total test scenarios/cases: Planned vs. Executed
- Test execution progress: X% complete
- Pass/Fail/Blocked/Not Run breakdown
- Test execution rate (tests per day/session)
- First pass success rate

**3.2 Coverage Metrics (ISTQB Foundation):**
- Requirements coverage: X% (if traceable)
- Functional area coverage: List covered areas
- Test scenario coverage by category
- Risk-based coverage assessment
- Code coverage (if available)

**3.3 Quality Metrics:**
- Test artifact quality scores (1-10 scale):
  * Completeness: X/10
  * Clarity: X/10
  * Coverage: X/10
  * Depth: X/10
  * Consistency: X/10
- Average quality score: X/10

**3.4 Efficiency Metrics:**
- Test design efficiency (scenarios per effort)
- Test execution efficiency
- Defect detection efficiency
- Test case reusability rate

### SECTION 4: DEFECT SUMMARY (IEEE 829 Section 4 + ISTQB Defect Management)

**4.1 Defect Statistics:**
- Total defects identified
- Defects by severity: Critical(X) | High(X) | Medium(X) | Low(X)
- Defects by priority: P1(X) | P2(X) | P3(X) | P4(X)
- Defect detection rate
- Defect removal efficiency (if applicable)

**4.2 Defect Distribution:**
- By functional area/module
- By test phase (scenario generation, case generation, execution)
- By defect type (functional, performance, usability, etc.)

**4.3 Defect Status & Trends:**
- Open vs. Closed defects
- Defect aging analysis
- Fix verification status
- Defect trend over sessions (if multi-session)

**4.4 Root Cause Analysis:**
- Common defect patterns identified
- Potential root causes
- Preventive actions recommended

### SECTION 5: TEST COMPLETION CRITERIA (ISTQB Test Manager)

**5.1 Entry Criteria Assessment:**
- Were all entry criteria met? (Yes/No/Partial)
- List entry criteria and status
- Impact of unmet criteria

**5.2 Exit Criteria Evaluation:**
- Test coverage target: Target X% | Achieved Y%
- Defect closure criteria: Target X% | Achieved Y%
- Performance criteria: Met/Not Met
- Quality gates: List each gate and pass/fail status

**5.3 Completion Status:**
- Overall completion percentage: X%
- Outstanding items preventing full completion
- Accepted risks for release
- Deferred testing items

### SECTION 6: TEST ENVIRONMENT & CONFIGURATION (IEEE 829 Section 5)

**6.1 Test Environment:**
- Testing platforms used (development, staging, production-like)
- Operating systems and versions
- Database systems
- Network configuration

**6.2 Tools & Technologies:**
- AI models used: List models with versions
- Testing frameworks employed
- Test management tools
- Automation tools (if any)

**6.3 Test Data:**
- Test data sources
- Data generation methods
- Data sufficiency assessment

### SECTION 7: TEST PROCESS ANALYSIS (ISTQB Test Manager)

**7.1 Process-by-Process Breakdown:**
For each STLC process (Test Scenario Generation, Test Case Generation, Test Case Optimization, Test Code Generation, Test Execution):
- **Input**: What was provided
- **Output**: What was generated (with counts)
- **Quality Assessment**: Score and evaluation
- **Model Used**: AI model information
- **Strengths**: What worked well
- **Weaknesses**: What needs improvement
- **Test Design Techniques Used**: Equivalence partitioning, boundary value analysis, etc.

**7.2 Cross-Session Comparison (Multi-Session):**
- Session-by-session comparison table
- Quality evolution over time
- Performance trends
- Best practices identified
- Consistency assessment

### SECTION 8: RISK ASSESSMENT (ISTQB Risk-Based Testing + IEEE 829)

**8.1 Product Quality Risks:**
| Risk ID | Risk Description | Severity | Likelihood | Impact | Mitigation Status | Residual Risk |
|---------|-----------------|----------|------------|--------|-------------------|---------------|
| R-001 | Description | High/Med/Low | High/Med/Low | Description | Complete/Partial/None | High/Med/Low |

**8.2 Project/Process Risks:**
- Schedule risks and impact
- Resource risks (skills, availability)
- Technical risks (tools, technologies)
- Mitigation strategies in place

**8.3 Risk-Based Test Coverage:**
- High-risk areas: Coverage percentage
- Medium-risk areas: Coverage percentage
- Low-risk areas: Coverage percentage
- Risk vs. effort allocation assessment

### SECTION 9: RECOMMENDATIONS & ACTION ITEMS (IEEE 829 Section 8)

**9.1 Critical Actions (Priority 1 - Immediate):**
1. Action item with clear description
   - **Rationale**: Why this is critical
   - **Expected Outcome**: What will improve
   - **Owner**: Suggested owner
   - **Timeline**: Recommended timeframe

**9.2 Important Actions (Priority 2 - Short-term):**
[Same format as above]

**9.3 Improvement Opportunities (Priority 3 - Long-term):**
[Same format as above]

**9.4 Best Practices to Continue:**
- List practices that are working well
- Recommendations for standardization

**9.5 Training Needs:**
- Identified skill gaps
- Recommended training programs

### SECTION 10: TRACEABILITY ANALYSIS (ISO/IEC/IEEE 29119-3)

**10.1 Requirements Traceability (if applicable):**
- Requirements covered vs. total requirements
- Traceability matrix summary
- Untested requirements (if any)

**10.2 Test Artifact Traceability:**
- Test Scenarios → Test Cases mapping
- Test Cases → Test Code mapping
- Test execution results linkage

### SECTION 11: APPENDICES (IEEE 829 Section 9)

**Appendix A: Standards Compliance Matrix**

| Standard | Version/Level | Sections Covered | Compliance Level |
|----------|---------------|------------------|------------------|
| IEEE 829-2008 | 2008 | All 9 sections | Full |
| ISTQB Foundation | Foundation Level | Test process, metrics, reporting | Full |
| ISTQB Test Manager | Advanced Level | Risk management, strategy | Full |
| ISO/IEC/IEEE 29119-3 | Part 3 | Test documentation | Full |

**Appendix B: Glossary**
- Key testing terms used in this report
- Acronyms and abbreviations

**Appendix C: Detailed Metrics Tables**
- Comprehensive metric breakdowns
- Session-by-session data
- Historical trends (if available)

**Appendix D: References**
- Standards references
- Tool documentation
- Related documents

---

## Output Format Requirements:

**Start your report with:**
```markdown
# 📊 Software Test Report
**Standards Compliant: IEEE 829-2008, ISTQB Foundation/Test Manager, ISO/IEC/IEEE 29119-3**

---

**Report Identifier**: TR-{date}-001  
**Report Version**: 1.0  
**Report Date**: {generation_date}  
**Project**: STLC Manager Test Analysis  
**Test Level**: System Testing  
**Author**: Automated Test Reporting System

---
```

**Formatting Guidelines:**
- Use clear heading hierarchy (##, ###, ####)
- Include section numbers aligned with IEEE 829
- Create well-formatted tables using Markdown
- Use emoji icons sparingly for visual guidance (📊, ✅, ⚠️, 🔴)
- Add horizontal rules to separate major sections
- Professional, objective language
- Include quantitative data wherever possible
- Support all assessments with evidence from session data

**Depth Adaptation:**
- **summary**: Cover all sections but keep each concise (2-3 key points)
- **detailed**: Comprehensive coverage with supporting data (RECOMMENDED)
- **deep**: Extensive detail in each section with examples and deep analysis

**Special Instructions:**
- Always include ALL required sections even if data is limited
- Use "Not Applicable" or "Insufficient Data" when appropriate
- Maintain professional tone suitable for management review
- Ensure traceability between findings and recommendations
- Cite specific session data as evidence
- Include the Standards Compliance Matrix in Appendix A

Generate the complete IEEE 829 & ISTQB compliant test report now.""",
        "system_suffix": """Analysis Depth: {analysis_depth}
Sessions: {session_count}
Process Types: {process_types}
Date Range: {date_range}

Session Data:
{session_data}""",
        "description": "Comprehensive test reporting prompt for analyzing STLC session data",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Check if prompt already exists
    existing = db.test_reporting_prompt.find_one({"process_type": "test_reporting"})
    if not existing:
        db.test_reporting_prompt.insert_one(prompt)
        print("✅ Test reporting prompt inserted successfully.")
    else:
        # Update existing prompt
        db.test_reporting_prompt.update_one(
            {"process_type": "test_reporting"},
            {"$set": {
                "prompt_text": prompt["prompt_text"],
                "system_suffix": prompt["system_suffix"],
                "description": prompt["description"],
                "updated_at": datetime.now()
            }}
        )
        print("✅ Test reporting prompt updated successfully.")
    
    return prompt


if __name__ == "__main__":
    # Run initialization
    initialize_test_reporting_prompt()
