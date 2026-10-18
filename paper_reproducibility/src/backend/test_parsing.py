#!/usr/bin/env python3

# Test our text parsing algorithm
test_response = """Here are some detailed test cases for the `TS_001` scenario:
**Test Case 1: Successful Task Creation**
* **Test Name:** TC_001_01
* **Preconditions:** User is logged in with valid credentials.
* **Steps:**
        1. Navigate to the task creation page.
        2. Fill in the task title and description fields.
        3. Select a task type from the dropdown menu.
        4. Set the due date and time for the task.
        5. Click the "Create Task" button.
* **Expected Result:** The task is successfully created, and the user is redirected to the task list page with the newly created task displayed.

**Test Case 2: Invalid Task Title**
* **Test Name:** TC_001_02
* **Preconditions:** User is logged in with valid credentials.
* **Steps:**
        1. Navigate to the task creation page.
        2. Leave the task title field empty.
        3. Fill in the rest of the task details (description, type, due date, etc.).
        4. Click the "Create Task" button.
* **Expected Result:** An error message is displayed indicating that the task title cannot be empty.

**Test Case 3: Task Creation with Maximum Characters**
* **Test Name:** TC_001_03
* **Preconditions:** User is logged in with valid credentials.
* **Steps:**
        1. Navigate to the task creation page.
        2. Fill in the task title with maximum allowed characters (e.g., 255 characters).
        3. Fill in the description with maximum allowed characters.
        4. Set the due date and time for the task.
        5. Click the "Create Task" button.
* **Expected Result:** The task is successfully created with the provided details, and the user is redirected to the task list page."""

def parse_text_test_cases(response, scenario_id="TS_001"):
    test_cases = []
    
    # Split by test case markers
    import re
    # Find all test case sections
    pattern = r'\*\*Test Case \d+:([^\*]+?)\*\*(?:\s*\n)?(.*?)(?=\*\*Test Case \d+:|$)'
    matches = re.findall(pattern, response, re.DOTALL)
    
    print(f"Found {len(matches)} test case matches")
    
    for idx, (title, content) in enumerate(matches):
        title = title.strip()
        print(f"\nTest Case {idx+1}: {title}")
        
        test_case = {
            "ScenarioID": scenario_id,
            "TestCaseID": f"TC_{idx+1:03d}",
            "Title": title,
            "Description": "",
            "Objective": "",
            "Category": "Generated",
            "Priority": "Medium",  
            "Prerequisites": [],
            "TestSteps": [],
            "ExpectedResults": "",
            "TestData": "",
            "Comments": "Parsed from text response"
        }
        
        # Parse content
        lines = content.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            print(f"  Processing line: {line[:60]}...")
            
            # Extract test name/ID
            if line.startswith('* **Test Name:**'):
                tc_id = line.replace('* **Test Name:**', '').strip()
                if tc_id:
                    test_case["TestCaseID"] = tc_id
                    
            # Extract preconditions
            elif line.startswith('* **Preconditions:**'):
                prereq = line.replace('* **Preconditions:**', '').strip()
                if prereq:
                    test_case["Prerequisites"].append(prereq)
                    
            # Extract steps
            elif line.startswith('* **Steps:**'):
                current_field = "steps"
            elif current_field == "steps" and re.match(r'^\s*\d+\.', line):
                step = re.sub(r'^\s*\d+\.\s*', '', line).strip()
                if step:
                    test_case["TestSteps"].append(step)
                    
            # Extract expected results
            elif line.startswith('* **Expected Result:**'):
                result = line.replace('* **Expected Result:**', '').strip()
                test_case["ExpectedResults"] = result
        
        test_cases.append(test_case)
        
        print(f"  Final TestCaseID: {test_case['TestCaseID']}")
        print(f"  Prerequisites: {len(test_case['Prerequisites'])}")
        print(f"  Test Steps: {len(test_case['TestSteps'])}")
        print(f"  Expected Results: {test_case['ExpectedResults'][:50]}...")

    return test_cases

# Test the parsing
result = parse_text_test_cases(test_response)
print(f"\n=== FINAL RESULT ===")
print(f"Parsed {len(result)} test cases")
for tc in result:
    print(f"- {tc['TestCaseID']}: {tc['Title']} ({len(tc['TestSteps'])} steps)")
