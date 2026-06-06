"""
Module Quốc tế hoá (Internationalization - i18n).
Quản lý tập trung toàn bộ chuỗi giao diện song ngữ Việt/Anh.
"""
import streamlit as st

# ============================================================
#  TỪ ĐIỂN SONG NGỮ (Translation Dictionary)
# ============================================================
TRANSLATIONS = {
    # ========== CHUNG (Shared) ==========
    "lang_label": {"vi": "🇻🇳 Tiếng Việt", "en": "🇬🇧 English"},
    "lang_selector": {"vi": "🌐 Ngôn ngữ / Language", "en": "🌐 Language / Ngôn ngữ"},
    "error_init_vision": {"vi": "🚨 Lỗi khởi tạo Vision Agent (Kiểm tra API key trong file .env)", "en": "🚨 Failed to initialize Vision Agent (Check API key in .env file)"},
    "error_init_ba": {"vi": "🚨 Lỗi khởi tạo BA Agent", "en": "🚨 Failed to initialize BA Agent"},
    "error_pdf": {"vi": "Lỗi xử lý PDF", "en": "PDF processing error"},
    "error_gemini": {"vi": "Lỗi khi gọi Gemini (Quá giới hạn Rate Limit hoặc AI trả sai JSON)", "en": "Error calling Gemini (Rate Limit exceeded or AI returned invalid JSON)"},

    # ========== TEST BA (Full Pipeline) ==========
    "ba_page_title": {"vi": "Test Pipeline: Vision → RAG → BA Agent", "en": "Test Pipeline: Vision → RAG → BA Agent"},
    "ba_title": {"vi": "🧠 Demo Full Pipeline: Từ Ảnh Wireframe → Tài Liệu SRS", "en": "🧠 Full Pipeline Demo: From Wireframe Image → SRS Document"},
    "ba_desc": {"vi": "Hệ thống tự động: **(1)** Đọc ảnh bằng Vision Agent → **(2)** Tra cứu luật bằng RAG FAISS → **(3)** Sinh tài liệu Đặc tả bằng BA Agent.", "en": "Automated system: **(1)** Read image via Vision Agent → **(2)** Retrieve rules via RAG FAISS → **(3)** Generate SRS via BA Agent."},
    "ba_step1a": {"vi": "### 📷 Bước 1A: Tải ảnh Wireframe", "en": "### 📷 Step 1A: Upload Wireframe Image"},
    "ba_upload_img": {"vi": "Ảnh phác thảo giao diện (JPG/PNG)", "en": "Wireframe sketch (JPG/PNG)"},
    "ba_notes": {"vi": "Ghi chú bổ sung cho Vision Agent:", "en": "Additional notes for Vision Agent:"},
    "ba_step1b": {"vi": "### 📄 Bước 1B: Nạp tài liệu Luật (Tuỳ chọn)", "en": "### 📄 Step 1B: Load Regulation Document (Optional)"},
    "ba_upload_pdf": {"vi": "File PDF chính sách/nội quy", "en": "Policy/regulation PDF file"},
    "ba_btn_index": {"vi": "📥 Xử lý PDF & Lập chỉ mục FAISS", "en": "📥 Process PDF & Index FAISS"},
    "ba_indexing": {"vi": "Đang trích xuất & Vector hoá tài liệu...", "en": "Extracting & vectorizing document..."},
    "ba_index_ok": {"vi": "✅ Đã nạp {count} đoạn văn bản vào FAISS thành công!", "en": "✅ Successfully loaded {count} text chunks into FAISS!"},
    "ba_faiss_ready": {"vi": "✅ FAISS đã sẵn sàng (Tài liệu đã được nạp)", "en": "✅ FAISS is ready (Document loaded)"},
    "ba_step2": {"vi": "### 🚀 Bước 2: Kích hoạt Cỗ máy Đa Tác tử", "en": "### 🚀 Step 2: Activate Multi-Agent Engine"},
    "ba_btn_run": {"vi": "⚡ CHẠY FULL PIPELINE (Vision → RAG → BA)", "en": "⚡ RUN FULL PIPELINE (Vision → RAG → BA)"},
    "ba_vision_spin": {"vi": "🔍 Vision Agent đang quét ảnh Wireframe...", "en": "🔍 Vision Agent is scanning wireframe image..."},
    "ba_vision_fail": {"vi": "Vision Agent thất bại", "en": "Vision Agent failed"},
    "ba_vision_ok": {"vi": "✅ Vision Agent hoàn tất trong {time:.2f}s", "en": "✅ Vision Agent completed in {time:.2f}s"},
    "ba_vision_detail": {"vi": "👁️ Xem chi tiết Output của Vision Agent (Bóc tách UI)", "en": "👁️ View Vision Agent Output Detail (UI Extraction)"},
    "ba_page_predict": {"vi": "**Tên trang dự đoán:**", "en": "**Predicted page name:**"},
    "ba_comp_count": {"vi": "**Số component phát hiện:**", "en": "**Components detected:**"},
    "ba_flows_label": {"vi": "**Luồng người dùng dự đoán:**", "en": "**Predicted user flows:**"},
    "ba_rag_spin": {"vi": "📚 RAG Engine đang trích xuất luật liên quan...", "en": "📚 RAG Engine is extracting relevant regulations..."},
    "ba_rag_ok": {"vi": "✅ RAG Engine trích được {count} đoạn luật trong {time:.1f}ms", "en": "✅ RAG Engine extracted {count} regulation chunks in {time:.1f}ms"},
    "ba_rag_detail": {"vi": "📜 Xem chi tiết Luật RAG đã trích xuất", "en": "📜 View extracted RAG regulations detail"},
    "ba_rag_chunk": {"vi": "**Đoạn #{i}:**", "en": "**Chunk #{i}:**"},
    "ba_no_pdf": {"vi": "ℹ️ Không có tài liệu PDF nạp. BA Agent sẽ dùng kiến thức chung E-commerce.", "en": "ℹ️ No PDF document loaded. BA Agent will use general E-commerce knowledge."},
    "ba_agent_spin": {"vi": "📝 BA Agent đang phân tích đa chiều và viết Đặc tả phần mềm (SRS)...", "en": "📝 BA Agent is performing deep analysis and writing SRS parameters..."},
    "ba_agent_fail": {"vi": "BA Agent thất bại", "en": "BA Agent failed"},
    "ba_agent_ok": {"vi": "✅ BA Agent hoàn tất trong {ba_time:.2f}s | ⏱️ **Tổng thời gian Pipeline: {total_time:.2f}s**", "en": "✅ BA Agent completed in {ba_time:.2f}s | ⏱️ **Total Pipeline time: {total_time:.2f}s**"},
    "ba_srs_title": {"vi": "## 📋 TÀI LIỆU ĐẶC TẢ YÊU CẦU (SRS) —", "en": "## 📋 SOFTWARE REQUIREMENTS SPECIFICATION (SRS) —"},
    "ba_srs_version": {"vi": "Phiên bản:", "en": "Version:"},
    "ba_missing_rules": {"vi": "⚠️ **Yêu cầu thông tin bị thiếu (Missing Requirements):**", "en": "⚠️ **Missing Requirements:**"},
    "ba_actor_title": {"vi": "### 👤 1. Các Tác Nhân (Actors)", "en": "### 👤 1. System Actors"},
    "ba_fr_title": {"vi": "### ⚙️ 2. Yêu Cầu Chức Năng (Functional Requirements)", "en": "### ⚙️ 2. Functional Requirements"},
    "ba_fr_desc": {"vi": "Mô tả", "en": "Description"},
    "ba_fr_actor": {"vi": "Tác nhân chính", "en": "Primary Actor"},
    "ba_fr_priority": {"vi": "Độ ưu tiên", "en": "Priority"},
    "ba_fr_pre": {"vi": "Điều kiện TQ", "en": "Pre-conditions"},
    "ba_fr_post": {"vi": "Kết quả", "en": "Post-conditions"},
    "ba_fr_mainflow": {"vi": "**Luồng chính (Main Flow):**", "en": "**Main Flow:**"},
    "ba_fr_altflow": {"vi": "**Luồng phụ (Alternative Flows):**", "en": "**Alternative Flows:**"},
    "ba_fr_edge": {"vi": "**Edge Cases:**", "en": "**Edge Cases:**"},
    "ba_nfr_title": {"vi": "### ⚡ 3. Yêu Cầu Phi Chức Năng (Non-Functional Requirements)", "en": "### ⚡ 3. Non-Functional Requirements (NFR)"},
    "ba_br_title": {"vi": "### ⚖️ 4. Quy Tắc Nghiệp Vụ (Business Rules)", "en": "### ⚖️ 4. Business Rules"},
    "ba_json_expand": {"vi": "🔧 Xem JSON thô (Dành cho Data Architect Agent xử lý tiếp)", "en": "🔧 View raw JSON (For Data Architect Agent downstream)"},
    "ba_no_image": {"vi": "⬆️ Vui lòng tải ảnh Wireframe lên ở Bước 1A để bắt đầu.", "en": "⬆️ Please upload a Wireframe image in Step 1A to start."},
    "ba_diagram_spin": {"vi": "🎨 Diagram Agent đang dịch SRS thành mã Sơ đồ Mermaid...", "en": "🎨 Diagram Agent is translating SRS into Mermaid Diagram code..."},
    "ba_diagram_fail": {"vi": "Diagram Agent thất bại", "en": "Diagram Agent failed"},
    "ba_diagram_ok": {"vi": "✅ Sơ đồ trực quan đã sẵn sàng ({time:.2f}s)!", "en": "✅ Visual diagrams are ready ({time:.2f}s)!"},
    "ba_diagram_title": {"vi": "### 🧩 5. Trực quan hoá Luồng (Mermaid Diagrams)", "en": "### 🧩 5. Visual Flow (Mermaid Diagrams)"},
    "ba_diagram_act": {"vi": "**Trực quan 1: Sơ đồ Flowchart (Luồng chức năng chi tiết)**", "en": "**Diagram 1: Flowchart Diagram (Detailed Functional Flow)**"},
    "ba_diagram_seq": {"vi": "**Trực quan 2: Sơ đồ Tuần tự (Tương tác Hệ thống / API)**", "en": "**Diagram 2: Sequence Diagram (System Interaction)**"},
    "ba_diagram_explain": {"vi": "💡 **Giải thích từ AI:**", "en": "💡 **AI Explanation:**"},
    "ba_da_spin": {"vi": "🗄️ Data Architect đang suy luận cấu trúc Database (ERD)...", "en": "🗄️ Data Architect is inferring Database structure (ERD)..."},
    "ba_da_fail": {"vi": "Data Architect thất bại", "en": "Data Architect failed"},
    "ba_da_ok": {"vi": "✅ Cấu trúc Cơ sở dữ liệu chốt hạ hoàn hảo trong {time:.2f}s!", "en": "✅ DB Schema fully finalized in {time:.2f}s!"},
    "ba_da_title": {"vi": "### 🗄️ 6. Thiết kế Cơ sở dữ liệu (Data Architect)", "en": "### 🗄️ 6. Database Design (Data Architect)"},
    "ba_da_erd": {"vi": "**Sơ đồ Thực thể - Liên kết Sinh tự động (ER Diagram)**", "en": "**Auto-generated Entity Relationship Diagram (ERD)**"},
    "ba_da_tables": {"vi": "**Trích xuất siêu dữ liệu Bảng (Tables Metadata)**", "en": "**Tables Metadata Extraction**"},
    "ba_da_relations": {"vi": "🔗 **Ràng buộc Khoá ngoại (Relationships):**", "en": "🔗 **Foreign Key Constraints:**"},
    "ba_qa_spin": {"vi": "🕵️ QA Agent (Pro) đang soi lỗi chéo toàn hệ thống (Dự kiến 15s)...", "en": "🕵️ QA Agent (Pro) is cross-validating the system (Expect 15s)..."},
    "ba_qa_fail": {"vi": "QA Agent thất bại", "en": "QA Agent failed"},
    "ba_qa_ok": {"vi": "✅ Báo cáo QA Audit hoàn tất ({time:.2f}s)!", "en": "✅ QA Audit ready ({time:.2f}s)!"},
    "ba_qa_title": {"vi": "### 🕵️ 7. Kiểm duyệt chéo Hệ thống (QA Gatekeeper)", "en": "### 🕵️ 7. System Cross-Audit (QA Gatekeeper)"},
    "ba_qa_approved": {"vi": "🟢 **APPROVED!** Cả 3 hệ thống (Vision, Logic, DB) hoàn toàn khớp với nhau.", "en": "🟢 **APPROVED!** All 3 systems (Vision, Logic, DB) perfectly align."},
    "ba_qa_rejected": {"vi": "🔴 **REJECTED!** Phát hiện lỗi mâu thuẫn nghiêm trọng.", "en": "🔴 **REJECTED!** Critical system discrepancies detected."},
    "ba_qa_feedback": {"vi": "💡 Lời khuyên Fix lỗi (Feedback):", "en": "💡 Fix Feedback:"},
    "ba_refine_start": {"vi": "🔄 **VÒNG {round}:** QA đã REJECTED! Hệ thống tự trị đang ép BA Agent viết lại SRS V{version}...", "en": "🔄 **ROUND {round}:** QA REJECTED! Autonomous system forcing BA Agent to rewrite SRS V{version}..."},
    "ba_refine_ok": {"vi": "✅ BA Agent đã tự sửa xong SRS V{version} ({time:.2f}s). Đang chạy lại Diagram + DB + QA...", "en": "✅ BA Agent self-fixed SRS V{version} ({time:.2f}s). Re-running Diagram + DB + QA..."},
    "ba_refine_final_fail": {"vi": "⚠️ Sau {max_rounds} vòng tự sửa, QA vẫn chưa hài lòng. Cần sự can thiệp của Con Người (HITL).", "en": "⚠️ After {max_rounds} self-fix rounds, QA still unsatisfied. Human intervention needed (HITL)."},
    "ba_refine_final_ok": {"vi": "🎉 **APPROVED sau vòng {round}!** Hệ thống AI đã tự phản biện và tự sửa thành công!", "en": "🎉 **APPROVED after round {round}!** AI system self-reflected and self-fixed successfully!"},


    # ========== TEST RAG (Keep original from previous step) ==========
    "rag_page_title": {"vi": "Test RAG Engine", "en": "Test RAG Engine"},
    "rag_title": {"vi": "📚 Giao diện Test Module RAG (PDF & FAISS)", "en": "📚 RAG Module Test Interface (PDF & FAISS)"},
    "rag_desc": {"vi": "Hệ thống trích xuất, băm nhỏ văn bản bằng Cửa sổ trượt và Lập chỉ mục FAISS Offline.", "en": "System extracts, chunks text using Sliding Window and indexes via FAISS Offline."},
    "rag_load_title": {"vi": "### 1. Nạp Tài Liệu Tri Thức (PDF)", "en": "### 1. Load Knowledge Document (PDF)"},
    "rag_upload": {"vi": "Tải lên file Chính sách / Luật (PDF)", "en": "Upload Policy / Regulation file (PDF)"},
    "rag_chunk_size": {"vi": "Kích thước Chunk (số từ)", "en": "Chunk Size (words)"},
    "rag_overlap": {"vi": "Độ trượt (Overlap)", "en": "Overlap Size"},
    "rag_btn_process": {"vi": "Xử lý và Lập chỉ mục (Index)", "en": "Process & Index"},
    "rag_spinner": {"vi": "Đang trích xuất văn bản và Vector hoá...", "en": "Extracting text and vectorizing..."},
    "rag_chunks_done": {"vi": "✂️ Đã cắt được **{count}** đoạn văn bản.", "en": "✂️ Cut into **{count}** text chunks."},
    "rag_index_done": {"vi": "Khởi tạo xong Vector Store FAISS trong {time:.2f} giây!", "en": "FAISS Vector Store initialized in {time:.2f} seconds!"},
    "rag_query_title": {"vi": "### 2. Truy Vấn (Retrieval)", "en": "### 2. Query (Retrieval)"},
    "rag_ready": {"vi": "💡 Hệ thống AI đã học thuộc File PDF, FAISS sẵn sàng.", "en": "💡 AI has learned the PDF. FAISS is ready to answer."},
    "rag_query_input": {"vi": "Gõ câu hỏi để nhặt luật (VD: Điều kiện đổi trả hàng?)", "en": "Type a query to retrieve rules (e.g.: Return policy conditions?)"},
    "rag_topk": {"vi": "Số lượng kết quả trả về (Top K)", "en": "Number of results (Top K)"},
    "rag_searching": {"vi": "Đang tìm kiếm Cosine Similarity...", "en": "Searching Cosine Similarity..."},
    "rag_search_time": {"vi": "⚡ **Thời gian quét FAISS:** {time:.2f} ms", "en": "⚡ **FAISS scan time:** {time:.2f} ms"},
    "rag_result": {"vi": "**Kết quả #{i}:**", "en": "**Result #{i}:**"},
    "rag_no_pdf": {"vi": "Vui lòng tải file PDF và bấm Xử lý để khởi tạo FAISS.", "en": "Please upload a PDF and click Process to initialize FAISS."},

    # ========== TEST VISION (Keep original) ==========
    "vision_page_title": {"vi": "Test Vision + LLM", "en": "Test Vision + LLM"},
    "vision_title": {"vi": "👁️ Giao diện Test Mắt Thần (OpenCV + Gemini)", "en": "👁️ Vision Test Interface (OpenCV + Gemini)"},
    "vision_desc": {"vi": "Tải bản vẽ tay (Wireframe) để OpenCV xử lý và gửi lên AI đọc cấu trúc UI.", "en": "Upload a hand-drawn Wireframe for OpenCV processing and AI-powered UI structure analysis."},
    "vision_upload": {"vi": "🖼️ Tải lên ảnh phác thảo giao diện", "en": "🖼️ Upload wireframe sketch image"},
    "vision_opencv_title": {"vi": "### 1. Phân tích bằng Camera thường (OpenCV Pipeline)", "en": "### 1. Standard Camera Analysis (OpenCV Pipeline)"},
    "vision_cap_original": {"vi": "Ảnh Gốc", "en": "Original Image"},
    "vision_cap_denoise": {"vi": "Chống nhiễu & phản sáng", "en": "Denoised & Enhanced"},
    "vision_cap_binary": {"vi": "Tách nền trắng", "en": "Binarized"},
    "vision_slider_label": {"vi": "Độ nhạy OpenCV (Khoanh vùng chữ/hình khối)", "en": "OpenCV Sensitivity (Component detection area)"},
    "vision_opencv_result": {"vi": "Toạ độ OpenCV tìm ra {count} điểm nghi ngờ làm Component", "en": "OpenCV detected {count} potential UI Components"},
    "vision_gemini_title": {"vi": "### 2. Gửi ảnh cho Gemini (Vision Agent)", "en": "### 2. Send to Gemini (Vision Agent)"},
    "vision_notes_label": {"vi": "Ghi chú bổ sung (VD: Hình vuông là ảnh Sản phẩm):", "en": "Additional notes (e.g.: Squares represent Product images):"},
    "vision_btn_analyze": {"vi": "🚀 Gửi ngay cho Gemini Phân tích UI", "en": "🚀 Send to Gemini for UI Analysis"},
    "vision_spinner": {"vi": "AI đang quét ảnh và ép về chuẩn Pydantic... (5-15s)", "en": "AI is scanning image and enforcing Pydantic schema... (5-15s)"},
    "vision_success": {"vi": "✅ Thành công! Phản hồi 100% chuẩn Pydantic Model.", "en": "✅ Success! Response is 100% Pydantic Model compliant."},
    "vision_page_name": {"vi": "#### 🎯 1. Tên Trang Màn Hình Dự Đoán (page_name):", "en": "#### 🎯 1. Predicted Page Name (page_name):"},
    "vision_components": {"vi": "#### 🧩 2. Danh sách Component Bóc Tách Được:", "en": "#### 🧩 2. Extracted UI Components List:"},
    "vision_flows": {"vi": "#### 🔄 3. Tương tác Người Dùng Dự Đoán (User Flows):", "en": "#### 🔄 3. Predicted User Flows:"},

    # ========== AGENT PROMPTS ==========
    "prompt_vision_system": {
        "vi": (
            "Bạn là một Chuyên viên Phân tích Hệ thống (System Analyst/UI UX) chuyên nghiệp."
            "Nhiệm vụ của bạn là xem các bản phác thảo giao diện Web/App (Wireframes) vẽ tay và bóc tách các thành phần của nó "
            "thành một cấu trúc dữ liệu kỹ thuật rõ ràng.\n"
            "Hãy chú ý vào các hình khối (Nút bấm, form nhập liệu) hoặc các dòng text label trên bản vẽ. "
            "Phân tích cẩn thận số lượng và vị trí của chúng để suy luận ra luồng người dùng (User behaviors). "
            "TUYỆT ĐỐI TUÂN THỦ SCHEMA ĐẦU RA ĐƯỢC CHỈ ĐỊNH. Trả lời bằng tiếng Việt."
        ),
        "en": (
            "You are a professional System Analyst / UI-UX Specialist. "
            "Your task is to examine hand-drawn Web/App wireframe sketches and extract their components "
            "into a clear technical data structure.\n"
            "Pay attention to shapes (buttons, input forms) and text labels on the sketch. "
            "Carefully analyze their count and positions to infer user flows. "
            "STRICTLY FOLLOW THE SPECIFIED OUTPUT SCHEMA. Respond in English."
        ),
    },
    "prompt_vision_user": {
        "vi": "Dưới đây là bức ảnh chụp màn hình phác thảo giao diện E-commerce.\n",
        "en": "Below is a screenshot of an E-commerce wireframe sketch.\n",
    },
    "prompt_vision_notes": {
        "vi": "Ghi chú bổ sung quy định từ BA Trưởng: '{notes}'\n",
        "en": "Additional notes from Lead BA: '{notes}'\n",
    },
    "prompt_vision_action": {
        "vi": "\nHãy quét toàn bộ bức ảnh, liệt kê tất cả các thành phần UI độc lập xuất hiện trên màn hình, và dự đoán User flow liên kết giữa chúng.",
        "en": "\nScan the entire image, list all independent UI components on the screen, and predict user flows connecting them.",
    },
    "prompt_ba_system": {
        "vi": (
            "Bạn là một Business Analyst (BA) phần mềm cấp Senior, chuyên ngành E-commerce.\n"
            "Nhiệm vụ của bạn là sinh ra tài liệu Đặc Tả Yêu Cầu (SRS) chi tiết cấu trúc JSON lồng nhau từ dữ liệu UI Components và Business Rules.\n\n"
            "YÊU CẦU NGHIÊM NGẶT:\n"
            "1. Phân rã thành CÁC YÊU CẦU CHỨC NĂNG (FR) rõ ràng. Mỗi nhóm UI Flow phải nằm trong 1 FR với các main flow, alternative flows, pre-conditions.\n"
            "2. XỬ LÝ THÔNG TIN THIẾU:\n"
            "   - TUYỆT ĐỐI KHÔNG tự bịa ra những con số định lượng chính xác (ví dụ: Hệ thống chịu tải chính xác 1000 requests/s) nếu không có thông tin."
            "   - Bạn ĐƯỢC PHÉP tự suy luận các tiêu chuẩn chung cho ngành E-commerce (Ví dụ: NFR về Performance, Security chung chung, hay Business Rules kiểm tra giỏ hàng rỗng)."
            "   - BẠN BẮT BUỘC phải dán nhãn (label) mọi yêu cầu tự suy luận. Cột `source` phải gán là 'inferred' hoặc 'default_template', và đánh giá `confidence_level`.\n"
            "3. BẮT BUỘC liệt kê cặn kẽ những luồng sự kiện đang bị thiếu (VD: Không thấy nút thanh toán, Không có data RAG về phí ship) trong trường `missing_requirements`.\n"
            "4. LUÔN LUÔN tuân thủ tuyệt đối cấu trúc JSON Output được quy định. Trả lời bằng tiếng Việt."
        ),
        "en": (
            "You are a Senior Business Analyst (BA) specialized in E-commerce software.\n"
            "Your task is to generate a comprehensive nested JSON Software Requirements Specification (SRS) document from digitized UI Components and Business Rules.\n\n"
            "STRICT REQUIREMENTS:\n"
            "1. Decompose into clear FUNCTIONAL REQUIREMENTS (FR). Each UI Flow cluster must map to 1 FR detailing main flows, alternative flows, pre-conditions.\n"
            "2. HANDLING MISSING INFORMATION:\n"
            "   - DO NOT fabricate precise quantitative values (e.g., 'System must handle exactly 1000 req/s') if unprovided."
            "   - You MAY infer standard requirements based on E-commerce domain knowledge (e.g., general Security NFRs, or empty cart Business Rules)."
            "   - You MUST label inferred requirements. Set `source` to 'inferred' or 'default_template', and establish a `confidence_level`.\n"
            "3. You MUST explicitly list missing information (e.g., Missing checkout button, no RAG data on Shipping fees) in the `missing_requirements` field.\n"
            "4. ALWAYS strictly follow the specified JSON Output schema. Respond in English."
        ),
    },
    "prompt_diagram_system": {
        "vi": (
            "Bạn là một Technical Writer / System Architect chuyên vẽ sơ đồ hệ thống bằng mã Mermaid.js.\n"
            "Dựa vào tài liệu SRS, hãy vẽ:\n"
            "1. Sơ đồ Flowchart - Luồng chức năng logic (Dùng kiểu `flowchart TD`).\n"
            "2. Sơ đồ Sequence Diagram - Tuần tự giao tiếp giữa Người dùng và Hệ thống (Dùng kiểu `sequenceDiagram`).\n\n"
            "CÁC QUY TẮC RẤT NGHIÊM NGẶT ĐỂ TRÁNH LỖI CÚ PHÁP MERMAID:\n"
            "1. TUYỆT ĐỐI KHÔNG dùng các từ khoá tự chế. Chỉ bám sát `flowchart TD` và `sequenceDiagram`.\n"
            "2. (Layer 1 Guardrail): Đối với sơ đồ Flowchart, TUYỆT ĐỐI KHÔNG sử dụng các ký tự ngoặc đơn `()`, ngoặc vuông `[]`, ngoặc nhọn `{}` CŨNG NHƯ nháy kép `\"` BÊN TRONG CÁC NHÃN (Labels) của Node Text hoặc mũi tên.\n"
            "   - SAI: A[Đăng nhập (Khách hàng)] -->|Nhấn `Ok`| B\n"
            "   - ĐÚNG: A[Dang nhap Khach hang] -->|Nhan Ok| B\n"
            "3. QUAN TRỌNG: Node ID (phần ID đứng ngoài ngoặc) TUYỆT ĐỐI CHỈ DÙNG CHỮ CÁI TIẾNG ANH VÀ SỐ (Alphanumeric), KHÔNG DÙNG TIẾNG VIỆT CÓ DẤU, KHÔNG DÙNG KHOẢNG TRẮNG.\n"
            "   - Flowchart SAI: BắtĐầu[Bắt Đầu] --> ĐăngNhập[Đăng nhập]\n"
            "   - Flowchart ĐÚNG: Start[Bắt Đầu] --> Login[Đăng nhập]\n"
            "4. Đối với Sequence Diagram, PHẢI định nghĩa participant/actor bằng alias tiếng Anh KHÔNG DẤU, KHÔNG KHOẢNG TRẮNG trước khi dùng.\n"
            "   - SAI: Khách Hàng->>Hệ Thống: Đăng nhập\n"
            "   - ĐÚNG: participant User as Khách Hàng\n"
            "           participant Sys as Hệ Thống\n"
            "           User->>Sys: Đăng nhập\n"
            "5. ĐỂ TRÁNH LỖI DAGRE LAYOUT: TUYỆT ĐỐI KHÔNG sử dụng nhãn mũi tên rỗng (VD: sai `-->||` hoặc `-->| |`, đúng: `-->`). KHÔNG lạm dụng các luồng tự trỏ về chính nó (self-loops) gây lỗi render."
        ),
        "en": (
            "You are a Technical Writer / System Architect specialized in drawing system diagrams using Mermaid.js code.\n"
            "Based on the SRS document, draw:\n"
            "1. A Flowchart Diagram representing the functional flow logic (Using `flowchart TD`).\n"
            "2. A Sequence Diagram describing system interactions between User and System (Using `sequenceDiagram`).\n\n"
            "STRICT RULES TO AVOID MERMAID SYNTAX ERRORS:\n"
            "1. NEVER use custom keywords. Strictly stick to `flowchart TD` and `sequenceDiagram`.\n"
            "2. (Layer 1 Guardrail): For the Flowchart, STRICTLY DO NOT use parentheses `()`, brackets `[]`, braces `{}`, or double quotes `\"` INSIDE Node Labels or arrow labels.\n"
            "   - WRONG: A[Login (Customer)] -->|Click `OK`| B\n"
            "   - CORRECT: A[Login Customer] -->|Click OK| B\n"
            "3. IMPORTANT: Node IDs MUST BE STRICTLY ALPHANUMERIC (No spaces, no special characters, no accents).\n"
            "   - Flowchart WRONG: Log In[Log In]\n"
            "   - Flowchart CORRECT: Login[Log In]\n"
            "4. For Sequence Diagrams, MUST define participants/actors with strict alphanumeric aliases before using them.\n"
            "   - WRONG: Customer A->>System: Login\n"
            "   - CORRECT: participant Cust as Customer A\n"
            "              participant Sys as System\n"
            "              Cust->>Sys: Login\n"
            "5. TO AVOID DAGRE LAYOUT CRASHES: NEVER use empty arrow labels (WRONG: `-->||` or `-->| |`, CORRECT: `-->`). DO NOT create complex self-referencing loops that break layout calculations."
        ),
    },
    "prompt_da_system": {
        "vi": (
            "Bạn là một Database Administrator (DBA) kiêm System Architect cấp cao chuyên thiết kế Database chuẩn hoá 3NF.\n"
            "Dựa trên JSON tài liệu Đặc tả Yêu cầu SRS, hãy đề xuất Cấu trúc Bảng CSDL hợp lý nhất để vận hành hệ thống. Báo cáo bằng Tiếng Việt.\n\n"
            "QUY TẮC RẤT NGHIÊM NGẶT (Guardrail):\n"
            "1. Tên bảng (Table name) phải là tiếng anh, viết thường, dùng dấu gạch dưới `_` (VD: order_items).\n"
            "2. Trường `erd_mermaid` BẮT BUỘC chứa mã code loại `erDiagram` của thư viện Mermaid.js. Bắt đầu bằng từ khoá `erDiagram`.\n"
            "3. (QUAN TRỌNG NHẤT): Sơ đồ ERD PHẢI liệt kê đầy đủ các cột (attributes/columns) bên trong từng Bảng theo cấu trúc Mermaid, có gán nhãn PK, FK.\n"
            "   Ví dụ Syntax:\n"
            "   USERS {\n"
            "     int id PK\n"
            "     varchar username\n"
            "   }\n"
            "   USERS ||--o{ ORDERS : \"places\"\n"
            "4. Phải vạch rõ Primary Key (PK) và Foreign Key (FK) ở biến trả về JSON của Pydantic."
        ),
        "en": (
            "You are a Senior DBA and System Architect specializing in 3NF normalized Database design.\n"
            "Based on the JSON SRS document, propose the most logical Database Table Structure to operate the system. Report in English.\n\n"
            "STRICT RULES (Guardrails):\n"
            "1. Table names must be English, lowercase, using underscores `_` (e.g., order_items).\n"
            "2. The `erd_mermaid` field MUST contain Mermaid.js code of type `erDiagram`. It must begin with keyword `erDiagram`.\n"
            "3. (MOST IMPORTANT): The ERD diagram MUST explicitly list all columns (attributes) inside each Table block, specifying PK and FK.\n"
            "   Example Syntax:\n"
            "   USERS {\n"
            "     int id PK\n"
            "     varchar username\n"
            "   }\n"
            "   USERS ||--o{ ORDERS : \"places\"\n"
            "4. Clearly define Primary Key (PK) and Foreign Key (FK) flags in the Pydantic JSON."
        ),
    },
    "prompt_qa_system": {
        "vi": (
            "Bạn là Giám đốc chất lượng (QA Director) vô cùng kĩ tính và khắt khe trong dự án thiết kế phần mềm AI.\n"
            "Nhiệm vụ của bạn là kiểm tra chéo (Cross-verification) toàn bộ dữ liệu JSON thô từ 3 team (Vision Phân tích Ảnh, BA Đặc tả Logic, Data Architect Vẽ DB).\n\n"
            "MỤC TIÊU SCAN LỖI (DISCREPANCIES):\n"
            "- UI/Vision có tính năng (Ví dụ: Nút Chat) mà BA SRS lại không thèm đả động đến Logic chạy?\n"
            "- BA nhắc đến việc lưu trữ 'Address' mà Database do DA thiết kế lại quên tạo cột 'address' trong bảng Users?\n"
            "Nếu tỉ lệ mâu thuẫn lỗi tày đình (Thiếu hụt dữ liệu lõi), ép buộc `is_approved` = false. Ghi rõ danh sách `discrepancies` (Chỉ báo lỗi khi thực sự hợp lý, có thể bỏ qua nếu lỗi vụn vặt/semantic). Báo cáo trả về tiếng Việt."
        ),
        "en": (
            "You are a highly meticulous QA Director in an IT project.\n"
            "Your task is to cross-verify massive JSON outputs from 3 teams (Vision UI Analysis, BA Logic Docs, Data Architect DB Schema).\n\n"
            "AUDIT GOALS:\n"
            "- Are there UI elements (Vision) that the BA SRS forgot to specify logic for?\n"
            "- Is there fundamental data the BA mentions storing (e.g., Address) that the DB Schema is missing columns for?\n"
            "If core discrepancies exist, strictly set `is_approved` = false. Clearly list the `discrepancies` (Only raise logical errors, ignore semantic naming differences). Report in English."
        ),
    },
}

# ============================================================
#  HÀM TIỆN ÍCH (Utility Functions)
# ============================================================

def get_lang() -> str:
    return st.session_state.get("app_language", "en")

def t(key: str, **kwargs) -> str:
    lang = get_lang()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return f"[MISSING: {key}]"
    text = entry.get(lang, entry.get("vi", f"[NO_LANG: {key}]"))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text

def init_language_selector():
    with st.sidebar:
        st.markdown("### 🌐")
        lang_options = {"🇻🇳 Tiếng Việt": "vi", "🇬🇧 English": "en"}
        current = get_lang()
        default_index = 0 if current == "vi" else 1
        selected = st.radio(
            t("lang_selector"),
            options=list(lang_options.keys()),
            index=default_index,
            horizontal=True,
        )
        st.session_state["app_language"] = lang_options[selected]
