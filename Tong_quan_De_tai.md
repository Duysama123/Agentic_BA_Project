# Đề tài: Nghiên cứu xây dựng Hệ thống Đa tác tử tích hợp Trí tuệ nhân tạo Thị giác với cơ chế Con người trong vòng lặp (Human-in-the-loop) nhằm tự động hóa phân tích nghiệp vụ : Ứng dụng trong lĩnh vực Thương mại điện tử

## 1. Bối cảnh & Vấn đề
Trong quy trình phát triển phần mềm, bước Phân tích Yêu cầu (Requirement Analysis) tốn rất nhiều thời gian, đặc biệt là việc "dịch" các bản phác thảo giao diện vẽ tay (Wireframes) thành tài liệu đặc tả (SRS) và thiết kế cơ sở dữ liệu (Database Schema). Đối với lĩnh vực Thương mại điện tử (E-commerce), nghiệp vụ thường chứa nhiều rẽ nhánh phức tạp (Thanh toán, Vận chuyển, Khuyến mãi). 

Việc phân tích thủ công dễ dẫn đến:
* **Bỏ sót các luồng ngoại lệ (Edge cases)** quan trọng như: Lỗi cổng thanh toán, hết hàng trong kho, mã giảm giá hết hạn.
* **Tài liệu nghiệp vụ không đồng nhất** với các tiêu chuẩn bảo mật và chính sách vận hành nội bộ của công ty.

## 2. Mục tiêu nghiên cứu
Thiết kế và xây dựng nền tảng Backend độc lập ứng dụng **Agentic AI** và **Vision AI** để tự động hóa việc khởi tạo tài liệu nghiệp vụ E-commerce từ hình ảnh phác thảo. Kết hợp với công nghệ **RAG (Retrieval-Augmented Generation)** để đảm bảo tài liệu sinh ra tuân thủ đúng chính sách kinh doanh và quy chuẩn tích hợp của doanh nghiệp.

## 3. Phạm vi nghiên cứu (Scope)
* **Domain ứng dụng:** Thương mại điện tử (Tập trung vào phân hệ Giỏ hàng - Cart, Thanh toán - Checkout, và Khuyến mãi - Promotions).
* **Dữ liệu đầu vào (Input):** Hình ảnh vẽ tay sơ đồ quy trình hoặc giao diện ứng dụng (Wireframes) của các tính năng E-commerce.
* **Cơ sở Tri thức (RAG Data):** Các file PDF chứa "Chính sách Đổi trả", "Quy chuẩn tích hợp Thanh toán (VNPay/MoMo)", "Luật Bảo vệ Người tiêu dùng" và các policy nội bộ của doanh nghiệp.

## 4. Kiến trúc Hệ thống Đa tác tử (Agentic Architecture & HITL)
Hệ thống mô phỏng một đội ngũ phát triển phần mềm Agile thông qua **Mô hình Máy trạng thái hữu hạn (FSM)** với cơ chế **Vòng lặp phản hồi (Feedback Loop)**, **Ràng buộc dữ liệu nghiêm ngặt** bằng Pydantic và đặc biệt là sự tham gia của **Con người trong vòng lặp (Human-in-the-loop)**:

1. **Vision Agent (Chuyên viên Phân tích Hệ thống):** Nhận ảnh chụp Wireframe/Flowchart. Kết hợp OpenCV xử lý ảnh và Vision AI để bóc tách các thành phần UI, luồng tương tác và chuyển hóa thành cấu trúc dữ liệu JSON (Textual UI Tree).
2. **BA Agent (Chuyên viên Phân tích Nghiệp vụ):** Nhận output đã chuẩn hóa từ Vision Agent và yêu cầu thô của người dùng. Tích hợp RAG (truy xuất luật/chính sách) để tổng hợp, chuẩn hóa và đưa ra file Đặc tả SRS.
3. **Diagram Agent (Chuyên viên Viết Sơ đồ / Technical Writer):** Trích xuất dữ liệu rẽ nhánh từ báo cáo SRS của BA để động hóa khởi tạo mã Mermaid.js, sinh các sơ đồ Use Case và Activity Flowchart trực quan trực tiếp trên nền tảng Web.
4. **Data Architect Agent (Chuyên viên Dữ liệu):** Trích xuất thông tin nghiệp vụ từ các Agent phía trên để phân tích và đề xuất mô hình Thực thể - Liên kết (ERD), sinh ra mã SQL/cấu trúc Bảng.
5. **QA Agent (Chuyên viên Kiểm thử & Phản biện):** Đóng vai trò chốt chặn (Self-reflection). Rà soát chéo kết quả các luồng. Yêu cầu sinh lại (Regeneration / Retry loop) nếu phát hiện lỗi hoặc không đồng nhất.
6. **Human-in-the-loop (Người duyệt / Product Owner):** Đóng vai trò quyết định cuối cùng và Review kết quả, can thiệp ở các ngã rẽ phức tạp.

## 5. Công nghệ Triển khai Lõi (Tập trung "Tự code từ đầu")
Để tối ưu hóa hàm lượng học thuật và chứng minh năng lực kỹ sư hệ thống:

* **Nền tảng LLM:** Sử dụng API Gemini 1.5 Pro / GPT-4o (Đảm nhiệm tư duy logic).
* **Agent Orchestration (Tự xây dựng hoàn toàn):**
    * Không dùng LangGraph/CrewAI. Tự lập trình bộ điều khiển State Machine (FSM) bằng Python để quản lý state và luồng hội thoại giữa các Agents.
    * Sử dụng `Pydantic` để ép kiểu dữ liệu output giữa các Agent, chấm dứt việc truyền chuỗi text lộn xộn.
* **RAG Pipeline (Tự xây dựng hoàn toàn):**
    * Tự lập trình xử lý file PDF, thuật toán chia nhỏ dữ liệu (Sliding-window Chunking).
    * Sử dụng model Open-source (`all-MiniLM-L6-v2`) để tạo Vector Embeddings.
    * Áp dụng thư viện **FAISS** để tối ưu hóa việc tìm kiếm Cosine Similarity trên bộ nhớ (RAM).
* **Vision Pre-processing:** Dùng **OpenCV** để nhị phân hóa (binarize), tìm viền (contour) và cắt nhỏ các khu vực UI trước khi đưa vào Vision LLM, giúp giảm thiểu ảo giác (hallucination).
* **Human-in-the-loop Interface:** Thiết kế module UI tương tác cho phép con người (Human) Review, Edit (can thiệp text), Override (ghi đè quyết định của Agent) hoặc Approve/Reject kết quả theo từng State.
* **API & Frontend:** FastAPI (Backend Services) và Streamlit (Giao diện Web tương tác).

## 6. Nền tảng Dữ liệu & Đánh giá (Evaluation)
* **Dữ liệu Tri thức (RAG Data):** Các tài liệu quy chuẩn (PDF, Docx) về thương mại điện tử, cổng thanh toán.
* **Dữ liệu Đầu vào (Input):** 10-15 tình huống wireframes (Vẽ tay tự chụp hoặc thu thập từ Dribbble/Pinterest).
* **Baseline (Dữ liệu đối chiếu):** Các bộ tài liệu SRS, Use-case chuẩn từ các đồ án xuất sắc các khóa trước hoặc open-source GitHub.
* **Phương pháp Đánh giá (Evaluation Metrics):**
    * *Độ bao phủ (Coverage):* Tỉ lệ % các Edge cases hệ thống tìm ra so với Baseline.
    * *Thời gian xử lý (Processing Time KPI):* Đo đạc hiệu năng tự động hóa so với làm thủ công.
    * Tích hợp Dashboard nhỏ trên Streamlit để vẽ biểu đồ (`Matplotlib`/`Plotly`) kết quả đánh giá.

---

## 7. Cấu trúc Thư mục Code (Directory Structure Định hướng)

Dưới đây là cấu trúc thư mục dạng Monorepo chuẩn Software Engineering cho dự án:

```text
agentic_ecommerce_ba/
│
├── data/                       # Chứa dữ liệu đầu vào và cơ sở tri thức
│   ├── raw_wireframes/         # Ảnh chụp wireframes (Input)
│   ├── knowledge_base/         # Các file PDF chứng sách, luật cho RAG
│   └── baselines/              # Tài liệu SRS mẫu để đối chiếu
│
├── src/                        # Chứa toàn bộ mã nguồn của hệ thống
│   ├── core/                   # Các logic cốt lõi dùng chung
│   │   ├── config.py           # Thiết lập biến môi trường (API Keys, Paths...)
│   │   ├── exceptions.py       # Custom Error/Exception Handling
│   │   └── logger.py           # Cấu hình logging hệ thống
│   │
│   ├── schemas/                # Khai báo Strict Data Contracts bằng Pydantic
│   │   ├── ui_schema.py        # Model cho Output của Vision Agent
│   │   ├── story_schema.py     # Model cho User Stories (BA Agent)
│   │   └── db_schema.py        # Model cho Database Tables (Data Architect)
│   │
│   ├── agents/                 # Nơi định nghĩa các Tác tử (Agents)
│   │   ├── base_agent.py       # Class cha chứa các hàm gọi LLM cơ bản
│   │   ├── vision_agent.py     # Logic cho Vision Agent
│   │   ├── ba_agent.py         # Logic cho BA Agent
│   │   ├── data_agent.py       # Logic cho Data Architect Agent
│   │   └── qa_agent.py         # Logic rà soát và phản biện của QA Agent
│   │
│   ├── orchestrator/           # Trái tim điều phối hệ thống (FSM)
│   │   ├── fsm.py              # Định nghĩa State Machine (State, Transition)
│   │   └── workflow_runner.py  # Vòng lặp chính, xử lý Feedback loop và Retry
│   │
│   ├── rag_engine/             # Toàn bộ luồng RAG tự code
│   │   ├── chunker.py          # Thuật toán cắt văn bản
│   │   ├── embedder.py         # Chạy model Local (MiniLM) để lấy Vector
│   │   └── vector_store.py     # Tích hợp FAISS để lưu trữ và search
│   │
│   ├── vision_utils/           # Tiền xử lý ảnh với OpenCV
│   │   ├── image_cropper.py    # Thuật toán tách các khối UI
│   │   └── enhancer.py         # Tăng cường độ nét ảnh vẽ tay
│   │
│   ├── evaluation/             # Mã nguồn dùng để đánh giá hệ thống
│   │   ├── metrics.py          # Hàm tính toán Coverage, Time...
│   │   └── plots.py            # Hàm vẽ biểu đồ với Plotly/Matplotlib
│   │
│   ├── api/                    # (Tùy chọn) Nếu muốn bọc hệ thống qua REST API
│   │   └── main.py             # Khởi tạo FastAPI application
│   │
│   └── app.py                  # Streamlit App - Giao diện chính của hệ thống
│
├── tests/                      # Unit tests cho các modules
│   ├── test_fsm.py
│   ├── test_rag.py
│   └── test_agents.py
│
├── requirements.txt            # Danh sách thư viện cần thiết (OpenCV, FAISS, Pydantic, streamlit...)
├── .env.example                # File mẫu chứa cấu hình môi trường
├── README.md                   # Hướng dẫn setup và sử dụng hệ thống
└── Tong_quan_De_tai.md         # File thuyết minh/tổng quan đồ án
```
