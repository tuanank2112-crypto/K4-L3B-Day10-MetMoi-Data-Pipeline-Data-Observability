# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `Metmoi`
- **Mã Nhóm / Lớp:** `H201`
- **Tên Repository Nộp Bài:** `K4-L3B-Day10-MetMoi-Data-Pipeline-Data-Observability`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | LeNhuY | 2A202602517 | tuanank2112@gmail.com | Solo Project Lead / Full Pipeline Owner (Ingestion, Cleaning, Vector DB, Observability, Repair) | `report/2A202602517_LeNhuY.md` |

---

## # Cá nhân

### ## LeNhuY - 2A202602517
- **Vai trò:** Solo Project Lead / Toàn bộ các mảng kỹ thuật (Full Pipeline Ownership).
- **Công việc chi tiết đã hoàn thành:**
  - **Module Pipeline & Core:** Thiết lập cấu hình hệ thống `core/config.py`, đường dẫn và utilities `core/utils.py`. Hoàn thiện luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - **Data Foundation & Recovery:** Xây dựng module thu thập Crossref API với cơ chế Fallback offline trong `src/ingestion/crossref.py`. Chuẩn hóa schema, tính toán trường `age_days` và `text_for_embedding` (cấu trúc 5 phần) trong `src/ingestion/cleaning.py`. Thực thi cơ chế Idempotent Repair phục hồi dữ liệu từ raw snapshot `data/raw/crossref_records.json`.
  - **RAG & Vector Database:** Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`. Nạp và quản lý 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - **Observability & Benchmark:** Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** và giám sát Freshness SLA trong `src/observability/quality.py`. Xây dựng bộ 10 câu hỏi benchmark đa dạng 4 nhóm nghiệp vụ trong `src/evaluation/testset.py`. Đo lường và xuất bảng đối chiếu 3 trạng thái vào `data/reports/corruption_report.md`.
  - **Bonus Extensions:** Xây dựng Interactive Observability Dashboard HTML (`src/observability/dashboard.py`), cơ chế Automated Self-Healing Gate (`src/observability/self_healing.py`), và bộ kiểm thử tự động Pytest CI (`tests/test_pipeline.py`).
- **Điều học được / Đóng góp chính:**
  - Nắm vững kiến trúc Data Pipeline hiện đại cho RAG Agent, cơ chế kiểm soát chất lượng dữ liệu với Great Expectations 1.x để chặn đứng Silent Failure, và thiết kế Idempotent Self-Healing Pipeline đảm bảo khả năng phục hồi dữ liệu tự động.
