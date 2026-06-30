import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy environment keys for testing so BaseAgent doesn't crash on init
os.environ["GEMINI_API_KEY"] = "dummy_key"

from src.agents.qa_agent import QAAgent

class TestQAAgentConsistency(unittest.TestCase):
    def setUp(self):
        self.qa_agent = QAAgent()

    def test_consistency_matching_by_id_and_label(self):
        vision_dict = {
            "page_name": "Checkout Flow",
            "elements": [
                {"id": "btn_checkout", "type": "button", "label": "Proceed to Checkout", "description": ""},
                {"id": "input_email", "type": "input", "label": "Email Address", "description": ""},
                {"id": "icon_logo", "type": "icon", "label": "Company Logo", "description": ""} # Missing element
            ]
        }
        
        # Test case: both btn_checkout (id) and Email Address (label) are referenced in main flow
        srs_dict = {
            "functional_requirements": [
                {
                    "id": "FR-1",
                    "name": "Checkout process",
                    "description": "Allows users to purchase products.",
                    "main_flow": [
                        "User inputs their Email Address and details.",
                        "User clicks the btn_checkout to complete payment."
                    ]
                }
            ]
        }
        
        checks = self.qa_agent._consistency_check(vision_dict, srs_dict)
        
        # We expect only 1 warning (for the "Company Logo" icon_logo, since it is not referenced anywhere)
        # The other two elements (btn_checkout and Email Address) should match successfully.
        self.assertEqual(len(checks), 1)
        self.assertIn("company logo", checks[0].message.lower())

if __name__ == "__main__":
    unittest.main()
