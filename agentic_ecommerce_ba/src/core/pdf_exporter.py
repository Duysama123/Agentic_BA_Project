from fpdf import FPDF
import json


class SRSPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Software Requirements Specification (SRS)', border=False, ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def _safe(text) -> str:
    """Strip non-latin1 characters so Helvetica won't crash."""
    if text is None:
        return ""
    s = str(text)
    # encode to latin-1 (what Helvetica supports), replace anything it can't handle
    return s.encode('latin-1', errors='replace').decode('latin-1')


def generate_srs_pdf(ba_data_json: str, output_path: str):
    data = json.loads(ba_data_json)

    pdf = SRSPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title Page
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 20, _safe(data.get('system_name', 'System Specification')), ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 10, f"Version: {_safe(data.get('version', '1.0'))}", ln=True, align='C')
    pdf.ln(20)

    # 1. Introduction
    intro = data.get('introduction', {})
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '1. Introduction', ln=True)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '1.1 Purpose', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, _safe(intro.get('purpose', '')))

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '1.2 Project Scope', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, _safe(intro.get('project_scope', '')))
    pdf.ln(5)

    # 2. Overall Description
    overall = data.get('overall_description', {})
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '2. Overall Description', ln=True)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '2.1 Product Perspective', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, _safe(overall.get('product_perspective', '')))

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '2.2 Operating Environment', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, _safe(overall.get('operating_environment', '')))
    pdf.ln(5)

    # 3. Functional Requirements
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '3. Functional Requirements', ln=True)
    reqs = data.get('functional_requirements', [])
    for fr in reqs:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, _safe(f"[{fr.get('id')}] {fr.get('name')}"), ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.multi_cell(0, 8, _safe(f"Actor: {fr.get('actor')}"))
        pdf.multi_cell(0, 8, _safe(f"Description: {fr.get('description')}"))

        main_flow = fr.get('main_flow', [])
        if main_flow:
            pdf.multi_cell(0, 8, "Main Flow:")
            for step in main_flow:
                pdf.multi_cell(0, 8, _safe(f"  - {step}"))
        pdf.ln(5)

    # 4. Non Functional Requirements
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '4. Non-Functional Requirements', ln=True)
    nfrs = data.get('non_functional_requirements', [])
    for nfr in nfrs:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, _safe(f"[{nfr.get('id')}] {nfr.get('type')}"), ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.multi_cell(0, 8, _safe(nfr.get('description', '')))
        pdf.ln(2)

    pdf.output(output_path)
