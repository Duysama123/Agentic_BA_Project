import time as _time
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
    """Render Mermaid diagram using Mermaid JS in HTML component."""
    if not code or not code.strip():
        st.warning("No diagram code available.")
        return
    
    clean = code.strip()
    if clean.startswith("```mermaid"):
        clean = clean[10:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()
    
    import base64
    code_b64 = base64.b64encode(clean.encode('utf-8')).decode('utf-8')
    
    html = f"""
    <div id="mermaid-render" class="mermaid"></div>
    <div id="error-container" style="color: #dc2626; background-color: #fee2e2; padding: 12px; border: 1px solid #fecaca; border-radius: 4px; font-family: monospace; white-space: pre-wrap; display: none;"></div>
    
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        
        const errorContainer = document.getElementById('error-container');
        const renderContainer = document.getElementById('mermaid-render');
        
        try {{
            const binString = atob("{code_b64}");
            const uint8Array = Uint8Array.from(binString, (m) => m.codePointAt(0));
            const cleanCode = new TextDecoder().decode(uint8Array);
            
            renderContainer.textContent = cleanCode;
            
            mermaid.initialize({{ 
                startOnLoad: false, 
                theme: 'default',
                securityLevel: 'loose',
                suppressErrorAlerts: true
            }});
            
            await mermaid.run({{
                nodes: [renderContainer]
            }});
        }} catch (err) {{
            console.error("Mermaid Render Error:", err);
            errorContainer.style.display = 'block';
            errorContainer.textContent = 'Mermaid Rendering Error: ' + err.message;
            renderContainer.style.display = 'none';
        }}
    </script>
    """
    components.html(html, height=700, scrolling=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.vision_agent import VisionAgent
from src.agents.ba_agent import BAAgent
from src.agents.diagram_agent import DiagramAgent
from src.agents.qa_agent import QAAgent
from src.agents.testcase_agent import TestCaseAgent
from src.rag_engine.chunker import extract_text_from_pdf, sliding_window_chunking
from src.rag_engine.vector_store import RAGVectorStore
from src.core.i18n import t, init_language_selector
from src.core.database import DatabaseManager
from src.core.config import Config

class MockSchema:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, dict_to_obj(v))
    def model_dump_json(self, indent=None):
        import json
        return json.dumps(self, default=lambda o: getattr(o, '__dict__', str(o)), separators=(',', ':'))
    def model_dump(self):
        import json
        return json.loads(self.model_dump_json())

def dict_to_obj(d):
    if isinstance(d, dict):
        return MockSchema(d)
    elif isinstance(d, list):
        return [dict_to_obj(i) for i in d]
    return d

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
    st.set_page_config(page_title="Specify.ai - Requirements Automation", layout="wide", initial_sidebar_state="expanded")
    
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #FAFAFA;
    }
    
    footer {visibility: hidden;}
    
    /* === Modern Sidebar (CodingLab style) === */
    [data-testid="stSidebar"] {
        background-color: #111827 !important; /* Deep dark blue */
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #E5E7EB !important;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFFFFF !important;
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    [data-testid="stSidebar"] hr {
        border-color: #374151;
        margin: 1.5rem 0;
    }
    
    /* Style Selectbox to fit dark theme and not look blurry/white */
    [data-testid="stSelectbox"] > div[data-baseweb="select"] > div {
        background-color: #1F2937 !important;
        border: 1px solid #374151 !important;
        color: #FFFFFF !important;
    }
    
    /* Menu Item Buttons (Secondary) */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #9CA3AF !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
        display: flex !important;
        justify-content: flex-start !important;
        padding: 0.6rem 1rem !important;
        margin-bottom: 0.2rem !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
    }
    
    /* Active State Trick for Secondary buttons */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:focus {
        background-color: #3730A3 !important;
        color: #FFFFFF !important;
    }
    
    /* Restore Red Sign Out Button (placed after to override generic secondary) */
    [data-testid="stSidebar"] .stButton:last-of-type > button[kind="secondary"],
    [data-testid="stSidebar"] div:last-child > .stButton > button[kind="secondary"] {
        background-color: #dc2626 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] .stButton:last-of-type > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] div:last-child > .stButton > button[kind="secondary"]:hover {
        background-color: #b91c1c !important;
    }
    
    /* Primary Button (New Project) */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #4F46E5 !important; /* Indigo blue */
        border: none !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        padding: 0.7rem 1rem !important;
        margin-bottom: 1rem !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #4338CA !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
    }
    
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
    
    /* === Pipeline Progress Cards === */
    .pipeline-card {
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }
    .pipeline-card-completed {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border: 1px solid #86efac;
    }
    .pipeline-card-active {
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        border: 1px solid #93c5fd;
        animation: pulse-border 2s ease-in-out infinite;
    }
    .pipeline-card-pending {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        opacity: 0.7;
    }
    .pipeline-card-error {
        background: linear-gradient(135deg, #fef2f2, #fee2e2);
        border: 1px solid #fca5a5;
    }
    @keyframes pulse-border {
        0%, 100% { border-color: #93c5fd; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        50% { border-color: #3b82f6; box-shadow: 0 0 8px 2px rgba(59, 130, 246, 0.15); }
    }
    .pipeline-icon {
        width: 36px; height: 36px; border-radius: 50%; display: flex;
        align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
    }
    .pipeline-icon-completed { background: #dcfce7; color: #16a34a; }
    .pipeline-icon-active { background: #dbeafe; color: #2563eb; }
    .pipeline-icon-pending { background: #f3f4f6; color: #9ca3af; }
    .pipeline-title { font-weight: 600; font-size: 15px; color: #111827; }
    .pipeline-subtitle { font-size: 13px; color: #6b7280; margin-top: 2px; }
    .pipeline-time { font-size: 14px; font-weight: 600; color: #6b7280; white-space: nowrap; }
    .badge-parallel {
        background: #fef3c7; color: #d97706; font-size: 11px; font-weight: 700;
        padding: 2px 8px; border-radius: 4px; margin-left: 8px; display: inline-block;
    }
    .pipeline-overall {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
        padding: 16px 20px; margin-bottom: 16px;
    }
    .pipeline-overall-title { font-weight: 600; font-size: 14px; color: #111827; }
    .pipeline-progress-bar {
        width: 100%; height: 6px; background: #e5e7eb; border-radius: 3px;
        margin: 8px 0 4px 0; overflow: hidden;
    }
    .pipeline-progress-fill {
        height: 100%; border-radius: 3px;
        background: linear-gradient(90deg, #22c55e, #3b82f6);
        transition: width 0.5s ease;
    }
    .pipeline-progress-label { font-size: 12px; color: #9ca3af; }
    .hitl-notice {
        background: linear-gradient(135deg, #fffbeb, #fef3c7);
        border: 1px solid #fde68a;
        border-radius: 10px; padding: 14px 18px; margin-top: 12px;
    }
    .hitl-notice-icon { font-size: 16px; margin-right: 8px; }
    .hitl-notice-text { font-size: 13px; color: #92400e; font-weight: 500; }
    .hitl-notice-sub { font-size: 12px; color: #a16207; margin-top: 4px; }
    .live-stream-box {
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 14px; margin-top: 10px; font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 12px; color: #334155; max-height: 200px; overflow-y: auto;
        line-height: 1.6;
    }
    .live-stream-label {
        font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;
        display: flex; align-items: center; gap: 6px;
    }
    .live-dot { width: 6px; height: 6px; border-radius: 50%; background: #3b82f6; animation: blink 1s infinite; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    .elapsed-timer {
        font-size: 13px; color: #9ca3af; display: flex; align-items: center; gap: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'orig_gemini_api_key' not in st.session_state:
        st.session_state.orig_gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    if 'orig_gemini_api_keys' not in st.session_state:
        st.session_state.orig_gemini_api_keys = os.getenv("GEMINI_API_KEYS", "")

    if not st.session_state.user:
        login_ui()
        return

    # init_language_selector()  # Removed: English only
    
    # Initialize Core Agents
    if 'vision_agent' not in st.session_state: st.session_state.vision_agent = VisionAgent()
    if 'ba_agent' not in st.session_state: st.session_state.ba_agent = BAAgent()
    if 'diagram_agent' not in st.session_state: st.session_state.diagram_agent = DiagramAgent()
    if 'qa_agent' not in st.session_state: st.session_state.qa_agent = QAAgent()
    if 'testcase_agent' not in st.session_state: st.session_state.testcase_agent = TestCaseAgent()
    if 'vector_store' not in st.session_state: st.session_state.vector_store = RAGVectorStore()
        
    # State Management
    if 'pipeline_state' not in st.session_state: st.session_state.pipeline_state = 'IDLE'
    if 'refinement_round' not in st.session_state: st.session_state.refinement_round = 0
    if 'qa_retry_count' not in st.session_state: st.session_state.qa_retry_count = 0
    if 'qa_reviewer_notes' not in st.session_state: st.session_state.qa_reviewer_notes = ""
    if 'image_bytes' not in st.session_state: st.session_state.image_bytes = None
    if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None
    if 'user_notes' not in st.session_state: st.session_state.user_notes = ""
    if 'image_name' not in st.session_state: st.session_state.image_name = ""
    if 'active_project_id' not in st.session_state: st.session_state.active_project_id = None
    if 'rag_context' not in st.session_state: st.session_state.rag_context = ""
    
    for key in ['cache_vision', 'cache_ba', 'cache_diagram', 'cache_qa', 'cache_testcase']:
        if key not in st.session_state: st.session_state[key] = None
    
    # Pipeline timing tracker
    if 'step_timings' not in st.session_state:
        st.session_state.step_timings = {}  # e.g. {'vision': 1.8, 'hitl1': 47, 'ba': 134, ...}
    if 'pipeline_start_time' not in st.session_state:
        st.session_state.pipeline_start_time = None

    # Sidebar - Modern CodingLab-style with Selectbox and Avatar
    with st.sidebar:
        user_email = st.session_state.user.email
        initial = user_email[0].upper() if user_email else "U"
        
        # User Avatar Profile Header
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; margin-top: 0.5rem;">
            <div style="width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 18px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); flex-shrink: 0;">
                {initial}
            </div>
            <div style="overflow: hidden;">
                <div style="font-weight: 700; font-size: 1.1rem; color: #F3F4F6; letter-spacing: 0.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Specify.ai</div>
                <div style="font-size: 0.8rem; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{user_email}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("+ New Project", type="primary", use_container_width=True):
            st.session_state.pipeline_state = 'IDLE'
            for key in ['cache_vision', 'cache_ba', 'cache_diagram', 'cache_qa', 'cache_testcase']:
                st.session_state[key] = None
            st.session_state.active_project_id = None
            st.session_state.step_timings = {}
            st.session_state.pipeline_start_time = None
            st.rerun()
        
        st.markdown("### PROJECT HISTORY")
            
        try:
            projects = st.session_state.db.get_projects(st.session_state.user.id)
            if not projects:
                st.caption("No projects yet.")
            else:
                project_options = {f"{p['name']} ({p['created_at'][:10]})": p for p in projects}
                
                selected_proj_name = st.selectbox(
                    "Select a project", 
                    options=["-- Select a past project --"] + list(project_options.keys()),
                    label_visibility="collapsed"
                )
                
                if selected_proj_name != "-- Select a past project --":
                    if st.button("Load Project", use_container_width=True):
                        p = project_options[selected_proj_name]
                        details = st.session_state.db.get_project_details(p['id'])
                        if details:
                            if details['image_base64']:
                                st.session_state.image_bytes = base64.b64decode(details['image_base64'])
                            st.session_state.image_name = details['name']
                            st.session_state.user_notes = details['user_notes']
                            
                            st.session_state.cache_vision = dict_to_obj(details.get('vision_data'))
                            st.session_state.cache_ba = dict_to_obj(details.get('ba_data'))
                            st.session_state.cache_diagram = dict_to_obj(details.get('diagram_data'))
                            qa_raw = details.get('qa_data', {})
                            if qa_raw and isinstance(qa_raw, dict) and '_step_timings' in qa_raw:
                                st.session_state.step_timings = qa_raw.pop('_step_timings')
                            else:
                                st.session_state.step_timings = {}
                            st.session_state.cache_qa = dict_to_obj(qa_raw)
                            st.session_state.cache_testcase = dict_to_obj(details.get('testcase_data', details.get('da_data')))
                            
                            st.session_state.pipeline_state = 'COMPLETED'
                            st.session_state.active_project_id = p['id']
                            st.rerun()
        except Exception as e:
            st.error(f"Failed to load history: {e}")
        
        st.markdown("---")
        
        with st.expander("API Key Configuration"):
            custom_key = st.text_input(
                "Gemini API Key (Optional)", 
                type="password", 
                help="Enter your personal Gemini API Key from Google AI Studio to avoid shared quota rate limits."
            )
            if custom_key:
                os.environ["GEMINI_API_KEY"] = custom_key.strip()
                if "GEMINI_API_KEYS" in os.environ:
                    del os.environ["GEMINI_API_KEYS"]
                st.caption("Using your custom API key.")
            else:
                os.environ["GEMINI_API_KEY"] = st.session_state.orig_gemini_api_key
                if st.session_state.orig_gemini_api_keys:
                    os.environ["GEMINI_API_KEYS"] = st.session_state.orig_gemini_api_keys
                elif "GEMINI_API_KEYS" in os.environ:
                    del os.environ["GEMINI_API_KEYS"]
                if os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEYS"):
                    st.caption("Using shared default keys.")
                else:
                    st.caption("No API key set!")

        # Logout button
        if st.button("Sign Out", use_container_width=True):
            st.session_state.db.logout()
            st.session_state.user = None
            st.rerun()

    # Header
    st.markdown("<h1 class='hero-title'>Specify.ai</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-subtitle'>The Agentic Systems Architect</p>", unsafe_allow_html=True)
    
    # Evaluation Survey Banner
    st.info("💡 **Help us evaluate this system!** If you are testing our app, please help by filling out this [2-minute Feedback Survey](https://forms.gle/35YmQcNYv9Jum54UA) after reviewing the output. Thank you!")

    
    # -------------------------------------------------------
    # Pipeline Progress Renderer
    # -------------------------------------------------------
    def _fmt_time(seconds):
        """Format seconds into human-readable string."""
        if seconds is None: return "—"
        if seconds < 60: return f"{seconds:.1f}s"
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s:02d}s"
    
    def _card(icon, icon_cls, card_cls, title, subtitle, time_str, extra_badge=""):
        return (
            f'<div class="pipeline-card {card_cls}">'
            f'  <div style="display:flex;align-items:center;gap:14px;">'
            f'    <div class="pipeline-icon {icon_cls}">{icon}</div>'
            f'    <div>'
            f'      <div class="pipeline-title">{title}{extra_badge}</div>'
            f'      <div class="pipeline-subtitle">{subtitle}</div>'
            f'    </div>'
            f'  </div>'
            f'  <div class="pipeline-time">{time_str}</div>'
            f'</div>'
        )
    
    PIPELINE_STEPS = [
        ("vision", "Vision Agent", "PROCESSING_VISION"),
        ("hitl1", "HITL-1 — Vision Review", "HITL_VISION"),
        ("ba", "BA Agent", "PROCESSING_BA"),
        ("hitl2", "HITL-2 — SRS Review", "HITL_BA"),
        ("diagrams", "Diagram · QA · Test Case Agents", "PROCESSING_DIAGRAMS"),
    ]
    TOTAL_STEPS = len(PIPELINE_STEPS)
    
    # Map pipeline_state to a step index for progress calculation
    STATE_ORDER = {
        'IDLE': -1, 'PROCESSING_VISION': 0, 'HITL_VISION': 1,
        'PROCESSING_BA': 2, 'HITL_BA': 3, 'PROCESSING_DIAGRAMS': 4,
        'HITL_QA': 5, 'COMPLETED': 6
    }
    
    def render_pipeline_progress(current_state, active_subtitle="Processing..."):
        """Render the progress dashboard above the active state's UI."""
        timings = st.session_state.step_timings
        current_idx = STATE_ORDER.get(current_state, -1)
        
        # Don't show progress for IDLE or COMPLETED
        if current_idx < 0:
            return
        
        # Calculate progress percentage
        completed_count = sum(1 for key, _, state in PIPELINE_STEPS if STATE_ORDER.get(state, 99) < current_idx)
        progress_pct = int((completed_count / TOTAL_STEPS) * 100)
        remaining_steps = TOTAL_STEPS - completed_count
        
        # Estimate remaining time
        done_times = [v for k, v in timings.items() if isinstance(v, (int, float)) and not k.endswith('_start')]
        avg_time = sum(done_times) / len(done_times) if done_times else 30
        est_remaining = int(remaining_steps * avg_time)
        est_str = f"Est. {est_remaining // 60}m {est_remaining % 60}s remaining" if est_remaining > 60 else f"Est. {est_remaining}s remaining"
        
        # Overall progress bar
        project_name = st.session_state.get('image_name', 'Project')
        html = f'''
        <div class="pipeline-overall">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="pipeline-overall-title">Overall progress</div>
                <div class="pipeline-time">{progress_pct}%</div>
            </div>
            <div class="pipeline-progress-bar"><div class="pipeline-progress-fill" style="width:{progress_pct}%;"></div></div>
            <div class="pipeline-progress-label">Step {completed_count + 1} of {TOTAL_STEPS} · {est_str}</div>
        </div>
        '''
        
        # Render each step card
        for step_key, step_name, step_state in PIPELINE_STEPS:
            step_idx = STATE_ORDER.get(step_state, 99)
            t = timings.get(step_key)
            badge = ""
            
            if step_key == "diagrams":
                badge = '<span class="badge-parallel">parallel</span>'
            
            if step_idx < current_idx:
                # Completed
                sub = timings.get(f"{step_key}_subtitle", "Completed")
                html += _card("✓", "pipeline-icon-completed", "pipeline-card-completed", step_name, sub, _fmt_time(t), badge)
            elif step_idx == current_idx:
                # Active
                elapsed = ""
                if st.session_state.pipeline_start_time and step_key in ['vision', 'ba', 'diagrams']:
                    step_start = timings.get(f"{step_key}_start")
                    if step_start:
                        elapsed = _fmt_time(_time.time() - step_start)
                html += _card("⟳", "pipeline-icon-active", "pipeline-card-active", step_name, active_subtitle, elapsed or "...", badge)
            else:
                # Pending
                html += _card("○", "pipeline-icon-pending", "pipeline-card-pending", step_name, "Waiting", "—", badge)
        
        st.markdown(html, unsafe_allow_html=True)
    
    
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
            
            # Sample wireframes package for public testers
            with st.expander("💡 Don't have a wireframe or business rules PDF? Test with these samples:"):
                c1, c2 = st.columns(2)
                
                # Check if local sample files exist
                sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "sample_files"))
                wf1_path = os.path.join(sample_dir, "sample_wireframe_1.png")
                wf2_path = os.path.join(sample_dir, "sample_wireframe_2.png")
                rules_path = os.path.join(sample_dir, "sample_business_rules.txt")
                
                with c1:
                    st.markdown("**Sample Wireframes:**")
                    if os.path.exists(wf1_path):
                        with open(wf1_path, "rb") as f:
                            wf1_bytes = f.read()
                        st.download_button(
                            "📥 Download Wireframe 1 (Search)",
                            wf1_bytes,
                            file_name="sample_wireframe_1.png",
                            mime="image/png",
                            use_container_width=True,
                            key="dl_wf1"
                        )
                    if os.path.exists(wf2_path):
                        with open(wf2_path, "rb") as f:
                            wf2_bytes = f.read()
                        st.download_button(
                            "📥 Download Wireframe 2 (Product List)",
                            wf2_bytes,
                            file_name="sample_wireframe_2.png",
                            mime="image/png",
                            use_container_width=True,
                            key="dl_wf2"
                        )
                with c2:
                    st.markdown("**Sample Business Rules:**")
                    if os.path.exists(rules_path):
                        with open(rules_path, "r", encoding="utf-8") as f:
                            rules_content = f.read()
                        st.download_button(
                            "📥 Download Rules (TXT)",
                            rules_content,
                            file_name="sample_business_rules.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="dl_rules"
                        )
            
            is_disabled = (uploaded_image is None) or (project_name == "")

            if st.button("START BUSINESS ANALYSIS", type="primary", use_container_width=True, disabled=is_disabled):
                st.session_state.image_bytes = uploaded_image.getvalue()
                st.session_state.image_name = project_name
                st.session_state.user_notes = user_notes
                if uploaded_pdf:
                    st.session_state.pdf_bytes = uploaded_pdf.getvalue()
                else:
                    st.session_state.pdf_bytes = None
                
                for key in ['cache_vision', 'cache_ba', 'cache_diagram', 'cache_qa', 'cache_testcase']:
                    st.session_state[key] = None
                if 'eval_session_id' not in st.session_state or st.session_state.eval_session_id is None:
                    try:
                        sess_id = st.session_state.db.create_eval_session(st.session_state.image_name if 'image_name' in st.session_state else "Unknown")
                        st.session_state.eval_session_id = sess_id
                        st.session_state.eval_session_start_time = _time.time()
                    except Exception as e:
                        pass
                st.session_state.pipeline_state = 'PROCESSING_VISION'
                st.session_state.qa_retry_count = 0
                st.session_state.step_timings = {}
                st.session_state.pipeline_start_time = _time.time()
                st.rerun()

    # ========================================================
    # STATE 2: PROCESSING_VISION
    # ========================================================
    elif st.session_state.pipeline_state == 'PROCESSING_VISION':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            # Record step start time
            if 'vision_start' not in st.session_state.step_timings:
                st.session_state.step_timings['vision_start'] = _time.time()
            
            render_pipeline_progress('PROCESSING_VISION', "Extracting UI components from wireframe...")
            
            with st.status("Vision Agent is analyzing your mockup...", expanded=True) as status_box:
                pipeline_error = False
                error_message = ""
                try:
                    st.write("[System] Initializing master node...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(st.session_state.image_bytes)
                        tmp_img_path = tmp.name

                    if st.session_state.cache_vision is None:
                        st.write("[VisionAgent] Extracting visual components...")
                        st.session_state.cache_vision = st.session_state.vision_agent.analyze_wireframe(tmp_img_path, st.session_state.user_notes)
                        
                        # Capture timing
                        meta = getattr(st.session_state.vision_agent, 'last_run_metadata', {"time": 0, "tokens": 0})
                        st.session_state.step_timings['vision'] = meta['time']
                        
                        el_count = len(getattr(st.session_state.cache_vision, 'elements', []))
                        page_n = getattr(st.session_state.cache_vision, 'page_name', 'UI')
                        st.session_state.step_timings['vision_subtitle'] = f"Completed — {el_count} UI components extracted"
                        
                        try:
                            out_j = st.session_state.cache_vision.model_dump() if hasattr(st.session_state.cache_vision, 'model_dump') else {}
                            st.session_state.db.log_agent_run(st.session_state.get('eval_session_id'), "VisionAgent", 1, {}, out_j, meta['time'], meta['tokens'], "success")
                        except Exception: pass
                except Exception as e:
                    pipeline_error = True
                    error_message = f"Vision analysis failed: {e}"

                if pipeline_error:
                    status_box.update(label=f"Pipeline halted: {error_message}", state="error", expanded=True)
                else:
                    status_box.update(label="Vision Analysis Completed", state="complete", expanded=False)
            
            if pipeline_error:
                st.error("The pipeline encountered an error.")
                if st.button("🔄 Retry Vision Agent", type="primary", use_container_width=True):
                    st.rerun()
            else:
                time.sleep(1)
                st.session_state.pipeline_state = 'HITL_VISION'
                st.session_state.step_timings['hitl1_start'] = _time.time()
                st.rerun()

    # ========================================================
    # STATE 3: HITL_VISION (Checkpoint 1)
    # ========================================================
    elif st.session_state.pipeline_state == 'HITL_VISION':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            render_pipeline_progress('HITL_VISION', "Awaiting your review...")
            
            st.markdown("### 1. Vision Agent — Confirm UI Tree ⏳ Pending")
            st.info("The AI has analyzed the wireframe and extracted the UI components below. Please verify and edit directly if there are any misidentifications before continuing.")
            
            # Show original image
            if st.session_state.image_bytes:
                with st.expander("View Source Mockup"):
                    st.image(st.session_state.image_bytes, use_container_width=True)
            
            st.markdown("#### Detected Components")
            
            # Form for editing
            page_name_input = st.text_input("Screen name", value=getattr(st.session_state.cache_vision, 'page_name', 'UI'))
            
            # Use data editor for elements
            el_data = getattr(st.session_state.cache_vision, 'elements', [])
            df_elements = pd.DataFrame([e.model_dump() if hasattr(e, 'model_dump') else e for e in el_data])
            edited_df = st.data_editor(df_elements, use_container_width=True, num_rows="dynamic")
            
            # Flow target (detected user flows)
            flows = getattr(st.session_state.cache_vision, 'detected_user_flows', [])
            flows_str = "\n".join(flows)
            flows_input = st.text_area("Detected User Flows", value=flows_str, height=100)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✓ Approve & Continue", type="primary", use_container_width=True):
                    hitl1_start = st.session_state.step_timings.get('hitl1_start', _time.time())
                    st.session_state.step_timings['hitl1'] = round(_time.time() - hitl1_start, 2)
                    st.session_state.step_timings['hitl1_subtitle'] = "Approved without edits"
                    st.session_state.pipeline_state = 'PROCESSING_BA'
                    st.rerun()
            with col2:
                if st.button("📝 Approve (Edited)", use_container_width=True):
                    # Save edited data back to cache_vision
                    st.session_state.cache_vision.page_name = page_name_input
                    
                    # reconstruct elements list
                    from src.schemas.ui_schema import UIElement
                    new_elements = []
                    for _, row in edited_df.iterrows():
                        new_elements.append(UIElement(
                            id=row.get('id', ''),
                            type=row.get('type', ''),
                            label=row.get('label', ''),
                            description=row.get('description', '')
                        ))
                    st.session_state.cache_vision.elements = new_elements
                    st.session_state.cache_vision.detected_user_flows = [f.strip() for f in flows_input.split('\n') if f.strip()]
                    
                    hitl1_start = st.session_state.step_timings.get('hitl1_start', _time.time())
                    st.session_state.step_timings['hitl1'] = round(_time.time() - hitl1_start, 2)
                    st.session_state.step_timings['hitl1_subtitle'] = "Approved with edits"
                    st.session_state.pipeline_state = 'PROCESSING_BA'
                    st.rerun()
            with col3:
                if st.button("🔄 Reject & Regenerate", use_container_width=True):
                    st.session_state.cache_vision = None
                    if 'eval_session_id' not in st.session_state or st.session_state.eval_session_id is None:
                        try:
                            sess_id = st.session_state.db.create_eval_session(st.session_state.image_name if 'image_name' in st.session_state else "Unknown")
                            st.session_state.eval_session_id = sess_id
                            st.session_state.eval_session_start_time = _time.time()
                        except Exception as e:
                            pass
                    st.session_state.pipeline_state = 'PROCESSING_VISION'
                    st.rerun()
            
            st.caption("Tip: Edit directly in the cells and click 'Approve (Edited)'. You don't need to reject the whole thing for a minor typo.")

    # ========================================================
    # STATE 4: PROCESSING_BA (with Live Streaming)
    # ========================================================
    elif st.session_state.pipeline_state == 'PROCESSING_BA':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            # Record step start time
            if 'ba_start' not in st.session_state.step_timings:
                st.session_state.step_timings['ba_start'] = _time.time()
            
            render_pipeline_progress('PROCESSING_BA', "Generating SRS — drafting requirements...")
            
            # Live stream container
            stream_placeholder = st.empty()
            
            # HITL-2 preview notice
            st.markdown(
                '<div class="hitl-notice">'
                '  <div class="hitl-notice-text">ℹ️ HITL-2 checkpoint coming up — you\'ll review the SRS draft before Diagram Agent starts.</div>'
                '  <div class="hitl-notice-sub">Estimated wait time for your review: ready in ~1 min.</div>'
                '</div>',
                unsafe_allow_html=True
            )
            
            with st.status("BA Agent is drafting requirements...", expanded=True) as status_box:
                pipeline_error = False
                error_message = ""
                
                try:
                    vision_j = st.session_state.cache_vision.model_dump_json() if hasattr(st.session_state.cache_vision, 'model_dump_json') else json.dumps(st.session_state.cache_vision.__dict__, separators=(',', ':'))
                    rag_context = ""
                    
                    if st.session_state.pdf_bytes:
                        st.write("[RAG Engine] Indexing business rules from PDF...")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                            tmp_pdf.write(st.session_state.pdf_bytes)
                            tmp_pdf_path = tmp_pdf.name
                        try:
                            from src.core.pdf_extractor import extract_text_from_pdf
                            from src.core.rag_engine import sliding_window_chunking
                            raw_text = extract_text_from_pdf(tmp_pdf_path)
                            chunks = sliding_window_chunking(raw_text, 300, 50)
                            st.session_state.vector_store.add_chunks(chunks)
                            st.write("[RAG Engine] Successfully loaded context.")
                            
                            st.write("[RAG Engine] Querying knowledge base...")
                            page_n = getattr(st.session_state.cache_vision, 'page_name', 'UI')
                            rag_results = st.session_state.vector_store.search(page_n, top_k=5)
                            rag_context = "\n---\n".join(rag_results)
                            st.session_state.rag_context = rag_context

                        except Exception as e:
                            st.write(f"[RAG Engine] Warning: Failed to parse PDF ({e})")

                    if st.session_state.cache_ba is None:
                        st.write("[BAAgent] Drafting Software Requirements Specification (SRS)...")
                        
                        if Config.GEMINI_STREAMING:
                            # Streaming callback: update the placeholder in real-time
                            def on_stream_chunk(accumulated_text):
                                # Show a cleaned-up preview (truncate for readability)
                                preview = accumulated_text
                                if len(preview) > 800:
                                    preview = "..." + preview[-800:]
                                stream_placeholder.markdown(
                                    f'<div class="live-stream-label"><div class="live-dot"></div> BA Agent — live output stream</div>'
                                    f'<div class="live-stream-box">{preview}▌</div>',
                                    unsafe_allow_html=True
                                )
                            
                            st.session_state.cache_ba = st.session_state.ba_agent.generate_requirements_stream(
                                vision_j, rag_context, stream_callback=on_stream_chunk
                            )
                        else:
                            st.write("[System] Streaming disabled for higher quota safety. Executing single call...")
                            st.session_state.cache_ba = st.session_state.ba_agent.generate_requirements(
                                vision_j, rag_context
                            )
                        
                        # Capture timing
                        meta = getattr(st.session_state.ba_agent, 'last_run_metadata', {"time": 0, "tokens": 0})
                        st.session_state.step_timings['ba'] = meta['time']
                        
                        fr_count = len(getattr(st.session_state.cache_ba, 'functional_requirements', []))
                        st.session_state.step_timings['ba_subtitle'] = f"Completed — {fr_count} functional requirements"
                        
                        # Clear the stream placeholder after completion (if streaming enabled)
                        if Config.GEMINI_STREAMING:
                            stream_placeholder.markdown(
                                f'<div class="live-stream-label">✅ BA Agent — generation complete ({_fmt_time(meta["time"])})</div>',
                                unsafe_allow_html=True
                            )
                        
                        try:
                            out_j = st.session_state.cache_ba.model_dump() if hasattr(st.session_state.cache_ba, 'model_dump') else {}
                            st.session_state.db.log_agent_run(st.session_state.get('eval_session_id'), "BAAgent", 1, {"vision": vision_j}, out_j, meta['time'], meta['tokens'], "success")
                        except Exception: pass
                except Exception as e:
                    pipeline_error = True
                    error_message = f"Business Analysis failed: {e}"

                if pipeline_error:
                    status_box.update(label=f"Pipeline halted: {error_message}", state="error", expanded=True)
                else:
                    status_box.update(label="Business Analysis Completed", state="complete", expanded=False)
            
            if pipeline_error:
                st.error("The pipeline encountered an error.")
                if st.button("🔄 Retry BA Agent", type="primary", use_container_width=True):
                    st.rerun()
            else:
                time.sleep(1)
                st.session_state.step_timings['hitl2_start'] = _time.time()
                st.session_state.pipeline_state = 'HITL_BA'
                st.rerun()


    # ========================================================
    # STATE 5: HITL_BA (Checkpoint 2)
    # ========================================================
    elif st.session_state.pipeline_state == 'HITL_BA':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            render_pipeline_progress('HITL_BA', "Awaiting your review...")
            
            st.markdown("### 2. BA Agent — Confirm SRS Draft ⏳ Pending")
            st.info("The SRS is generated from the UI Tree and RAG policies. Use the text areas below to freely edit the flows and add missing edge cases.")
            
            ba = st.session_state.cache_ba
            
            reqs = getattr(ba, 'functional_requirements', [])
            edited_reqs = []
            
            for i, fr_obj in enumerate(reqs):
                fr = fr_obj if isinstance(fr_obj, dict) else (fr_obj.model_dump() if hasattr(fr_obj, 'model_dump') else fr_obj.__dict__)
                st.markdown(f"**Use case: {fr.get('id')} — {fr.get('name')}**")
                st.write(f"Actor: **{fr.get('actor')}**")
                st.write(f"Description: **{fr.get('description')}**")
                
                main_flow_str = "\n".join(fr.get('main_flow', []))
                edited_main = st.text_area(f"Main flow (AI generated)", value=main_flow_str, height=150, key=f"mf_{i}")
                
                edited_reqs.append({
                    "id": fr.get('id'),
                    "name": fr.get('name'),
                    "description": fr.get('description'),
                    "actor": fr.get('actor'),
                    "priority": fr.get('priority'),
                    "main_flow": [line.strip() for line in edited_main.split('\n') if line.strip()]
                })
                st.markdown("---")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✓ Approve SRS", type="primary", use_container_width=True):
                    hitl2_start = st.session_state.step_timings.get('hitl2_start', _time.time())
                    st.session_state.step_timings['hitl2'] = round(_time.time() - hitl2_start, 2)
                    st.session_state.step_timings['hitl2_subtitle'] = "Approved without edits"
                    st.session_state.pipeline_state = 'PROCESSING_DIAGRAMS'
                    st.rerun()
            with col2:
                if st.button("📝 Approve (Edited)", use_container_width=True):
                    # Save edits
                    from src.schemas.ba_schema import FunctionalRequirement
                    new_reqs = []
                    for r in edited_reqs:
                        new_reqs.append(FunctionalRequirement(**r))
                    st.session_state.cache_ba.functional_requirements = new_reqs
                    hitl2_start = st.session_state.step_timings.get('hitl2_start', _time.time())
                    st.session_state.step_timings['hitl2'] = round(_time.time() - hitl2_start, 2)
                    st.session_state.step_timings['hitl2_subtitle'] = "Approved with edits"
                    st.session_state.pipeline_state = 'PROCESSING_DIAGRAMS'
                    st.rerun()
            with col3:
                if st.button("🔄 Reject & Regenerate", use_container_width=True):
                    st.session_state.cache_ba = None
                    st.session_state.pipeline_state = 'PROCESSING_BA'
                    st.rerun()
                    
            st.caption("Tip: Use the textarea to add edge cases the AI missed - then click 'Approve (Edited)' to keep the good parts and add yours.")

    # ========================================================
    # STATE 6: PROCESSING_DIAGRAMS
    # ========================================================
    elif st.session_state.pipeline_state == 'PROCESSING_DIAGRAMS':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            # Record step start time
            if 'diagrams_start' not in st.session_state.step_timings:
                st.session_state.step_timings['diagrams_start'] = _time.time()
            
            render_pipeline_progress('PROCESSING_DIAGRAMS', "Generating diagrams, running QA audit, and creating Test Cases...")
            
            with st.status("Generating Diagrams, Test Cases, and running QA...", expanded=True) as status_box:
                pipeline_error = False
                error_message = ""
                
                try:
                    ba_j = st.session_state.cache_ba.model_dump_json() if hasattr(st.session_state.cache_ba, 'model_dump_json') else json.dumps(st.session_state.cache_ba.__dict__, separators=(',', ':'))
                    vision_j = st.session_state.cache_vision.model_dump_json() if hasattr(st.session_state.cache_vision, 'model_dump_json') else json.dumps(st.session_state.cache_vision.__dict__, separators=(',', ':'))
                    
                    if st.session_state.cache_diagram is None:
                        st.write("[DiagramAgent] Generating Flowchart and Sequence Diagram...")
                        st.session_state.cache_diagram = st.session_state.diagram_agent.generate_diagrams(ba_j)
                        try:
                            meta = getattr(st.session_state.diagram_agent, 'last_run_metadata', {"time": 0, "tokens": 0})
                            out_j = st.session_state.cache_diagram.model_dump() if hasattr(st.session_state.cache_diagram, 'model_dump') else {}
                            st.session_state.db.log_agent_run(st.session_state.get('eval_session_id'), "DiagramAgent", st.session_state.get('qa_retry_count', 0) + 1, {"ba": ba_j}, out_j, meta['time'], meta['tokens'], "success")
                        except Exception: pass
                    
                    if st.session_state.cache_testcase is None:
                        st.write("[TestCaseAgent] Deriving Test Cases from SRS...")
                        st.session_state.cache_testcase = st.session_state.testcase_agent.generate_test_cases(ba_j)
                        try:
                            meta = getattr(st.session_state.testcase_agent, 'last_run_metadata', {"time": 0, "tokens": 0})
                            out_j = st.session_state.cache_testcase.model_dump() if hasattr(st.session_state.cache_testcase, 'model_dump') else {}
                            st.session_state.db.log_agent_run(st.session_state.get('eval_session_id'), "TestCaseAgent", st.session_state.get('qa_retry_count', 0) + 1, {"ba": ba_j}, out_j, meta['time'], meta['tokens'], "success")
                        except Exception: pass
                    
                    if st.session_state.cache_qa is None:
                        st.write("[QAAgent] Auditing system logic and consistency...")
                        st.session_state.cache_qa = st.session_state.qa_agent.audit_system(
                            vision_j, ba_j, rag_context=st.session_state.get('rag_context', '')
                        )

                        try:
                            meta = getattr(st.session_state.qa_agent, 'last_run_metadata', {"time": 0, "tokens": 0})
                            out_j = st.session_state.cache_qa.model_dump() if hasattr(st.session_state.cache_qa, 'model_dump') else {}
                            status = "success" if getattr(st.session_state.cache_qa, 'is_approved', False) else ("escalated" if st.session_state.get('qa_retry_count',0) >= 2 else "retry")
                            st.session_state.db.log_agent_run(st.session_state.get('eval_session_id'), "QAAgent", st.session_state.get('qa_retry_count', 0) + 1, {}, out_j, meta['time'], meta['tokens'], status)
                        except Exception: pass
                    qa_j = st.session_state.cache_qa.model_dump_json() if hasattr(st.session_state.cache_qa, 'model_dump_json') else json.dumps(st.session_state.cache_qa.__dict__, separators=(',', ':'))
                    
                except Exception as e:
                    pipeline_error = True
                    error_message = f"Generation failed: {e}"

                qa_approved = getattr(st.session_state.cache_qa, 'is_approved', False)
                
                if pipeline_error:
                    status_box.update(label=f"Pipeline halted: {error_message}", state="error", expanded=True)
                elif not qa_approved:
                    status_box.update(label="QA Failed", state="error", expanded=True)
                else:
                    status_box.update(label="Diagrams & QA Completed", state="complete", expanded=False)
            
            if pipeline_error:
                st.error("The pipeline encountered an error.")
                if st.button("🔄 Retry", type="primary", use_container_width=True):
                    st.rerun()
            elif not qa_approved:
                # QA Retry Logic
                st.session_state.qa_retry_count += 1
                if st.session_state.qa_retry_count < 3:
                    st.warning(f"QA Agent detected issues. Auto-retrying ({st.session_state.qa_retry_count}/3)...")
                    time.sleep(2)
                    st.session_state.cache_diagram = None
                    st.session_state.cache_testcase = None
                    st.session_state.cache_qa = None
                    st.rerun()
                else:
                    st.error("QA Agent detected issues continuously. Escalating to human review.")
                    time.sleep(2)
                    st.session_state.pipeline_state = 'HITL_QA'
                    st.rerun()
            else:
                # Save to DB
                if st.session_state.active_project_id is None:
                    try:
                        st.write("[DBAgent] Persisting artifacts to cloud storage...")
                        diag_j = st.session_state.cache_diagram.model_dump_json() if hasattr(st.session_state.cache_diagram, 'model_dump_json') else json.dumps(st.session_state.cache_diagram.__dict__, separators=(',', ':'))
                        tc_j = st.session_state.cache_testcase.model_dump_json() if hasattr(st.session_state.cache_testcase, 'model_dump_json') else json.dumps(st.session_state.cache_testcase.__dict__, separators=(',', ':')) if st.session_state.cache_testcase else None
                        
                        qa_dict = json.loads(qa_j) if qa_j else {}
                        qa_dict['_step_timings'] = st.session_state.get('step_timings', {})
                        qa_j_with_timings = json.dumps(qa_dict, separators=(',', ':'))
                        
                        resp = st.session_state.db.save_project(
                            st.session_state.user.id, st.session_state.image_name, 
                            st.session_state.image_bytes, vision_j, ba_j, diag_j, qa_j_with_timings, tc_j
                        )
                        if getattr(resp, 'data', None) and len(resp.data) > 0:
                            st.session_state.active_project_id = resp.data[0]['id']
                    except Exception as db_e:
                        st.error(f"Database error: {db_e}")
                time.sleep(1)
                try:
                    if st.session_state.get('eval_session_id'):
                        tot_time = round(_time.time() - st.session_state.get('eval_session_start_time', _time.time()), 2)
                        st.session_state.db.update_eval_session(st.session_state.eval_session_id, tot_time, "approved")
                        diag_j = st.session_state.cache_diagram.model_dump_json() if hasattr(st.session_state.cache_diagram, 'model_dump_json') else '{}'
                        st.session_state.db.save_generated_document(st.session_state.eval_session_id, 1, ba_j, diag_j, '{}', qa_j)
                except Exception: pass
                
                # Capture diagrams step timing
                diag_start = st.session_state.step_timings.get('diagrams_start', _time.time())
                st.session_state.step_timings['diagrams'] = round(_time.time() - diag_start, 2)
                st.session_state.step_timings['diagrams_subtitle'] = "Diagram + QA completed — approved"
                
                st.session_state.pipeline_state = 'COMPLETED'
                st.rerun()

    # ========================================================
    # STATE 7: HITL_QA (Checkpoint 3)
    # ========================================================
    elif st.session_state.pipeline_state == 'HITL_QA':
        if 'hitl_start_time' not in st.session_state: st.session_state.hitl_start_time = _time.time()
        
        st.markdown("### QA Review — Session #" + (st.session_state.get('eval_session_id', '???')[:8] if st.session_state.get('eval_session_id') else 'N/A'))
        qa = st.session_state.cache_qa
        
        struct_checks = getattr(qa, 'structural_checks', [])
        struct_err = sum(1 for c in struct_checks if getattr(c, 'type', '') == 'error')
        struct_warn = sum(1 for c in struct_checks if getattr(c, 'type', '') == 'warning')
        
        consist_checks = getattr(qa, 'consistency_checks', [])
        consist_warn = sum(1 for c in consist_checks if getattr(c, 'type', '') == 'warning')
        
        domain_checks = getattr(qa, 'domain_checks', [])
        domain_passed = sum(1 for c in domain_checks if getattr(c, 'passed', False))
        domain_total = len(domain_checks)
        
        decision = getattr(qa, 'decision', None)
        d_action = getattr(decision, 'action', 'approve') if decision else 'approve'
        d_reason = getattr(decision, 'reason', 'No issues') if decision else 'No issues'

        # Action pill header
        action_color = "#f59e0b" if d_action != 'approve' else "#10b981"
        action_text = "Action required" if d_action != 'approve' else "Approved"
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">'
            f'<div style="color: #6b7280;">Feature: <b>Checkout flow</b> &middot; Attempt: <b>{st.session_state.qa_retry_count+1}/3</b></div>'
            f'<div style="background-color: {action_color}20; color: {action_color}; padding: 4px 12px; border-radius: 16px; font-weight: bold; font-size: 14px;">⚠️ {action_text}</div>'
            f'</div>', 
            unsafe_allow_html=True
        )

        # 4 Metrics Columns
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            with st.container(border=True):
                se_count = getattr(qa, 'structural_errors_count', struct_err)
                st.metric("Structural Errors", f"{se_count}")
                if se_count > 0:
                    st.markdown(f'<span style="background-color: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">Failed</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="background-color: #d1fae5; color: #059669; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">Passed</span>', unsafe_allow_html=True)
        with c2:
            with st.container(border=True):
                score_consist = getattr(qa, 'entity_consistency_score', 100 if consist_warn == 0 else max(0, 100 - consist_warn * 10))
                st.metric("Entity Consistency", f"{score_consist}%")
                if score_consist < 100:
                    st.markdown(f'<span style="background-color: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">{consist_warn} Warnings</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="background-color: #d1fae5; color: #059669; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">Passed</span>', unsafe_allow_html=True)
        with c3:
            with st.container(border=True):
                compliance_rate = getattr(qa, 'domain_policy_compliance_rate', 100.0)
                st.metric("Policy Compliance", f"{compliance_rate:.1f}%")
                failed_domain = sum(1 for c in domain_checks if not getattr(c, 'passed', False))
                if failed_domain > 0:
                    st.markdown(f'<span style="background-color: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">{failed_domain} Failed</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="background-color: #d1fae5; color: #059669; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">Compliant</span>', unsafe_allow_html=True)
        with c4:
            with st.container(border=True):
                density = getattr(qa, 'edge_case_density', 0.0)
                st.metric("Edge-Case Density", f"{density:.2f}")
                if density < 1.0:
                    st.markdown(f'<span style="background-color: #fef3c7; color: #d97706; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">Low Density</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="background-color: #d1fae5; color: #059669; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">Robust</span>', unsafe_allow_html=True)


        # Alert Box
        if d_action != 'approve':
            st.error(f"**QA decision — retry required**\n\n→ {d_reason}", icon="🚨")
        else:
            st.success("**QA decision — ready to deploy**\n\n→ All critical checks passed.", icon="✅")

        # Domain Checklist
        st.markdown("#### 🛡️ Domain checklist")
        for c in domain_checks:
            c_id = getattr(c, 'id', '')
            c_sev = getattr(c, 'severity', 'LOW')
            c_msg = getattr(c, 'message', '')
            c_pass = getattr(c, 'passed', False)
            
            icon = "✅" if c_pass else "❌"
            color = "#059669" if c_pass else "#dc2626"
            bg = "#d1fae5" if c_pass else "#fee2e2"
            pass_text = "Pass" if c_pass else "Fail"
            
            sev_badge = f'<span style="background-color: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 8px;">{c_sev}</span>' if not c_pass and c_sev in ['CRITICAL', 'HIGH'] else ''
            
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e5e7eb;">'
                f'  <div style="display: flex; align-items: flex-start; gap: 12px;">'
                f'    <div style="font-size: 16px;">{icon}</div>'
                f'    <div>'
                f'      <div style="font-weight: 600; font-size: 15px; color: #111827;">{c_id} &middot; {c_msg} {sev_badge}</div>'
                f'    </div>'
                f'  </div>'
                f'  <div style="background-color: {bg}; color: {color}; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">{pass_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
        st.markdown("<br>", unsafe_allow_html=True)

        # Structural Validation
        st.markdown("#### 🧱 Structural validation")
        with st.container(border=True):
            if not struct_checks:
                st.markdown(f'<div style="padding: 8px 0; color: #059669; font-weight: 500;">✅ All structural and consistency checks passed.</div>', unsafe_allow_html=True)
            for c in struct_checks:
                c_msg = getattr(c, 'message', '')
                c_path = getattr(c, 'path', '')
                st.markdown(
                    f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e5e7eb;">'
                    f'  <div style="display: flex; align-items: center; gap: 12px;">'
                    f'    <div style="font-size: 16px;">❌</div>'
                    f'    <div><span style="font-weight: 600; color: #111827;">{c_path}</span> — <span style="color: #4b5563;">{c_msg}</span></div>'
                    f'  </div>'
                    f'  <div style="background-color: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">Error</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            for c in consist_checks:
                c_msg = getattr(c, 'message', '')
                st.markdown(
                    f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e5e7eb;">'
                    f'  <div style="display: flex; align-items: center; gap: 12px;">'
                    f'    <div style="font-size: 16px;">⚠️</div>'
                    f'    <div><span style="font-weight: 600; color: #111827;">Consistency</span> — <span style="color: #4b5563;">{c_msg}</span></div>'
                    f'  </div>'
                    f'  <div style="background-color: #fef3c7; color: #d97706; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">Warning</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        reviewer_notes = st.text_area("Reviewer notes (sent to agent on retry)", placeholder="Ví dụ: EC-07 cần thêm đoạn xử lý reject khi signature sai — trả về 403 và log vào audit trail...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Fix failed agents", use_container_width=True):
                spent = round(_time.time() - st.session_state.hitl_start_time, 2)
                st.session_state.db.log_human_review(st.session_state.get('eval_session_id'), "HITL-3", "reject", {}, {}, spent)
                st.session_state.qa_retry_count = 0
                st.session_state.cache_diagram = None
                st.session_state.cache_testcase = None
                st.session_state.cache_qa = None
                if reviewer_notes:
                    st.session_state.user_notes += f"\n[QA Feedback]: {reviewer_notes}"
                st.session_state.pipeline_state = 'PROCESSING_DIAGRAMS'
                st.rerun()
        with col2:
            if st.button("✅ Override & approve", type="primary", use_container_width=True):
                spent = round(_time.time() - st.session_state.hitl_start_time, 2)
                st.session_state.db.log_human_review(st.session_state.get('eval_session_id'), "HITL-3", "approve", {}, {}, spent)
                if st.session_state.active_project_id is None:
                    vision_j = st.session_state.cache_vision.model_dump_json() if hasattr(st.session_state.cache_vision, 'model_dump_json') else json.dumps(st.session_state.cache_vision.__dict__)
                    ba_j = st.session_state.cache_ba.model_dump_json() if hasattr(st.session_state.cache_ba, 'model_dump_json') else json.dumps(st.session_state.cache_ba.__dict__)
                    diag_j = st.session_state.cache_diagram.model_dump_json() if hasattr(st.session_state.cache_diagram, 'model_dump_json') else json.dumps(st.session_state.cache_diagram.__dict__)
                    qa_j = st.session_state.cache_qa.model_dump_json() if hasattr(st.session_state.cache_qa, 'model_dump_json') else json.dumps(st.session_state.cache_qa.__dict__)
                    tc_j = st.session_state.cache_testcase.model_dump_json() if hasattr(st.session_state.cache_testcase, 'model_dump_json') else json.dumps(st.session_state.cache_testcase.__dict__) if st.session_state.cache_testcase else None
                    
                    qa_dict = json.loads(qa_j) if qa_j else {}
                    qa_dict['_step_timings'] = st.session_state.get('step_timings', {})
                    qa_j_with_timings = json.dumps(qa_dict, separators=(',', ':'))
                    
                    try:
                        resp = st.session_state.db.save_project(
                            st.session_state.user.id, st.session_state.image_name, 
                            st.session_state.image_bytes, vision_j, ba_j, diag_j, qa_j_with_timings, tc_j
                        )
                        if getattr(resp, 'data', None) and len(resp.data) > 0:
                            st.session_state.active_project_id = resp.data[0]['id']
                    except Exception:
                        pass
                
                # Evaluation Telemetry
                try:
                    if st.session_state.get('eval_session_id'):
                        tot_time = round(_time.time() - st.session_state.get('eval_session_start_time', _time.time()), 2)
                        st.session_state.db.update_eval_session(st.session_state.eval_session_id, tot_time, "approved")
                        st.session_state.db.save_generated_document(st.session_state.eval_session_id, 1, ba_j, diag_j, '{}', qa_j)
                except Exception: pass

                st.session_state.pipeline_state = 'COMPLETED'
                st.rerun()
        with col3:
            if st.button("❌ Reject all", use_container_width=True):
                spent = round(_time.time() - st.session_state.hitl_start_time, 2)
                st.session_state.db.log_human_review(st.session_state.get('eval_session_id'), "HITL-3", "reject_all", {}, {}, spent)
                
                try:
                    if st.session_state.get('eval_session_id'):
                        tot_time = round(_time.time() - st.session_state.get('eval_session_start_time', _time.time()), 2)
                        st.session_state.db.update_eval_session(st.session_state.eval_session_id, tot_time, "rejected")
                except Exception: pass

                st.session_state.pipeline_state = 'UPLOAD'
                st.session_state.cache_vision = None
                st.session_state.cache_ba = None
                st.session_state.cache_diagram = None
                st.session_state.cache_testcase = None
                st.session_state.cache_qa = None
                st.rerun()
    # ========================================================
    # STATE 8: COMPLETED
    # ========================================================
    elif st.session_state.pipeline_state == 'COMPLETED':
        _, col_center, _ = st.columns([1, 4, 1])
        with col_center:
            render_pipeline_progress('COMPLETED', "All steps completed successfully!")
            
            st.success("✅ Workflow Completed Successfully!")
            
            # ---- CACHED DOCUMENT EXPORT ----
            @st.cache_data(show_spinner=False, ttl=3600)
            def generate_cached_docs(_ba_j, _diag_j, _tc_j):
                from src.core.document_exporter import generate_srs_docx, convert_docx_to_pdf
                import tempfile, os, traceback
                out_dir = tempfile.mkdtemp()
                docx_path = os.path.join(out_dir, "SRS_Document.docx")
                pdf_path = os.path.join(out_dir, "SRS_Document.pdf")
                template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "srs_template-ieee.docx"))
                
                try:
                    if os.path.exists(template_path):
                        generate_srs_docx(_ba_j, template_path, docx_path, _diag_j, _tc_j)
                        
                        with open(docx_path, "rb") as f:
                            docx_bytes = f.read()
                            
                        pdf_bytes = None
                        if convert_docx_to_pdf(docx_path, pdf_path):
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                        
                        return docx_bytes, pdf_bytes, None
                    else:
                        return None, None, "Template file not found."
                except Exception as e:
                    return None, None, f"{e}\n{traceback.format_exc()}"
            
            # Tabbed results view
            tab_export, tab_diagrams, tab_testcases, tab_summary = st.tabs(["📄 SRS Export", "🧩 Diagrams", "🧪 Test Cases", "📊 Pipeline Summary"])
            
            # ---- TAB 1: SRS Export ----
            with tab_export:
                st.markdown("### Export Final Documents")
                ba_j = st.session_state.cache_ba.model_dump_json() if hasattr(st.session_state.cache_ba, 'model_dump_json') else json.dumps(st.session_state.cache_ba.__dict__)
                
                with st.spinner("Generating IEEE Standard Documents..."):
                    diag_j = None
                    if hasattr(st.session_state, 'cache_diagram') and st.session_state.cache_diagram:
                        diag_j = st.session_state.cache_diagram.model_dump_json() if hasattr(st.session_state.cache_diagram, 'model_dump_json') else json.dumps(st.session_state.cache_diagram.__dict__)

                    tc_j = None
                    if hasattr(st.session_state, 'cache_testcase') and st.session_state.cache_testcase:
                        tc_j = st.session_state.cache_testcase.model_dump_json() if hasattr(st.session_state.cache_testcase, 'model_dump_json') else json.dumps(st.session_state.cache_testcase.__dict__)
                    
                    docx_bytes, pdf_bytes, err = generate_cached_docs(ba_j, diag_j, tc_j)
                    
                    if err:
                        st.error(f"Error generating document: {err}")
                    elif docx_bytes:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📝 Download IEEE SRS (DOCX)", 
                                docx_bytes, 
                                file_name="IEEE_SRS.docx", 
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                type="primary",
                                use_container_width=True
                            )
                        with col2:
                            if pdf_bytes:
                                st.download_button(
                                    "📄 Download PDF", 
                                    pdf_bytes, 
                                    file_name="IEEE_SRS.pdf", 
                                    mime="application/pdf", 
                                    type="primary",
                                    use_container_width=True
                                )
                            else:
                                st.info("PDF Generation not supported on this OS without Word/LibreOffice.")
            
            # ---- TAB 2: Diagrams ----
            with tab_diagrams:
                diagram = st.session_state.cache_diagram
                if diagram:
                    flowchart_code = getattr(diagram, 'flowchart_diagram', '')
                    sequence_code = getattr(diagram, 'sequence_diagram', '')
                    explanation = getattr(diagram, 'diagram_explanation', '')
                    
                    st.markdown("### Flowchart — Functional Logic Flow")
                    if flowchart_code and flowchart_code.strip():
                        render_mermaid(flowchart_code)
                        with st.expander("View Mermaid source code"):
                            st.code(flowchart_code, language="text")
                    else:
                        st.warning("No flowchart data generated by Diagram Agent.")
                    
                    st.markdown("---")
                    st.markdown("### Sequence Diagram — System Interaction")
                    if sequence_code and sequence_code.strip():
                        render_mermaid(sequence_code)
                        with st.expander("View Mermaid source code"):
                            st.code(sequence_code, language="text")
                    else:
                        st.warning("No sequence diagram data generated by Diagram Agent.")
                    
                    if explanation:
                        st.markdown("---")
                        st.info(f"💡 **AI Explanation:** {explanation}")
                    
                    # Regenerate button
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🔄 Regenerate Diagrams", use_container_width=True):
                        st.session_state.cache_diagram = None
                        st.session_state.cache_testcase = None
                        st.session_state.cache_qa = None
                        st.session_state.pipeline_state = 'PROCESSING_DIAGRAMS'
                        st.rerun()
                else:
                    st.warning("No diagram data available.")
            
            # ---- TAB 3: Test Cases ----
            with tab_testcases:
                st.markdown("### Derived Test Cases")
                testcases = st.session_state.cache_testcase
                if testcases and hasattr(testcases, 'test_cases'):
                    tc_list = testcases.test_cases
                    st.success(f"Generated {len(tc_list)} test cases derived from the SRS.")
                    for tc in tc_list:
                        with st.expander(f"[{getattr(tc, 'priority', 'Medium')} Priority] {getattr(tc, 'test_id', 'TC')} - {getattr(tc, 'scenario', 'Scenario')}"):
                            st.markdown(f"**Test Type:** {getattr(tc, 'test_type', 'Functional')}")
                            st.markdown(f"**Precondition:** {getattr(tc, 'precondition', 'None')}")
                            
                            steps = getattr(tc, 'steps', [])
                            if steps:
                                st.markdown("**Steps:**")
                                for s in steps:
                                    st.markdown(f"{getattr(s, 'step_number', '')}. {getattr(s, 'action', '')} ➔ *{getattr(s, 'expected_result', '')}*")
                            
                            st.markdown(f"**Final Expected Result:** {getattr(tc, 'final_expected_result', 'None')}")
                            
                            auto_hint = getattr(tc, 'automation_hint', '')
                            if auto_hint:
                                st.info(f"🤖 **Automation Hint:** `{auto_hint}`")
                                
                            bdd = getattr(tc, 'bdd_gherkin', '')
                            if bdd:
                                st.markdown("**BDD Gherkin Format:**")
                                st.code(bdd, language="gherkin")
                else:
                    st.warning("No test case data available.")

            # ---- TAB 4: Pipeline Summary ----
            with tab_summary:
                st.markdown("### Pipeline Execution Summary")
                timings = st.session_state.get('step_timings', {})
                
                if timings:
                    summary_data = []
                    
                    if 'vision' in timings:
                        summary_data.append({"Step": "👁️ Vision Agent", "Duration": _fmt_time(timings['vision']), "Type": "Agent"})
                    if 'hitl1' in timings:
                        summary_data.append({"Step": "✋ HITL-1 Review", "Duration": _fmt_time(timings['hitl1']), "Type": "Human"})
                    if 'ba' in timings:
                        summary_data.append({"Step": "📝 BA Agent", "Duration": _fmt_time(timings['ba']), "Type": "Agent"})
                    if 'hitl2' in timings:
                        summary_data.append({"Step": "✋ HITL-2 Review", "Duration": _fmt_time(timings['hitl2']), "Type": "Human"})
                    if 'diagrams' in timings:
                        summary_data.append({"Step": "🧩 Diagram + QA", "Duration": _fmt_time(timings['diagrams']), "Type": "Agent"})
                    
                    if summary_data:
                        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
                    
                    # Total pipeline time
                    start = st.session_state.get('pipeline_start_time')
                    if start:
                        total = round(_time.time() - start, 2)
                    else:
                        total = round(sum([v for v in timings.values() if isinstance(v, (int, float))]), 2)
                        
                    agent_time = sum(timings.get(k, 0) for k in ['vision', 'ba', 'diagrams'])
                    human_time = sum(timings.get(k, 0) for k in ['hitl1', 'hitl2'])
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Total Pipeline", _fmt_time(total))
                    with c2:
                        st.metric("Agent Processing", _fmt_time(agent_time))
                    with c3:
                        st.metric("Human Review", _fmt_time(human_time))
                else:
                    if st.session_state.get('active_project_id'):
                        st.info("Project loaded from history. Execution timings are not preserved in history.")
                    else:
                        st.info("No timing data available for this run.")

if __name__ == "__main__":
    main()
