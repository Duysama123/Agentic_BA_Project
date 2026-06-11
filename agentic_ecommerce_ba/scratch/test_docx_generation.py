import os
import sys
import json

# Add project src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.document_exporter import generate_srs_docx, convert_docx_to_pdf

def test_generation():
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "srs_template-ieee.docx"))
    docx_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Test_Output.docx"))
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Test_Output.pdf"))
    image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_files", "sample_wireframe_1.png"))
    
    print("Testing document generation...")
    print("Template:", template_path)
    print("Output DOCX:", docx_path)
    print("Output PDF:", pdf_path)
    print("Mockup Image:", image_path)
    
    # Mock BA Data
    ba_data = {
        "system_name": "E-Commerce System",
        "version": "1.0.0",
        "author": "Antigravity Test Suite",
        "organization": "Graduation Thesis Test Team",
        "introduction": {
            "purpose": "This is a test purpose description for document verification.",
            "glossary": [
                {"term": "SRS", "definition": "Software Requirements Specification"},
                {"term": "HITL", "definition": "Human-in-the-Loop"}
            ],
            "intended_audience": "System designers, QA engineers, and developers.",
            "project_scope": "Testing the automated document generation features."
        },
        "overall_description": {
            "product_perspective": "A standalone system that converts wireframes to standard SRS documents.",
            "product_functions": [
                "Parse hand-drawn wireframes using YOLO.",
                "Review UI elements with Human-in-the-Loop.",
                "Draft SRS chapters using RAG.",
                "Export complete IEEE-standard documents."
            ],
            "user_classes": [
                {"name": "Business Analyst", "characteristics": "Reviews and refines specifications."}
            ],
            "operating_environment": "Cross-platform cloud execution via Streamlit Cloud.",
            "design_constraints": [
                "Strict adherence to IEEE templates.",
                "Responsive UI layout."
            ],
            "assumptions_dependencies": [
                "External AI APIs are accessible.",
                "Supabase is configured."
            ]
        },
        "functional_requirements": [
            {
                "id": "FR-001",
                "name": "Upload Wireframe",
                "actor": "Business Analyst",
                "description": "The system shall allow users to upload wireframe mockup files.",
                "priority": "High",
                "pre_conditions": ["User is on the main workspace page."],
                "main_flow": [
                    "User clicks upload button.",
                    "System validates image format.",
                    "System stores image bytes in session state."
                ],
                "post_conditions": ["Image is visible in the review preview."],
                "alternative_flows": [
                    {
                        "condition": "Invalid file format",
                        "steps": [
                            "System shows warning notification.",
                            "System requests another file."
                        ]
                    }
                ]
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-001",
                "type": "Performance",
                "metric": "Response time",
                "description": "Visual component extraction must execute within 3 seconds."
            }
        ],
        "business_rules": [
            {
                "id": "BR-001",
                "name": "Upload Limit",
                "description": "Files must not exceed 10 megabytes in size."
            }
        ]
    }
    
    # Mock Diagram Data
    diagram_data = {
        "flowchart_diagram": "```mermaid\ngraph TD\nA[Start] --> B(Upload) --> C[Review] --> D[Done]\n```",
        "sequence_diagram": "```mermaid\nsequenceDiagram\nUser->>System: Upload mockup\nSystem->>YOLO: Extract elements\nYOLO-->>System: Bounding boxes\n```",
        "diagram_explanation": "These diagrams represent the data flows during wireframe parsing and verification."
    }
    
    # Mock Vision Data
    vision_data = {
        "page_name": "Checkout Detail Page Mockup",
        "elements": [
            {
                "id": "btn_checkout",
                "type": "button",
                "label": "Proceed to Checkout",
                "description": "Primary action button located at the bottom right corner."
            },
            {
                "id": "input_email",
                "type": "text_input",
                "label": "Email Address",
                "description": "Standard email input field positioned at the top section."
            },
            {
                "id": "dropdown_shipping",
                "type": "dropdown",
                "label": "Select Shipping Method",
                "description": "List of shipping options available based on user address."
            }
        ],
        "detected_user_flows": [
            "User enters email address in standard text input.",
            "User selects preferred shipping method from the shipping dropdown options.",
            "User clicks 'Proceed to Checkout' to complete the transaction."
        ]
    }
    
    # Read image bytes
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
        
    ba_j = json.dumps(ba_data)
    diag_j = json.dumps(diagram_data)
    vision_j = json.dumps(vision_data)
    
    try:
        # Run generator
        generate_srs_docx(
            ba_data_json=ba_j,
            template_path=template_path,
            output_path=docx_path,
            diagram_data_json=diag_j,
            vision_data_json=vision_j,
            image_bytes=img_bytes
        )
        print("Success: Generated docx file at", docx_path)
        
        # Run PDF converter
        pdf_ok = convert_docx_to_pdf(docx_path, pdf_path)
        if pdf_ok:
            print("Success: Converted docx to PDF at", pdf_path)
        else:
            print("Notice: PDF conversion skipped or failed (MS Word not installed locally, which is normal for CLI testing).")
            
    except Exception as e:
        print("Error during document generation:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()
