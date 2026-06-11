import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove TestCaseAgent instantiation
content = re.sub(r"\s*if 'testcase_agent' not in st\.session_state: st\.session_state\.testcase_agent = TestCaseAgent\(\)\n", "\n", content)

# 2. Fix loops
content = content.replace("['cache_vision', 'cache_ba', 'cache_diagram', 'cache_qa', 'cache_testcase']", "['cache_vision', 'cache_ba', 'cache_diagram', 'cache_qa']")

# 3. Remove cache_testcase = dict_to_obj...
content = re.sub(r"\s*st\.session_state\.cache_testcase = dict_to_obj\(details\.get\('testcase_data', details\.get\('da_data'\)\)\)\n", "\n", content)

# 4. Text replacements
content = content.replace("Generating diagrams, running QA audit, and creating Test Cases...", "Generating diagrams and running QA audit...")
content = content.replace("Generating Diagrams, Test Cases, and running QA...", "Generating Diagrams and running QA...")

# 5. Remove Test Case Generation block
tc_gen_pattern = r"\s*if st\.session_state\.cache_testcase is None:\s*st\.write\(\"\[TestCaseAgent\][^\n]+\n\s*st\.session_state\.cache_testcase = st\.session_state\.testcase_agent\.generate_test_cases[^\n]+\n(?:\s*if hasattr[^\n]+\n\s*meta = [^\n]+\n\s*out_j = [^\n]+\n\s*st\.session_state\.db\.log_agent_run[^\n]+\n)?"
content = re.sub(tc_gen_pattern, "", content)

# 6. Remove cache reset
content = re.sub(r"\s*st\.session_state\.cache_testcase = None\n", "\n", content)

# 7. Remove tc_j assignments
tc_j_pattern = r"\s*tc_j = st\.session_state\.cache_testcase\.model_dump_json\(\)[^\n]+\n"
content = re.sub(tc_j_pattern, "\n", content)

# 8. Remove tc_j from save_project calls
content = re.sub(r"st\.session_state\.image_bytes, vision_j, ba_j, diag_j, qa_j_with_timings, tc_j\)", "st.session_state.image_bytes, vision_j, ba_j, diag_j, qa_j_with_timings)", content)

# 9. Update generate_cached_docs signature
content = content.replace("def generate_cached_docs(_ba_j, _diag_j, _tc_j):", "def generate_cached_docs(_ba_j, _diag_j):")
content = content.replace("generate_srs_docx(_ba_j, template_path, docx_path, _diag_j, _tc_j)", "generate_srs_docx(_ba_j, template_path, docx_path, _diag_j)")
content = content.replace("docx_bytes, pdf_bytes, err = generate_cached_docs(ba_j, diag_j, tc_j)", "docx_bytes, pdf_bytes, err = generate_cached_docs(ba_j, diag_j)")

# 10. Fix tabs
content = content.replace('tab_export, tab_diagrams, tab_testcases, tab_summary = st.tabs(["📄 SRS Export", "🧩 Diagrams", "🧪 Test Cases", "📊 Pipeline Summary"])', 'tab_export, tab_diagrams, tab_summary = st.tabs(["📄 SRS Export", "🧩 Diagrams", "📊 Pipeline Summary"])')

# 11. Remove tab_testcases block
tc_tab_pattern = r"\s*# ---- TAB 3: Test Cases ----\s*with tab_testcases:[\s\S]*?(?=\s*# ---- TAB 4: Pipeline Summary ----)"
content = re.sub(tc_tab_pattern, "\n                        ", content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.py cleaned.")
