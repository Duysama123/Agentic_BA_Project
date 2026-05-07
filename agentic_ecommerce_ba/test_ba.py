import streamlit as st
import os
import sys
import tempfile
import time
import pandas as pd
import streamlit.components.v1 as components

def render_mermaid(code: str):
    """Render Mermaid Diagram bằng HTML Component và JS nhúng."""
    cleaned_code = code.replace('"', '\\"') if '"' in code else code
    html_string = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'base' }});
        </script>
    </head>
    <body style="background-color: transparent;">
        <pre class="mermaid">
{code}
        </pre>
    </body>
    </html>
    '''
    components.html(html_string, height=600, scrolling=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.vision_agent import VisionAgent
from src.agents.ba_agent import BAAgent
from src.agents.diagram_agent import DiagramAgent
from src.agents.data_agent import DataArchitectAgent
from src.agents.qa_agent import QAAgent
from src.rag_engine.chunker import extract_text_from_pdf, sliding_window_chunking
from src.rag_engine.vector_store import RAGVectorStore
from src.core.i18n import t, init_language_selector

def main():
    st.set_page_config(page_title=t("ba_page_title"), layout="wide")
    init_language_selector()
    
    st.title(t("ba_title"))
    st.write(t("ba_desc"))

    # ====== Khởi tạo Agents ====== #
    if 'vision_agent' not in st.session_state:
        try: st.session_state.vision_agent = VisionAgent()
        except Exception as e: st.error(f"{t('error_init_vision')}: {e}"); st.stop()
    if 'ba_agent' not in st.session_state:
        try: st.session_state.ba_agent = BAAgent()
        except Exception as e: st.error(f"{t('error_init_ba')}: {e}"); st.stop()
    if 'diagram_agent' not in st.session_state:
        try: st.session_state.diagram_agent = DiagramAgent()
        except Exception as e: st.error(f"Lỗi Diagram Agent: {e}"); st.stop()
    if 'data_agent' not in st.session_state:
        try: st.session_state.data_agent = DataArchitectAgent()
        except Exception as e: st.error(f"Lỗi Data Architect Agent: {e}"); st.stop()
    if 'qa_agent' not in st.session_state:
        try: st.session_state.qa_agent = QAAgent()
        except Exception as e: st.error(f"Lỗi QA Agent: {e}"); st.stop()
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = RAGVectorStore()
    if 'rag_ready' not in st.session_state:
        st.session_state.rag_ready = False
        
    # ====== Khởi tạo Trạng thái FSM Cache ====== #
    if 'cache_vision' not in st.session_state: st.session_state.cache_vision = None
    if 'cache_ba' not in st.session_state: st.session_state.cache_ba = None
    if 'cache_diagram' not in st.session_state: st.session_state.cache_diagram = None
    if 'cache_da' not in st.session_state: st.session_state.cache_da = None
    if 'cache_qa' not in st.session_state: st.session_state.cache_qa = None
    if 'uploaded_img_id' not in st.session_state: st.session_state.uploaded_img_id = None
    if 'pipeline_started' not in st.session_state: st.session_state.pipeline_started = False

    st.markdown("---")
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.info(t("ba_step1a"))
        uploaded_image = st.file_uploader(t("ba_upload_img"), type=["jpg", "jpeg", "png"])
        user_notes = st.text_input(t("ba_notes"), "")

    with col_right:
        st.info(t("ba_step1b"))
        uploaded_pdf = st.file_uploader(t("ba_upload_pdf"), type=["pdf"])
        if uploaded_pdf and not st.session_state.rag_ready:
            if st.button(t("ba_btn_index"), use_container_width=True):
                with st.spinner(t("ba_indexing")):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_pdf.getbuffer())
                        tmp_path = tmp.name
                    try:
                        raw_text = extract_text_from_pdf(tmp_path)
                        chunks = sliding_window_chunking(raw_text, chunk_size=300, overlap=50)
                        st.session_state.vector_store.add_chunks(chunks)
                        st.session_state.rag_ready = True
                        st.success(t("ba_index_ok", count=len(chunks)))
                    except Exception as e:
                        st.error(f"{t('error_pdf')}: {e}")
                    finally:
                        try: os.unlink(tmp_path)
                        except: pass
        elif st.session_state.rag_ready:
            st.success(t("ba_faiss_ready"))

    st.markdown("---")
    st.write(t("ba_step2"))

    if uploaded_image is not None:
        
        # Tự động gỡ bộ nhớ tạm nếu user thả ảnh mới vào
        if st.session_state.uploaded_img_id != uploaded_image.file_id:
            st.session_state.cache_vision = None
            st.session_state.cache_ba = None
            st.session_state.cache_diagram = None
            st.session_state.cache_da = None
            st.session_state.cache_qa = None
            st.session_state.pipeline_started = False
            st.session_state.refinement_round = 0
            st.session_state.uploaded_img_id = uploaded_image.file_id
            st.info("🔄 Hệ thống nhận diện Ảnh mới đã được upload! Bộ nhớ Trí tuệ LLM Cache cũ đã được dọn dẹp sạch sẽ.")
            
        col_btn1, col_btn2 = st.columns([4, 1])
        with col_btn1:
            run_clicked = st.button("🚀 Chạy Pipeline Agentic LLM (Tích hợp Smart Cache)", type="primary", use_container_width=True)
        with col_btn2:
            clear_clicked = st.button("🗑️ Xóa sạch Cache", use_container_width=True)
            
        if clear_clicked:
            st.session_state.cache_vision = None
            st.session_state.cache_ba = None
            st.session_state.cache_diagram = None
            st.session_state.cache_da = None
            st.session_state.cache_qa = None
            st.session_state.pipeline_started = False
            st.session_state.refinement_round = 0
            st.rerun()
            
        if run_clicked:
            st.session_state.pipeline_started = True

        if st.session_state.pipeline_started:
            
            # PHASE 1: VISION
            if st.session_state.cache_vision is not None:
                vision_result = st.session_state.cache_vision
                st.success("⚡ PHASE 1 (Vision): Dữ liệu lấy thần tốc từ Cache State. Tiết kiệm ~1500 Tokens!")
                vision_time = 0
            else:
                with st.spinner(t("ba_vision_spin")):
                    start_total = time.time()
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(uploaded_image.getbuffer())
                            tmp_path = tmp.name
                        start_vision = time.time()
                        vision_result = st.session_state.vision_agent.analyze_wireframe(tmp_path, user_notes)
                        vision_time = time.time() - start_vision
                        st.session_state.cache_vision = vision_result # Gắng save
                    except Exception as e: st.error(f"{t('ba_vision_fail')}: {e}"); st.stop()
                    finally:
                        try: os.unlink(tmp_path)
                        except: pass
                st.success(t("ba_vision_ok", time=vision_time))
            with st.expander(t("ba_vision_detail"), expanded=False):
                st.write(f"{t('ba_page_predict')} `{vision_result.page_name}`")
                components_data = [el.model_dump() for el in vision_result.elements]
                st.table(components_data)
            
            vision_json_str = vision_result.model_dump_json(indent=2)
            
            # PHASE 2: RAG
            rag_context = ""
            if st.session_state.rag_ready:
                with st.spinner(t("ba_rag_spin")):
                    search_query = f"{vision_result.page_name} " + " ".join([el.type for el in vision_result.elements])
                    start_rag = time.time()
                    rag_results = st.session_state.vector_store.search(search_query, top_k=5)
                    rag_time = time.time() - start_rag
                    rag_context = "\n---\n".join(rag_results)
                st.success(t("ba_rag_ok", count=len(rag_results), time=rag_time*1000))
            else:
                st.info(t("ba_no_pdf"))
                
            # PHASE 3: BA
            if st.session_state.cache_ba is not None:
                ba_result = st.session_state.cache_ba
                st.success("⚡ PHASE 3 (BA Logic): SRS Document bốc thẳng từ Cache State rỗng thời gian chạy!")
            else:
                with st.spinner(t("ba_agent_spin")):
                    start_ba = time.time()
                    try:
                        ba_result = st.session_state.ba_agent.generate_requirements(
                            ui_analysis_json=vision_json_str,
                            business_rules_context=rag_context
                        )
                        ba_time = time.time() - start_ba
                        st.session_state.cache_ba = ba_result # Save game
                    except Exception as e: st.error(f"{t('ba_agent_fail')}: {e}"); st.stop()
                    
                st.success(t("ba_agent_ok", ba_time=ba_time, total_time=ba_time))
            
            # ====== BƯỚC 3: RENDER THE NEW SRS ====== #
            st.markdown("---")
            st.markdown(f"{t('ba_srs_title')} **{ba_result.system_name}** ({t('ba_srs_version')} {ba_result.version})")
            
            # 1. Missing Requirements
            if ba_result.missing_requirements and len(ba_result.missing_requirements) > 0:
                st.error(t("ba_missing_rules"))
                for mr in ba_result.missing_requirements:
                    st.write(f"- {mr}")
            
            # 2. Actors
            st.markdown(t("ba_actor_title"))
            actor_df = pd.DataFrame([a.model_dump() for a in ba_result.actors])
            st.table(actor_df)
            
            # 3. FR
            st.markdown(t("ba_fr_title"))
            for fr in ba_result.functional_requirements:
                with st.container(border=True):
                    st.markdown(f"**[{fr.id}] {fr.name}**")
                    cols = st.columns(3)
                    cols[0].write(f"**{t('ba_fr_actor')}:** {fr.actor}")
                    cols[1].write(f"**{t('ba_fr_priority')}:** {fr.priority}")
                    st.markdown(f"*{fr.description}*")
                    
                    st.write(f"**{t('ba_fr_pre')}:** " + "; ".join(fr.pre_conditions))
                    st.write(f"**{t('ba_fr_post')}:** " + "; ".join(fr.post_conditions))
                    
                    st.write(t("ba_fr_mainflow"))
                    for step in fr.main_flow:
                        st.write(f"  - {step}")
                        
                    if fr.alternative_flows:
                        st.write(t("ba_fr_altflow"))
                        for idx, alt in enumerate(fr.alternative_flows):
                            with st.expander(f"Alt {idx+1}: {alt.condition}"):
                                for s in alt.steps: st.write(f" - {s}")
                                
                    if fr.edge_cases:
                        st.write(t("ba_fr_edge"))
                        for ec in fr.edge_cases:
                            st.write(f"  - 🔴 {ec}")

            # 4. NFR
            st.markdown(t("ba_nfr_title"))
            if ba_result.non_functional_requirements:
                nfr_df = pd.DataFrame([n.model_dump() for n in ba_result.non_functional_requirements])
                st.table(nfr_df)
            else:
                st.write("None")
                
            # 5. BR
            st.markdown(t("ba_br_title"))
            if ba_result.business_rules:
                br_df = pd.DataFrame([b.model_dump() for b in ba_result.business_rules])
                st.table(br_df)
            else:
                st.write("None")
            
            # ====== BƯỚC 4: RENDER DIAGRAMS ====== #
            st.markdown("---")
            st.markdown(t("ba_diagram_title"))
            
            if st.session_state.cache_diagram is not None:
                diagram_result = st.session_state.cache_diagram
                st.success("⚡ PHASE 4 (UML): Trích xuất Code Mermaid siêu miết mà từ bộ lưu Cache State!")
            else:
                with st.spinner(t("ba_diagram_spin")):
                    start_diagram = time.time()
                    try:
                        srs_json_string = ba_result.model_dump_json(indent=2)
                        diagram_result = st.session_state.diagram_agent.generate_diagrams(srs_json_string)
                        diagram_time = time.time() - start_diagram
                        st.session_state.cache_diagram = diagram_result # Checkpoint
                        st.success(t("ba_diagram_ok", time=diagram_time))
                    except Exception as e:
                        st.error(f"{t('ba_diagram_fail')}: {e}")
                        st.stop()
                        
            try:
                st.markdown(t("ba_diagram_act"))
                render_mermaid(diagram_result.flowchart_diagram)
                st.expander("Show Flowchart Code").code(diagram_result.flowchart_diagram, language="mermaid")
                
                st.markdown(t("ba_diagram_seq"))
                render_mermaid(diagram_result.sequence_diagram)
                st.expander("Show Sequence Code").code(diagram_result.sequence_diagram, language="mermaid")
                
                st.info(f"{t('ba_diagram_explain')} {diagram_result.diagram_explanation}")
                
            except Exception as e:
                st.error(f"{t('ba_diagram_fail')}: {e}")
                    
            # ====== BƯỚC 5: DATA ARCHITECT (DB SCHEMA & ERD) ====== #
            st.markdown("---")
            st.markdown(t("ba_da_title"))
            
            if st.session_state.cache_da is not None:
                da_result = st.session_state.cache_da
                st.success("⚡ PHASE 5 (Database): ERD Layout render cấp tốc từ State Memory!")
            else:
                with st.spinner(t("ba_da_spin")):
                    start_da = time.time()
                    try:
                        srs_json_string = ba_result.model_dump_json(indent=2)
                        da_result = st.session_state.data_agent.design_database(srs_json_string)
                        da_time = time.time() - start_da
                        st.session_state.cache_da = da_result
                        st.success(t("ba_da_ok", time=da_time))
                    except Exception as e:
                        st.error(f"{t('ba_da_fail')}: {e}")
                        st.stop()
                        
            try:
                st.markdown(t("ba_da_erd"))
                render_mermaid(da_result.erd_mermaid)
                st.expander("Show ERD Code").code(da_result.erd_mermaid, language="mermaid")
                
                st.markdown(t("ba_da_relations"))
                for rel in da_result.relationships:
                    st.write(f"- {rel}")
                    
                st.markdown(t("ba_da_tables"))
                for table in da_result.tables:
                    with st.expander(f"🗃️ Bảng: `{table.name}` - {table.description}"):
                        # Đổi list pydantic column sang dataframe để render bảng metadata siêu đẹp
                        col_df = pd.DataFrame([c.model_dump() for c in table.columns])
                        st.dataframe(col_df, use_container_width=True)
                        
            except Exception as e:
                st.error(f"{t('ba_da_fail')}: {e}")
                    
            # ====== BƯỚC 6: QA AUDIT + AUTO-REFINEMENT LOOP ====== #
            MAX_REFINEMENT_ROUNDS = 2
            
            # Khởi tạo biến đếm vòng lặp
            if 'refinement_round' not in st.session_state:
                st.session_state.refinement_round = 0
                
            st.markdown("---")
            st.markdown(t("ba_qa_title"))
            
            if st.session_state.cache_qa is not None:
                qa_result = st.session_state.cache_qa
                st.success("⚡ PHASE 6 (QA Check): Án phản biện xuất ra nhẹ tựa lông hồng từ State Cache cũ!")
            else:
                with st.spinner(t("ba_qa_spin")):
                    start_qa = time.time()
                    try:
                        da_json_string = da_result.model_dump_json(indent=2)
                        srs_json_string = ba_result.model_dump_json(indent=2)
                        
                        qa_result = st.session_state.qa_agent.audit_system(
                            vision_json=vision_json_str,
                            srs_json=srs_json_string,
                            db_json=da_json_string
                        )
                        qa_time = time.time() - start_qa
                        st.success(t("ba_qa_ok", time=qa_time))
                    except Exception as e:
                        st.error(f"{t('ba_qa_fail')}: {e}")
                        st.stop()
            
            # --- Render kết quả QA hiện tại ---
            if qa_result.is_approved:
                st.success(t("ba_qa_approved"))
                if st.session_state.refinement_round > 0:
                    st.balloons()
                    st.success(t("ba_refine_final_ok", round=st.session_state.refinement_round))
            else:
                st.error(t("ba_qa_rejected"))
                    
            if qa_result.discrepancies:
                st.markdown("⚠️ **Chi tiết Lỗi (Discrepancies):**")
                disc_df = pd.DataFrame([d.model_dump() for d in qa_result.discrepancies])
                st.dataframe(disc_df, use_container_width=True)
                
            st.info(f"{t('ba_qa_feedback')} {qa_result.feedback_for_agents}")
            
            # --- AUTO-REFINEMENT LOOP ---
            if not qa_result.is_approved and st.session_state.refinement_round < MAX_REFINEMENT_ROUNDS:
                st.markdown("---")
                current_round = st.session_state.refinement_round + 1
                st.warning(t("ba_refine_start", round=current_round, version=current_round + 1))
                
                # BƯỚC 6A: BA Agent tự viết lại SRS
                with st.spinner(f"🧠 BA Agent đang tự phản biện và viết lại SRS V{current_round + 1}..."):
                    start_refine = time.time()
                    try:
                        qa_feedback_text = qa_result.feedback_for_agents
                        if qa_result.discrepancies:
                            qa_feedback_text += "\n\nCHI TIẾT LỖI:\n"
                            for d in qa_result.discrepancies:
                                qa_feedback_text += f"- [{d.severity}] {d.module_source}: {d.description}\n"
                        
                        ba_result = st.session_state.ba_agent.refine_requirements(
                            previous_srs_json=ba_result.model_dump_json(indent=2),
                            qa_feedback=qa_feedback_text,
                            ui_analysis_json=vision_json_str
                        )
                        refine_time = time.time() - start_refine
                        st.session_state.cache_ba = ba_result
                        st.success(t("ba_refine_ok", version=current_round + 1, time=refine_time))
                    except Exception as e:
                        st.error(f"BA Refinement thất bại: {e}")
                        st.stop()
                
                # BƯỚC 6B: Diagram Agent chạy lại
                with st.spinner(f"📊 Diagram Agent đang vẽ lại sơ đồ dựa trên SRS V{current_round + 1}..."):
                    try:
                        srs_json_string = ba_result.model_dump_json(indent=2)
                        diagram_result = st.session_state.diagram_agent.generate_diagrams(srs_json_string)
                        st.session_state.cache_diagram = diagram_result
                    except Exception as e:
                        st.error(f"Diagram Refinement thất bại: {e}")
                        st.stop()
                
                # BƯỚC 6C: Data Architect Agent chạy lại
                with st.spinner(f"🗄️ Data Architect đang thiết kế lại Database dựa trên SRS V{current_round + 1}..."):
                    try:
                        da_result = st.session_state.data_agent.design_database(srs_json_string)
                        st.session_state.cache_da = da_result
                    except Exception as e:
                        st.error(f"DA Refinement thất bại: {e}")
                        st.stop()
                
                # BƯỚC 6D: QA Agent chạy lại lần nữa
                with st.spinner(f"🕵️ QA Agent đang kiểm duyệt lại SRS V{current_round + 1}..."):
                    try:
                        da_json_string = da_result.model_dump_json(indent=2)
                        qa_result = st.session_state.qa_agent.audit_system(
                            vision_json=vision_json_str,
                            srs_json=srs_json_string,
                            db_json=da_json_string
                        )
                        st.session_state.cache_qa = qa_result
                    except Exception as e:
                        st.error(f"QA Re-audit thất bại: {e}")
                        st.stop()
                
                st.session_state.refinement_round = current_round
                
                # Render kết quả vòng lặp
                st.markdown("---")
                st.markdown(f"### 🔄 Kết quả QA Audit — Vòng {current_round}")
                
                if qa_result.is_approved:
                    st.balloons()
                    st.success(t("ba_refine_final_ok", round=current_round))
                else:
                    st.error(t("ba_qa_rejected"))
                    if qa_result.discrepancies:
                        st.markdown("⚠️ **Chi tiết Lỗi còn lại (Discrepancies):**")
                        disc_df2 = pd.DataFrame([d.model_dump() for d in qa_result.discrepancies])
                        st.dataframe(disc_df2, use_container_width=True)
                    st.info(f"{t('ba_qa_feedback')} {qa_result.feedback_for_agents}")
                    
                    if current_round >= MAX_REFINEMENT_ROUNDS:
                        st.warning(t("ba_refine_final_fail", max_rounds=MAX_REFINEMENT_ROUNDS))
            
            elif not qa_result.is_approved and st.session_state.refinement_round >= MAX_REFINEMENT_ROUNDS:
                st.warning(t("ba_refine_final_fail", max_rounds=MAX_REFINEMENT_ROUNDS))
            
            # ====== BƯỚC 7: HUMAN-IN-THE-LOOP (HITL) MẢNH GHÉP CUỐI CÙNG ====== #
            st.markdown("---")
            st.markdown("## 🧑‍💻 Mảnh Ghép Cuối Cùng: Quyết định của Ban Giám Đốc (Bạn)")
            
            if qa_result.is_approved:
                st.info("🤖 **Hệ thống AI báo cáo:** Thưa Sếp, tài liệu phân tích đã hoàn hảo và qua mặt bộ phận QA của chúng tôi! Mời Sếp xem xét vòng cuối.")
            else:
                st.warning("🤖 **Hệ thống AI báo cáo:** Thưa Sếp, các Tác tử nội bộ vẫn đang cãi nhau (Mâu thuẫn Logic). Chúng tôi cần góc nhìn của Con Người để giải quyết!")
                
            col_hitl_1, col_hitl_2 = st.columns(2)
            
            with col_hitl_1:
                if st.button("✅ TÔI (CON NGƯỜI) PHÊ DUYỆT BẢN NÀY", type="primary", use_container_width=True):
                    st.success("🎉 TUYỆT VỜI! Mọi tài liệu đã được chốt. Bản quyền thuộc về Trí Tuệ của Bạn & Trí Tuệ Nhân Tạo.")
                    st.balloons()
                    # Logic xuất file PDF / Word sẽ code ở đây ở tương lai
                    
            with col_hitl_2:
                with st.expander("❌ TÔI CHÊ! BẮT CẢ LŨ STAFF AI LÀM LẠI", expanded=False):
                    st.write("Bạn thấy hệ thống phân tích sót chức năng nào? Đừng ngại mắng, Tác tử BA sẽ ngoan ngoãn tự sửa lại toàn bộ tài liệu.")
                    human_feedback = st.text_area("✍️ Feedback (Ví dụ: Thêm luồng Momo, giỏ hàng...)", height=100)
                    if st.button("🚀 Ra Lệnh Làm Lại", type="primary"):
                        if human_feedback.strip() == "":
                            st.warning("Xin Sếp gõ vài chữ trước khi ra lệnh!")
                        else:
                            st.session_state.cache_qa = None
                            st.session_state.cache_da = None
                            st.session_state.cache_diagram = None
                            
                            with st.spinner("🧠 Staff AI đang nuốt từng chữ của Sếp để Đập đi xây lại SRS..."):
                                try:
                                    srs_json_string = ba_result.model_dump_json(indent=2)
                                    combined_feedback = f"### [LỆNH CHỈ ĐẠO ÉP BUỘC TỪ CON NGƯỜI (HUMAN BOSS)] ###\n{human_feedback}\n\n### [LỖI CŨ CÒN TỒN ĐỌNG CHƯA GIẢI QUYẾT TỪ QA YẾU KÉM] ###\n{qa_result.feedback_for_agents}"
                                    
                                    new_ba_result = st.session_state.ba_agent.refine_requirements(
                                        previous_srs_json=srs_json_string,
                                        qa_feedback=combined_feedback,
                                        ui_analysis_json=vision_json_str
                                    )
                                    st.session_state.cache_ba = new_ba_result
                                    # Reset biến loop để hệ thống chạy fresh 1 vòng mới 
                                    st.session_state.refinement_round = 0 
                                    st.rerun()  # Refresh stream, nhảy qua thẳng Bước 4
                                except Exception as e:
                                    st.error(f"Nhân viên AI biểu tình (Lỗi Server Call): {e}")

            with st.expander(t("ba_json_expand")):
                st.json(ba_result.model_dump())
    else:
        st.warning(t("ba_no_image"))

if __name__ == "__main__":
    main()

