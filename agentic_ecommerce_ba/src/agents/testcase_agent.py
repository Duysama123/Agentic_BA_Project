import os
import json
import time as _time

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.base_agent import BaseAgent
from src.schemas.testcase_schema import TestCaseDocument
from src.core.logger import setup_logger

logger = setup_logger("TestCaseAgent")

class TestCaseAgent(BaseAgent):
    def __init__(self):
        super().__init__("TestCaseAgent")
        # Use gemini-2.5-flash for downstream test case generation
        self.model_name = "gemini-2.5-flash"

    def generate_test_cases(self, srs_json: str) -> TestCaseDocument:
        """
        Takes the finalized SRS JSON string as input and generates test cases.
        """
        start_time = _time.time()
        
        system_prompt = (
            "You are a Senior QA Automation Engineer and Software Tester.\n"
            "Your task is to derive comprehensive Test Cases based strictly on the provided Software Requirements Specification (SRS).\n"
            "Ensure you cover main flows, alternative flows, and exception paths mentioned in the SRS.\n"
            "For each test case, you MUST provide:\n"
            "- A unique ID (e.g., TC-01)\n"
            "- Test Type (Functional, Boundary, Edge Case, UI, Negative)\n"
            "- Priority (High/Medium/Low)\n"
            "- Precondition and clear step-by-step Actions.\n"
            "- Final Expected Result.\n"
            "- 'automation_hint': A CSS selector or API hint for automated testing (e.g. `cy.get('#btn-submit').click()` or `POST /api/checkout`).\n"
            "- 'bdd_gherkin': The test scenario formatted cleanly in Given/When/Then syntax.\n"
            "Do NOT make up features that are not in the SRS. Focus on validation rules, error handling, and business logic described."
        )

        user_prompt = f"Here is the SRS in JSON format:\n{srs_json}\n\nPlease generate a comprehensive set of test cases."

        try:
            result = self.call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                pydantic_schema=TestCaseDocument
            )
            
            elapsed = round(_time.time() - start_time, 2)
            self.last_run_metadata = {
                "time": elapsed,
                "tokens": 0 # Handled in call_llm
            }
            logger.info(f"Test Cases generated in {elapsed}s.")
            return result
        except Exception as e:
            logger.error(f"Failed to generate Test Cases: {e}")
            raise e
