# Báo Cáo Pha 1 — Baseline Data Pipeline & Observability

## 1. Nguồn Dữ Liệu & Ingestion
- **Nguồn:** Crossref REST API
- **Query:** `agentic retrieval augmented generation large language model`
- **Tổng số tài liệu ingest:** 24
- **Trạng thái Ingestion:** Hoàn thành, dữ liệu thô bảo toàn tại `data/raw/`

## 2. Kiểm Soát Chất Lượng Dữ Liệu (Great Expectations 1.x)
- **Quality Gate Success:** `PASS` (`True`)
- **Tổng số dòng đã làm sạch:** 24
- **Chi tiết kiểm định:**
  - `ExpectTableRowCountToBeBetween`: True
  - `ExpectColumnValuesToNotBeNull (paper_id, title)`: True
  - `ExpectColumnValuesToBeUnique (paper_id)`: True
  - `ExpectColumnValueLengthsToBeBetween (summary >= 20)`: True

## 3. Giám Sát Freshness SLA
- **Tuân thủ Freshness SLA:** `ĐẠT` (`is_fresh = True`)
- **Số bài báo quá hạn (> 180 ngày):** 1 / 24 (4.2%)
- **Khoảng thời gian bài báo:** `2026-03-28` đến `2026-07-22`

## 4. Hiệu Năng RAG Baseline
- **Retrieval Hit Rate:** `1.0000` (100.0%)
- **Mean Token F1 Score:** `1.0000` (100.0%)
- **Vector DB Collection:** `papers-baseline`
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
