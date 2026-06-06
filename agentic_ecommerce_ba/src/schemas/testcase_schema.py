from pydantic import BaseModel, Field
from typing import List

class TestCaseStep(BaseModel):
    step_number: int = Field(..., description="Step number")
    action: str = Field(..., description="Action to be performed by the user or system")
    expected_result: str = Field(..., description="Expected outcome of this specific step")

class TestCase(BaseModel):
    test_id: str = Field(..., description="Unique ID for the test case, e.g., TC-UC01-01")
    scenario: str = Field(..., description="A brief description of the scenario being tested")
    test_type: str = Field(..., description="Type of test (e.g., Functional, Boundary, Edge Case, Negative, UI)")
    priority: str = Field(..., description="Priority of the test (High / Medium / Low)")
    precondition: str = Field(..., description="Conditions that must be met before executing the test")
    steps: List[TestCaseStep] = Field(..., description="List of step-by-step actions and expected results")
    final_expected_result: str = Field(..., description="The overall expected result of the test case")
    automation_hint: str = Field(..., description="Hint for QA Automation (e.g., suggested CSS selectors like cy.get('#submit-btn') or API endpoint validation)")
    bdd_gherkin: str = Field(..., description="The test case formatted in BDD Gherkin syntax (Given... When... Then...)")

class TestCaseDocument(BaseModel):
    test_cases: List[TestCase] = Field(..., description="A list of generated comprehensive test cases derived from the SRS")
