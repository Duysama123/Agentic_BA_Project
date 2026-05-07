import streamlit as st
import os
import sys
import tempfile
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.rag_engine.chunker import extract_text_from_pdf, sliding_window_chunking
from src.rag_engine.vector_store import RAGVectorStore
from src.core.i18n import t, init_language_selector

def main():
    st.set_page_config(page_title=t("rag_page_title"), layout="wide")
    init_language_selector()
    
    st.title(t("rag_title"))
    st.write(t("rag_desc"))

    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = RAGVectorStore()
    if 'pdf_processed' not in st.session_state:
        st.session_state.pdf_processed = False

    col1, col2 = st.columns([1, 1])

    with col1:
        st.success(t("rag_load_title"))
        uploaded_file = st.file_uploader(t("rag_upload"), type=["pdf"])
        
        chunk_size = st.number_input(t("rag_chunk_size"), min_value=50, max_value=2000, value=300)
        overlap = st.number_input(t("rag_overlap"), min_value=10, max_value=500, value=50)

        if uploaded_file is not None and not st.session_state.pdf_processed:
            if st.button(t("rag_btn_process"), use_container_width=True):
                with st.spinner(t("rag_spinner")):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    
                    start_time = time.time()
                    try:
                        raw_text = extract_text_from_pdf(tmp_path)
                        chunks = sliding_window_chunking(raw_text, chunk_size=int(chunk_size), overlap=int(overlap))
                        st.write(t("rag_chunks_done", count=len(chunks)))
                        
                        st.session_state.vector_store.add_chunks(chunks)
                        
                        end_time = time.time()
                        st.success(t("rag_index_done", time=end_time - start_time))
                        st.session_state.pdf_processed = True
                        
                    except Exception as e:
                        st.error(f"{t('error_pdf')}: {e}")
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass

    with col2:
        st.info(t("rag_query_title"))
        if st.session_state.pdf_processed:
            st.write(t("rag_ready"))
            query = st.text_input(t("rag_query_input"))
            top_k = st.slider(t("rag_topk"), 1, 10, 3)
            
            if query:
                with st.spinner(t("rag_searching")):
                    start_search = time.time()
                    results = st.session_state.vector_store.search(query, top_k=top_k)
                    search_time = time.time() - start_search
                    
                    st.write(t("rag_search_time", time=search_time*1000))
                    st.markdown("---")
                    
                    for i, res in enumerate(results):
                        st.markdown(t("rag_result", i=i+1))
                        st.warning(res)
        else:
            st.warning(t("rag_no_pdf"))

if __name__ == "__main__":
    main()
