import os
import json
from docxtpl import DocxTemplate

def generate_srs_docx(ba_data_json: str, template_path: str, output_path: str, diagram_data_json: str = None, testcase_data_json: str = None) -> str:
    """
    Load data from BA Agent into the IEEE DOCX template.
    If diagram_data_json or testcase_data_json is provided, appends to the DOCX.
    Returns the path to the generated DOCX.
    """
    data = json.loads(ba_data_json)
    
    from datetime import datetime
    if 'date_created' not in data:
        data['date_created'] = datetime.now().strftime("%B %d, %Y")
    if 'author' not in data:
        data['author'] = "Agentic BA System"
    if 'organization' not in data:
        data['organization'] = "E-Commerce Project Team"
    
    # Initialize the template
    doc = DocxTemplate(template_path)
    
    # Check if the user has added diagram variables to the template
    template_vars = doc.get_undeclared_template_variables()
    
    append_at_end = True
    temp_files = []
    
    if diagram_data_json:
        diag_data = json.loads(diagram_data_json)
        data['diagram_explanation'] = diag_data.get("diagram_explanation", "")
        
        if 'flowchart_image' in template_vars or 'sequence_image' in template_vars:
            append_at_end = False
            import requests
            import zlib
            import base64
            import tempfile
            from docxtpl import InlineImage
            from docx.shared import Inches
            
            def get_kroki_url(mermaid_text: str) -> str:
                mermaid_text = mermaid_text.strip()
                if mermaid_text.startswith("```mermaid"): mermaid_text = mermaid_text[10:]
                elif mermaid_text.startswith("```"): mermaid_text = mermaid_text[3:]
                if mermaid_text.endswith("```"): mermaid_text = mermaid_text[:-3]
                mermaid_text = mermaid_text.strip()
                compressed = zlib.compress(mermaid_text.encode('utf-8'), 9)
                encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
                return f"https://kroki.io/mermaid/png/{encoded}"

            fc_code = diag_data.get("flowchart_diagram", "")
            if fc_code and 'flowchart_image' in template_vars:
                try:
                    r = requests.get(get_kroki_url(fc_code), timeout=15)
                    if r.status_code == 200:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        tmp.write(r.content)
                        tmp.close()
                        temp_files.append(tmp.name)
                        data['flowchart_image'] = InlineImage(doc, tmp.name, width=Inches(6.0))
                except Exception as e:
                    print("Failed to fetch flowchart image:", e)

            seq_code = diag_data.get("sequence_diagram", "")
            if seq_code and 'sequence_image' in template_vars:
                try:
                    r = requests.get(get_kroki_url(seq_code), timeout=15)
                    if r.status_code == 200:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        tmp.write(r.content)
                        tmp.close()
                        temp_files.append(tmp.name)
                        data['sequence_image'] = InlineImage(doc, tmp.name, width=Inches(6.0))
                except Exception as e:
                    print("Failed to fetch sequence image:", e)

    print("DEBUG - data keys:", data.keys())
    
    # Render the document with the context
    doc.render(data)
    
    # Save the output
    doc.save(output_path)
    
    for tmp_file in temp_files:
        try:
            os.unlink(tmp_file)
        except:
            pass
            
    # Append extras if available and not included in template
    if (diagram_data_json or testcase_data_json) and append_at_end:
        append_extras_to_docx(output_path, diagram_data_json, testcase_data_json)
        
    return output_path

def append_extras_to_docx(docx_path: str, diagram_data_json: str = None, testcase_data_json: str = None):
    import base64
    import zlib
    import requests
    import tempfile
    from docx import Document
    from docx.shared import Inches

    try:
        doc = Document(docx_path)
        
        if diagram_data_json:
            diag_data = json.loads(diagram_data_json)
            doc.add_page_break()
            doc.add_heading('System Diagrams (Auto-Generated)', level=1)

            def get_kroki_url(mermaid_text: str) -> str:
                if mermaid_text.startswith("```mermaid"):
                    mermaid_text = mermaid_text[10:]
                if mermaid_text.endswith("```"):
                    mermaid_text = mermaid_text[:-3]
                mermaid_text = mermaid_text.strip()
                compressed = zlib.compress(mermaid_text.encode('utf-8'), 9)
                encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
                return f"https://kroki.io/mermaid/png/{encoded}"

            # Fetch and add Flowchart
            fc_code = diag_data.get("flowchart_diagram", "")
            if fc_code:
                try:
                    r = requests.get(get_kroki_url(fc_code), timeout=15)
                    if r.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(r.content)
                            tmp_path = tmp.name
                        doc.add_heading('Flowchart Diagram', level=2)
                        doc.add_picture(tmp_path, width=Inches(6.0))
                        os.unlink(tmp_path)
                except Exception as e:
                    print("Failed to add flowchart image:", e)

            # Fetch and add Sequence
            seq_code = diag_data.get("sequence_diagram", "")
            if seq_code:
                try:
                    r = requests.get(get_kroki_url(seq_code), timeout=15)
                    if r.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(r.content)
                            tmp_path = tmp.name
                        doc.add_heading('Sequence Diagram', level=2)
                        doc.add_picture(tmp_path, width=Inches(6.0))
                        os.unlink(tmp_path)
                except Exception as e:
                    print("Failed to add sequence image:", e)

            explanation = diag_data.get("diagram_explanation", "")
            if explanation:
                doc.add_heading('Diagram Explanation', level=2)
                doc.add_paragraph(explanation)

        if testcase_data_json:
            tc_data = json.loads(testcase_data_json)
            test_cases = tc_data.get("test_cases", [])
            if test_cases:
                doc.add_page_break()
                doc.add_heading('System Test Cases (Auto-Generated)', level=1)
                for tc in test_cases:
                    tc_id = tc.get("test_id", "TC")
                    tc_scen = tc.get("scenario", "Scenario")
                    doc.add_heading(f"[{tc.get('priority', 'Medium')} Priority] {tc_id} - {tc_scen}", level=2)
                    doc.add_paragraph(f"Test Type: {tc.get('test_type', 'Functional')}")
                    doc.add_paragraph(f"Precondition: {tc.get('precondition', 'None')}")
                    
                    steps = tc.get("steps", [])
                    if steps:
                        doc.add_paragraph("Steps:")
                        for s in steps:
                            doc.add_paragraph(f"  {s.get('step_number', '')}. {s.get('action', '')} -> {s.get('expected_result', '')}")
                            
                    doc.add_paragraph(f"Final Expected Result: {tc.get('final_expected_result', 'None')}")
                    
                    auto_hint = tc.get("automation_hint", "")
                    if auto_hint:
                        doc.add_paragraph(f"Automation Hint: {auto_hint}")
                    
                    bdd = tc.get("bdd_gherkin", "")
                    if bdd:
                        doc.add_paragraph("BDD Gherkin Format:")
                        doc.add_paragraph(bdd)

        doc.save(docx_path)
    except Exception as e:
        print("Failed to append extras:", e)

def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Convert DOCX to PDF.
    Tries LibreOffice first (for Linux/Streamlit Cloud).
    Falls back to docx2pdf (for Windows/Mac with MS Word installed).
    """
    import platform
    import subprocess
    import os

    # 1. Try LibreOffice on Linux (Streamlit Cloud)
    if platform.system() == 'Linux':
        try:
            outdir = os.path.dirname(pdf_path)
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", docx_path, "--outdir", outdir],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            # libreoffice saves the file as same name but .pdf
            expected_pdf = os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
            if expected_pdf != pdf_path and os.path.exists(expected_pdf):
                os.rename(expected_pdf, pdf_path)
            return True
        except Exception as e:
            print(f"LibreOffice conversion failed: {e}")

    # 2. Try docx2pdf for local Windows/Mac users
    try:
        from docx2pdf import convert
        import pythoncom
        
        # docx2pdf uses COM on Windows; if called from a background thread (like Streamlit sometimes does),
        # COM needs to be initialized.
        pythoncom.CoInitialize()
        
        convert(docx_path, pdf_path)
        return True
    except Exception as e:
        print(f"Error converting to PDF (MS Word might not be installed or accessible): {e}")
        return False
