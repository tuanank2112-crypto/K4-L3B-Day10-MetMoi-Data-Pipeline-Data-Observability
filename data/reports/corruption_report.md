# Báo Cáo Đối Chiếu 3 Trạng Thái — Baseline vs Corrupted vs Repaired

> **Báo cáo phân tích hiện tượng Silent Failure và năng lực tự phục hồi (Self-Healing) của Data Pipeline.**

---

## 1. Bảng Đối Chiếu Định Lượng 3 Trạng Thái

| Tiêu chí / Metric | Baseline (Chuẩn) | Corrupted (Tiêm lỗi) | Repaired (Đã phục hồi) | Nhận xét & Đánh giá |
| :--- | :---: | :---: | :---: | :--- |
| **Tổng số tài liệu** | 24 | 23 | 24 | Mất bản ghi mới do drop, tăng do duplicate, phục hồi chuẩn 24 |
| **Data Quality Gate (GX 1.x)** | **PASS** (True) | **FAIL** (False) | **PASS** (True) | Chốt kiểm dịch phát hiện lỗi schema, duplicate và rỗng summary |
| **Freshness SLA** | **ĐẠT** (True) | **CẢNH BÁO** (False) | **ĐẠT** (True) | Vi phạm SLA khi tỷ lệ bài cũ vượt quá 25% |
| **Tỷ lệ bài quá hạn (>180d)** | < 25% | 47.8% | 4.2% | Cảnh báo thời gian thực về dữ liệu quá hạn |
| **Retrieval Hit Rate** | **1.0000** (100.0%) | **0.6000** (60.0%) | **1.0000** (100.0%) | Sụt giảm mạnh khi dữ liệu bị lỗi, khôi phục 100% sau repair |
| **Mean Token F1** | **1.0000** | **0.5000** | **1.0000** | Chất lượng câu trả lời phục hồi hoàn toàn sau sửa chữa |

---

## 2. Phân Tích Hiện Tượng Silent Failure

Khi dữ liệu đầu vào bị tiêm 6 kịch bản lỗi (Drop latest records, Blank summary, Noise injection, Truncate title, Stale date, Duplicate rows):
1. **Hệ thống không phát sinh ngoại lệ runtime (No crash):** Vector database vẫn nhận embedding và Agent vẫn trả lời câu hỏi của người dùng như bình thường.
2. **Tuy nhiên chất lượng suy thoái nghiêm trọng (Silent Degradation):**
   - Retrieval Hit Rate giảm từ **100.0%** xuống **60.0%**.
   - Các câu hỏi liên quan đến tài liệu mới hoặc tài liệu bị rỗng tóm tắt không thể truy vấn chính xác.
   - Nếu không có **Data Quality Gate (Great Expectations 1.x)** và **Freshness SLA**, lỗi dữ liệu này sẽ âm thầm lọt vào phục vụ người dùng cuối mà đội ngũ vận hành không hề hay biết.

---

## 3. Cơ Chế Tự Phục Hồi (Idempotent Repair)

1. **Bảo toàn Raw Snapshot:** Nhờ giữ nguyên dữ liệu gốc tại `data/raw/crossref_records.json`, hệ thống có thể hoàn nguyên bất kỳ lúc nào mà không cần phụ thuộc vào mạng ngoài.
2. **Tính Idempotent (Bảo toàn trạng thái):** Quá trình làm sạch, tính toán lại `age_days`, tạo `text_for_embedding` và đồng bộ hóa ChromaDB collection `papers-repaired` có thể chạy lặp lại nhiều lần mà luôn sinh ra cùng một kết quả chuẩn xác.
3. **Phục hồi hiệu năng:** Sau khi Repair, Data Quality Gate đạt **PASS**, Freshness SLA đạt **ĐẠT**, Retrieval Hit Rate và Mean Token F1 đạt lại phong độ đỉnh cao (**100.0%**).
