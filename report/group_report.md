# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | H201 (K4)                  |
| Tên nhóm         | Metmoi                     |
| Repository         | K4-L3B-Day10-MetMoi-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26                 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | LeNhuY | 2A202602517 | Solo Project Lead / Full Pipeline Owner | Toàn bộ pipeline (`core`, `ingestion`, `observability`, `retrieval`, `evaluation`, `pipelines`) |

## 2. Tóm tắt kết quả

Nhóm Metmoi (thực hiện solo bởi học viên LeNhuY) đã hoàn thành xuất sắc 100% các mục tiêu cốt lõi và các hạng mục điểm thưởng của bài lab:
1. **Baseline Pipeline:** Thiết lập luồng dữ liệu end-to-end từ Crossref REST API/Local snapshot, làm sạch chuẩn hóa khử trùng lặp 24 tài liệu, tạo trường `text_for_embedding` cấu trúc 5 phần, đánh chỉ mục ChromaDB với mô hình `all-MiniLM-L6-v2`, và đo lường độ chính xác trên bộ benchmark 10 câu hỏi.
2. **Data Observability:** Cấu hình Data Quality Gate theo chuẩn mới **Great Expectations 1.x** (Ephemeral Context với 4 expectations trọng yếu) và theo dõi Freshness SLA (cảnh báo khi tỷ lệ bài quá hạn >180 ngày vượt quá 25%).
3. **Data Corruption & Silent Failure:** Tiêm 6 kịch bản lỗi giả lập sự cố sản xuất (drop latest, blank summary, noise injection, truncate title, stale date, duplicate rows). Hệ thống chứng minh hiện tượng Silent Failure khi RAG vẫn chạy nhưng Hit Rate sụt giảm nghiêm trọng.
4. **Idempotent Self-Healing / Repair:** Kích hoạt cơ chế tự phục hồi từ nguồn raw lineage ban đầu, tái tạo hoàn toàn không gian vector, đưa Data Quality Gate từ `FAIL` về `PASS`, và khôi phục hiệu năng của Agent về mức tối đa.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref REST API (Fallback: data/raw/crossref_response.json)
    -> Raw Lineage Ingestion (data/raw/crossref_records.json)
    -> Cleaning & Data Modeling (Deduplication, age_days, 5-part text_for_embedding)
    -> Great Expectations 1.x Quality Gate & Freshness SLA Check
    -> Embedding (all-MiniLM-L6-v2) + ChromaDB Indexing (papers-baseline)
    -> Benchmark Evaluation (10 câu hỏi qua 4 nhóm nghiệp vụ)
    -> Synthetic Data Corruption (Tiêm 6 kịch bản lỗi & ghi log)
    -> Re-indexing & Re-evaluation (Đo lường Silent Failure)
    -> Idempotent Self-Healing Repair (Khôi phục từ raw snapshot)
    -> 3-State Comparative Report (Baseline vs Corrupted vs Repaired)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| ---- | ----- | ----------- | --------------- | ----- |
| `core/` | `.env`, config paths | Quản lý cấu hình, đường dẫn động, utilities | `Settings`, `Paths` | LeNhuY |
| `ingestion/` | Crossref API / Snapshot | Fetch, parse `PaperRecord`, clean, calculate `age_days` | `papers_clean.csv`, `papers_clean.json` | LeNhuY |
| `observability/` | Clean/Corrupted DataFrame | GX 1.x suite, Freshness SLA monitor | `quality_report.json`, `freshness_report.json` | LeNhuY |
| `retrieval/` | Cleaned DataFrame | Embed MiniLM, quản lý ChromaDB collections, QA routing | Chroma collections (`baseline`, `corrupted`, `repaired`) | LeNhuY |
| `evaluation/` | Cleaned DataFrame | Sinh 10 câu benchmark, chấm Hit Rate & Token F1 | `test_set.json`, `baseline_metrics.json` | LeNhuY |
| `pipelines/` | End-to-end modules | Điều phối Phase 1 & Corruption Flow | `phase1_report.md`, `corruption_report.md` | LeNhuY |

## 4. Bảng Đối Chiếu 3 Trạng Thái (Baseline vs Corrupted vs Repaired)

Bảng đối chiếu định lượng chi tiết sinh tự động từ thực thi pipeline:

| Tiêu chí / Metric | Baseline (Chuẩn) | Corrupted (Tiêm lỗi) | Repaired (Đã phục hồi) | Nhận xét & Đánh giá |
| :--- | :---: | :---: | :---: | :--- |
| **Tổng số tài liệu** | 24 | 23 | 24 | Mất do drop 20%, tăng do duplicate, phục hồi chuẩn 24 |
| **Data Quality Gate (GX 1.x)** | **PASS** (True) | **FAIL** (False) | **PASS** (True) | Chốt kiểm dịch phát hiện lỗi schema, duplicate và rỗng summary |
| **Freshness SLA** | **ĐẠT** (True) | **CẢNH BÁO** (False) | **ĐẠT** (True) | Vi phạm SLA khi tỷ lệ bài cũ (>180d) vượt quá 25% |
| **Tỷ lệ bài quá hạn (>180d)** | 4.2% | 47.8% | 4.2% | Cảnh báo thời gian thực về dữ liệu quá hạn |
| **Retrieval Hit Rate** | **1.0000** (100.0%) | **0.6000** (60.0%) | **1.0000** (100.0%) | Sụt giảm mạnh khi lỗi, khôi phục 100% sau repair |
| **Mean Token F1** | **1.0000** | **0.5000** | **1.0000** | Chất lượng câu trả lời phục hồi hoàn toàn sau sửa chữa |

Chi tiết tại: `data/reports/corruption_report.md`.

## 5. Hạng Mục Điểm Thưởng Vượt Chuẩn (Bonus +10 Điểm)

1. **B1: Interactive Observability Dashboard (`script/run_dashboard.py` & `src/observability/dashboard.py`):**
   - Sinh giao diện HTML trực quan tại `data/reports/observability_dashboard.html` hiển thị biểu đồ phân bố độ tuổi bài báo, KPI Data Quality và cảnh báo Drift thời gian thực.
2. **B2: Automated Self-Healing & Auto-Repair Pipeline (`script/run_self_healing_demo.py` & `src/observability/self_healing.py`):**
   - Cổng tự phục hồi tự động phát hiện vi phạm Great Expectations hoặc Freshness SLA, ngay lập tức kích hoạt luồng tái tạo từ raw lineage snapshot mà không cần can thiệp thủ công.
3. **B3: Automated Test Suite Pytest (`tests/test_pipeline.py`):**
   - 6 test cases bao phủ toàn diện: Parser, Clean DataFrame 5-part modeling, Data Quality Gate GX 1.x, Freshness SLA, Benchmark generation và Data Corruption impact. Đã pass 100%.

## 6. Kết Luận & Bài Học Kinh Nghiệm

1. **Tầm quan trọng của Data Observability:** Trong các hệ thống RAG hiện đại, dữ liệu bẩn là nguyên nhân hàng đầu dẫn đến ảo giác (hallucination) mà không gây crash hệ thống (Silent Failure). Việc thiết lập Great Expectations 1.x đóng vai trò như một chốt kiểm dịch bắt buộc trước khi nạp vào Vector Database.
2. **Thiết kế Idempotent:** Bảo toàn bản ghi thô (Raw Lineage) cho phép hệ thống tự phục hồi trạng thái một cách tin cậy và có thể lặp lại nhiều lần mà không phụ thuộc vào trạng thái lỗi trước đó.
