import streamlit as st
import os
import sys
import tempfile
import time
import pandas as pd
import json
import base64
import streamlit.components.v1 as components

def render_mermaid(code: str):
    cleaned_code = code.replace('"', '\\"') if '"' in code else code
    html_string = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Outfit', sans-serif; background-color: transparent; }}
        </style>
        <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
    </head>
    <body>
        <pre class="mermaid" style="display: flex; justify-content: center;">
{code}
        </pre>
    </body>
    </html>
    '''
    components.html(html_string, height=500, scrolling=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.vision_agent import VisionAgent
from src.agents.ba_agent import BAAgent
from src.agents.diagram_agent import DiagramAgent
from src.agents.data_agent import DataArchitectAgent
from src.agents.qa_agent import QAAgent
from src.rag_engine.chunker import extract_text_from_pdf, sliding_window_chunking
from src.rag_engine.vector_store import RAGVectorStore
from src.core.i18n import t, init_language_selector
from src.core.database import DatabaseManager

class MockSchema:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)
    def model_dump_json(self, indent=None):
        return json.dumps(self.__dict__, indent=indent)

def dict_to_obj(d):
    return MockSchema(d) if isinstance(d, dict) else d

def login_ui():
    st.markdown("<h1 class='hero-title'>Specify.ai</h1>", unsafe_allow_html=True)
    st.markdown("<h4 class='hero-subtitle'>Please authenticate to access your workspace.</h4>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1.5, 3, 1.5])
    with col:
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])
            
            with tab_login:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Log In", type="primary", use_container_width=True):
                    with st.spinner("Authenticating..."):
                        try:
                            resp = st.session_state.db.login(email, password)
                            st.session_state.user = resp.user
                            st.rerun()
                        except Exception as e:
                            st.error(f"Authentication failed: {e}")
                            
            with tab_signup:
                s_email = st.text_input("Email", key="signup_email")
                s_password = st.text_input("Password", type="password", key="signup_pass")
                if st.button("Sign Up", type="primary", use_container_width=True):
                    with st.spinner("Creating account..."):
                        try:
                            st.session_state.db.signup(s_email, s_password)
                            st.success("Account created successfully. You can now Log In.")
                        except Exception as e:
                            st.error(f"Signup failed: {e}")

def main():
    st.set_page_config(page_title="Specify.ai - Requirements Automation", layout="wide")
    
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #FAFAFA;
    }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    
    .hero-title { 
        text-align: center; 
        color: #111827;
        font-size: 2.8rem; 
        font-weight: 700; 
        margin-bottom: 0px; 
        padding-top: 1rem; 
        letter-spacing: -0.05em;
    }
    .hero-subtitle { 
        text-align: center; 
        color: #6B7280; 
        font-size: 1.1rem; 
        font-weight: 400;
        margin-bottom: 1.5rem; 
    }
    
    /* Clean container cards */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { 
        background: #FFFFFF; 
        border: 1px solid #E5E7EB; 
        border-radius: 8px; 
        padding: 1.5rem; 
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); 
    }
    
    /* Solid CTA Button */
    .stButton > button[kind="primary"] { 
        background-color: #111827;
        color: #FFFFFF; 
        border: none; 
        font-weight: 500; 
        padding: 0.5rem 1rem; 
        border-radius: 6px; 
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover { 
        background-color: #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
    }
    
    /* Input styling */
    .stTextInput input, .stTextArea textarea {
        border-radius: 6px;
        border-color: #D1D5DB;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    if 'user' not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        login_ui()
        return

    init_language_selector()
    
    # Initialize Core Agents
    if 'vision_agent' not in st.session_state: st.session_state.vision_agent = VisionAgent()
    if 'ba_agent' not in st.session_state: st.session_state.ba_agent = BAAgent()
    if 'diagram_agent' not in st.session_state: st.session_state.diagram_agent = DiagramAgent()
    if 'data_agent' not in st.session_state: st.session_state.data_agent = DataArchitectAgent()
    if 'qa_agent' not in st.session_state: st.session_state.qa_agent = QAAgent()
    if 'vector_store' not in st.session_state: st.session_state.vector_store = RAGVectorStore()
        
    # State Management
    if 'pipeline_state' not in st.session_state: st.session_state.pipeline_state = 'IDLE'
    if 'refinement_round' not in st.session_state: st.session_state.refinement_round = 0
    if 'image_bytes' not in st.session_state: st.session_state.image_bytes = None
    if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
    if 'user_notes' not in st.session_state: st.session_state.user_notes = ""
    if 'image_name' not in st.session_state: st.session_state.image_name = ""
    if 'active_project_id' not in st.session_state: st.session_state.active_project_id = None
    
    for key in ['cache_vision', 'cache_ba', 'cache_diagram', 'cache_da', 'cache_qa']:
        if key not in st.session_state: st.session_state[key] = None

    # Sidebar History
    with st.sidebar:
        st.markdown(f"Account: `{st.session_state.user.email}`")
        if st.button("Sign Out"):
            st.session_state.db.logout()
            st.session_state.user = None
            st.rerun()
            
        st.markdown("---")
        st.markdown("### Project History")
        
        if st.button("+ New Project", type="primary", use_container_width=True):
            st.session_state.pipeline_state = 'IDLE'
            for key in ['cache_vision', 'cache_ba', 'cache_diagram', 'cache_da', 'cache_qa']:
                st.session_state[key] = None
            st.session_state.active_project_id = None
            st.rerun()
            
        try:
            projects = st.session_state.db.get_projects(st.session_state.user.id)
            for p in projects:
                btn_name = f"{p['name']} ({p['created_at'][:10]})"
                if st.button(btn_name, use_container_width=True, key=f"hist_{p['id']}"):
                    details = st.session_state.db.get_project_details(p['id'])
                    if details:
                        if details['image_base64']:
                            st.session_state.image_bytes = base64.b64decode(details['image_base64'])
                        st.session_state.image_name = details['name']
                        st.session_state.user_notes = details['user_notes']
                        
                        st.session_state.cache_vision = dict_to_obj(details.get('vision_data'))
                        st.session_state.cache_ba = dict_to_obj(details.get('ba_data'))
                        st.session_state.cache_diagram = dict_to_obj(details.get('diagram_data'))
                        st.session_state.cache_da = dict_to_obj(details.get('da_data'))
                        st.session_state.cache_qa = dict_to_obj(details.get('qa_data'))
                        
                        st.session_state.pipeline_state = 'COMPLETED'
                        st.session_state.active_project_id = p['id']
                        st.rerun()
        except Exception as e:
            st.error(f"Failed to load history: {e}")

    # Header
    st.markdown("<h1 class='hero-title'>Specify.ai</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-subtitle'>The Agentic Systems Architect</p>", unsafe_allow_html=True)
    
    # ========================================================
    # STATE 1: IDLE
    # ========================================================
    if st.session_state.pipeline_state == 'IDLE':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            # Compact 2-column layout to prevent scrolling
            col_left, col_right = st.columns(2)
            
            with col_left:
                project_name = st.text_input("Project Name (Required)", placeholder="E.g., Inventory Management System")
                uploaded_image = st.file_uploader("Upload UI Mockup/Wireframe", type=["jpg", "jpeg", "png"])
                
            with col_right:
                user_notes = st.text_area("Master Directives (Optional)", placeholder="E.g., Require Stripe integration...", height=68)
                uploaded_pdf = st.file_uploader("Business Rules Context (PDF)", type=["pdf"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            is_disabled = (uploaded_image is None) or (project_name == "")
            if st.button("START BUSINESS ANALYSIS", type="primary", use_container_width=True, disabled=is_disabled):
                st.session_state.image_bytes = uploaded_image.getvalue()
                st.session_state.image_name = project_name
                st.session_state.user_notes = user_notes
                if uploaded_pdf:
                    st.session_state.pdf_bytes = uploaded_pdf.getvalue()
                else:
                    st.session_state.pdf_bytes = None
                
                for key in ['cache_vision', 'cache_ba', 'cache_diagram', 'cache_da', 'cache_qa']:
                    st.session_state[key] = None
                st.session_state.pipeline_state = 'PROCESSING'
                st.rerun()

    # ========================================================
    # STATE 2: PROCESSING
    # ========================================================
    elif st.session_state.pipeline_state == 'PROCESSING':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            with st.status("Multi-Agent Pipeline is architecting your system...", expanded=True) as status_box:
                pipeline_error = False
                error_message = ""
                
                try:
                    # Context Initialization
                    st.write("[System] Initializing master node...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(st.session_state.image_bytes)
                        tmp_img_path = tmp.name

                    # RAG Processing if PDF exists
                    rag_context = ""
                    if st.session_state.pdf_bytes:
                        st.write("[RAG Engine] Indexing business rules from PDF...")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                            tmp_pdf.write(st.session_state.pdf_bytes)
                            tmp_pdf_path = tmp_pdf.name
                        try:
                            raw_text = extract_text_from_pdf(tmp_pdf_path)
                            chunks = sliding_window_chunking(raw_text, 300, 50)
                            st.session_state.vector_store.add_chunks(chunks)
                            st.write("[RAG Engine] Successfully loaded context.")
                        except Exception as e:
                            st.write(f"[RAG Engine] Warning: Failed to parse PDF ({e})")
                except Exception as e:
                    pipeline_error = True
                    error_message = f"System initialization failed: {e}"

                if not pipeline_error:
                    try:
                        # Vision Agent
                        if st.session_state.cache_vision is None:
                            st.write("[VisionAgent] Extracting visual components...")
                            st.session_state.cache_vision = st.session_state.vision_agent.analyze_wireframe(tmp_img_path, st.session_state.user_notes)
                        vision_j = st.session_state.cache_vision.model_dump_json() if hasattr(st.session_state.cache_vision, 'model_dump_json') else json.dumps(st.session_state.cache_vision.__dict__)

                        # RAG Search
                        if st.session_state.pdf_bytes:
                            st.write("[RAG Engine] Querying knowledge base...")
                            page_n = getattr(st.session_state.cache_vision, 'page_name', 'UI')
                            rag_results = st.session_state.vector_store.search(page_n, top_k=5)
                            rag_context = "\\n---\\n".join(rag_results)
                    except Exception as e:
                        pipeline_error = True
                        error_message = f"Vision analysis failed: {e}"

                if not pipeline_error:
                    try:
                        # BA Agent
                        if st.session_state.cache_ba is None:
                            st.write("[BAAgent] Drafting Software Requirements Specification (SRS)...")
                            st.session_state.cache_ba = st.session_state.ba_agent.generate_requirements(vision_j, rag_context)
                        ba_j = st.session_state.cache_ba.model_dump_json() if hasattr(st.session_state.cache_ba, 'model_dump_json') else json.dumps(st.session_state.cache_ba.__dict__)
                    except Exception as e:
                        pipeline_error = True
                        error_message = f"Business Analysis failed: {e}"

                if not pipeline_error:
                    try:
                        # Diagram Agent
                        if st.session_state.cache_diagram is None:
                            st.write("[DiagramAgent] Generating UML and Flowcharts...")
                            st.session_state.cache_diagram = st.session_state.diagram_agent.generate_diagrams(ba_j)
                    except Exception as e:
                        pipeline_error = True
                        error_message = f"Diagram generation failed: {e}"
                
                if not pipeline_error:
                    try:
                        # Data Agent
                        if st.session_state.cache_da is None:
                            st.write("[DataArchitectAgent] Designing database schemas...")
                            st.session_state.cache_da = st.session_state.data_agent.design_database(ba_j)
                        da_j = st.session_state.cache_da.model_dump_json() if hasattr(st.session_state.cache_da, 'model_dump_json') else json.dumps(st.session_state.cache_da.__dict__)
                    except Exception as e:
                        pipeline_error = True
                        error_message = f"Data Architecture design failed: {e}"

                if not pipeline_error:
                    try:
                        # QA Agent
                        if st.session_state.cache_qa is None:
                            st.write("[QAAgent] Auditing system logic and consistency...")
                            st.session_state.cache_qa = st.session_state.qa_agent.audit_system(vision_j, ba_j, da_j)
                        
                        qa_j = st.session_state.cache_qa.model_dump_json() if hasattr(st.session_state.cache_qa, 'model_dump_json') else json.dumps(st.session_state.cache_qa.__dict__)
                    except Exception as e:
                        pipeline_error = True
                        error_message = f"QA Audit failed: {e}"

                if not pipeline_error:
                    # Save to Database
                    if st.session_state.active_project_id is None:
                        try:
                            st.write("[DBAgent] Persisting artifacts to cloud storage...")
                            diag_j = st.session_state.cache_diagram.model_dump_json() if hasattr(st.session_state.cache_diagram, 'model_dump_json') else json.dumps(st.session_state.cache_diagram.__dict__)
                            
                            resp = st.session_state.db.save_project(
                                st.session_state.user.id, st.session_state.image_name, 
                                st.session_state.image_bytes, vision_j, ba_j, diag_j, da_j, qa_j
                            )
                            if getattr(resp, 'data', None) and len(resp.data) > 0:
                                st.session_state.active_project_id = resp.data[0]['id']
                                st.write("[DBAgent] Record saved successfully.")
                        except Exception as db_e:
                            st.error(f"Database error: {db_e}")
                            # Does not fail the pipeline if db fails

                if pipeline_error:
                    status_box.update(label=f"Pipeline halted: {error_message}", state="error", expanded=True)
                else:
                    status_box.update(label="Analysis Completed", state="complete", expanded=False)
            
            if pipeline_error:
                st.error("The pipeline encountered an error. Existing progress has been cached.")
                if st.button("🔄 Retry Failed Step", type="primary", use_container_width=True):
                    st.rerun()
            else:
                time.sleep(1)
                st.session_state.pipeline_state = 'COMPLETED'
                st.rerun()

    # ========================================================
    # STATE 3: COMPLETED
    # ========================================================
    elif st.session_state.pipeline_state == 'COMPLETED':
        st.markdown(f"**Active Workspace:** {st.session_state.image_name}")
        
        tab_vision, tab_srs, tab_diag, tab_db = st.tabs(["Vision Analysis", "SRS Document", "Diagrams & Flow", "Data Architecture"])
        
        with tab_vision:
            with st.container(border=True):
                if st.session_state.image_bytes:
                    st.image(st.session_state.image_bytes, caption="Source Mockup", use_container_width=True)
                el_data = getattr(st.session_state.cache_vision, 'elements', [])
                if el_data:
                    df = pd.DataFrame([e.model_dump() if hasattr(e, 'model_dump') else e for e in el_data])
                    st.dataframe(df, use_container_width=True)
                
        with tab_srs:
            ba = st.session_state.cache_ba
            st.markdown(f"### {getattr(ba, 'system_name', 'System Specification')}")
            st.markdown(f"**Version:** {getattr(ba, 'version', '1.0')}")
            
            intro = getattr(ba, 'introduction', None)
            if intro:
                intro_dict = intro if isinstance(intro, dict) else (intro.model_dump() if hasattr(intro, 'model_dump') else intro.__dict__)
                st.markdown("#### 1. Introduction")
                st.markdown(f"**Purpose:** {intro_dict.get('purpose')}")
                st.markdown(f"**Scope:** {intro_dict.get('project_scope')}")
            
            overall = getattr(ba, 'overall_description', None)
            if overall:
                overall_dict = overall if isinstance(overall, dict) else (overall.model_dump() if hasattr(overall, 'model_dump') else overall.__dict__)
                st.markdown("#### 2. Overall Description")
                st.markdown(f"**Perspective:** {overall_dict.get('product_perspective')}")
                st.markdown(f"**Environment:** {overall_dict.get('operating_environment')}")
            
            st.markdown("#### 3. Functional Requirements")
            reqs = getattr(ba, 'functional_requirements', [])
            for fr_obj in reqs:
                fr = fr_obj if isinstance(fr_obj, dict) else (fr_obj.model_dump() if hasattr(fr_obj, 'model_dump') else fr_obj.__dict__)
                with st.expander(f"[{fr.get('id')}] {fr.get('name')} (Priority: {fr.get('priority')})"):
                    st.write(f"**Actor:** {fr.get('actor')}")
                    st.write(f"**Description:** {fr.get('description')}")
                    st.write(f"**Main Flow:** {', '.join(fr.get('main_flow', []))}")
                    
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Regenerate SRS", key="regen_srs", help="Clear downstream results and run Business Analysis again"):
                st.session_state.cache_ba = None
                st.session_state.cache_diagram = None
                st.session_state.cache_da = None
                st.session_state.cache_qa = None
                st.session_state.pipeline_state = 'PROCESSING'
                st.rerun()

        with tab_diag:
            diag = st.session_state.cache_diagram
            flow_code = getattr(diag, 'flowchart_diagram', '')
            seq_code = getattr(diag, 'sequence_diagram', '')
            with st.container(border=True):
                st.markdown("#### Operational Flowchart")
                render_mermaid(flow_code)
                with st.expander("[Debug] View raw Mermaid code"):
                    st.code(flow_code, language='text')
            with st.container(border=True):
                st.markdown("#### System Sequence Diagram")
                render_mermaid(seq_code)
                with st.expander("[Debug] View raw Mermaid code"):
                    st.code(seq_code, language='text')

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Regenerate Diagrams", key="regen_diagram"):
                st.session_state.cache_diagram = None
                st.session_state.cache_qa = None
                st.session_state.pipeline_state = 'PROCESSING'
                st.rerun()

        with tab_db:
            da = st.session_state.cache_da
            erd_code = getattr(da, 'erd_mermaid', '')
            render_mermaid(erd_code)
            with st.expander("[Debug] View raw ERD Mermaid code"):
                st.code(erd_code, language='text')

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Regenerate Data Architecture", key="regen_da"):
                st.session_state.cache_da = None
                st.session_state.cache_qa = None
                st.session_state.pipeline_state = 'PROCESSING'
                st.rerun()

        # HITL & Export
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Quality Assurance & Export")
        
        qa_approved = getattr(st.session_state.cache_qa, 'is_approved', True)
        if qa_approved:
            st.success("System architecture verified. No critical logic conflicts detected.")
            if st.button("Export Specifications (PDF)", type="primary"):
                from src.core.pdf_exporter import generate_srs_pdf
                ba_j = st.session_state.cache_ba.model_dump_json() if hasattr(st.session_state.cache_ba, 'model_dump_json') else json.dumps(st.session_state.cache_ba.__dict__)
                try:
                    filepath = os.path.join(tempfile.gettempdir(), f"SRS_{st.session_state.image_name}.pdf")
                    generate_srs_pdf(ba_j, filepath)
                    with open(filepath, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF Document",
                            data=pdf_file,
                            file_name=f"Specification_{st.session_state.image_name}.pdf",
                            mime="application/octet-stream",
                            type="primary"
                        )
                except Exception as e:
                    st.error(f"Failed to generate PDF: {e}")
        else:
            st.error("Logic conflicts detected. Manual review recommended.")

if __name__ == "__main__":
    main()
