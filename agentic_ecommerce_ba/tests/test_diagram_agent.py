import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.diagram_agent import sanitize_mermaid

class TestDiagramAgentSanitizer(unittest.TestCase):
    def test_nested_quotes_flowchart(self):
        # Mermaid code containing nested quotes like: Start("('Start')")
        # Should NOT be corrupted to Start("'"('Start'")")
        mermaid_in = """flowchart TD
    Start("('Start')") --> UserAccess{"Guest or Registered User?"}
    UserAccess -- Guest --> BrowseGuest["Browse Products as Guest"]
    BrowseGuest --> AddToCart["Add to Cart"]"""
        
        expected_out = """flowchart TD
    Start("('Start')") --> UserAccess{"Guest or Registered User?"}
    UserAccess -- Guest --> BrowseGuest["Browse Products as Guest"]
    BrowseGuest --> AddToCart["Add to Cart"]"""
        
        self.assertEqual(sanitize_mermaid(mermaid_in), expected_out)

    def test_unquoted_flowchart_shapes(self):
        # Unquoted shape labels should be wrapped in quotes
        mermaid_in = """flowchart TD
    A(Round Shape) --> B[Rectangle Shape]
    B --> C{Decision Shape}
    C --> D([Stadium Shape])"""
        
        expected_out = """flowchart TD
    A("Round Shape") --> B["Rectangle Shape"]
    B --> C{"Decision Shape"}
    C --> D(["Stadium Shape"])"""
        
        self.assertEqual(sanitize_mermaid(mermaid_in), expected_out)

    def test_quoted_flowchart_shapes(self):
        # Quoted shape labels should remain unchanged
        mermaid_in = """flowchart TD
    A("Already Quoted") --> B['Single Quoted']
    B --> C["Another Quoted"]"""
        
        expected_out = """flowchart TD
    A("Already Quoted") --> B['Single Quoted']
    B --> C["Another Quoted"]"""
        
        self.assertEqual(sanitize_mermaid(mermaid_in), expected_out)

    def test_sequence_diagram_unaffected(self):
        # Sequence diagrams should remain completely unaffected
        mermaid_in = """sequenceDiagram
    participant User
    participant System
    User->>System: Access Page"""
        
        self.assertEqual(sanitize_mermaid(mermaid_in), mermaid_in)

if __name__ == "__main__":
    unittest.main()
