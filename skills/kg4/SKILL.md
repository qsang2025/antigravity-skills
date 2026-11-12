---
name: kg4
description: Kích hoạt trực tiếp mô hình Google Gemini 4 High (Gemini 4 Argon kèm Extended Thinking) từ Google Gemini Web qua MCP gemini-web. Tự động kích hoạt khi người dùng gõ /kg4 [câu hỏi], kg4 [câu hỏi], hoặc muốn Gemini 4 trực tiếp giải quyết vấn đề với tư duy suy luận sâu nhất.
---

# Lệnh /kg4 — Kích Hoạt Nhanh Mô Hình Google Gemini 4 High (Argon)

Kỹ năng này cho phép Antigravity tự động kết nối và ủy quyền cho **Google Gemini 4 High (Gemini 4 Argon kèm Extended Thinking)** từ Google Gemini Web khi người dùng gõ lệnh rút gọn `/kg4`.

## ⚡ Nguyên Tắc Xử Lý Bắt Buộc (Mandatory Rules)

1. **Trích xuất nội dung (Query Extraction):**
   - Lấy toàn bộ phần nội dung đứng sau tiền tố `/kg4`, `"""/kg4"""`, hoặc `kg4:`.
   - Ví dụ: `/kg4 viết script python crawl dữ liệu` ➔ Nội dung gửi đi: `viết script python crawl dữ liệu`.
   - Nếu người dùng chỉ gõ `/kg4` mà không có nội dung đi kèm: Hãy hỏi nhanh: *"Bạn muốn Gemini 4 giải quyết bài toán hay phân tích nội dung gì?"*.

2. **Gọi Tool MCP Trực Tiếp:**
   - Agent **BẮT BUỘC** gọi tool `gemini_web_ask` (Server: `gemini-web`):
     - `prompt`: Nội dung câu hỏi của người dùng.
     - `model`: `"gemini-4"` (đảm bảo gọi đúng Gemini 4 Argon).
     - `extended_thinking`: `True` (luôn kích hoạt chế độ **Gemini 4 High** suy luận sâu cao nhất).

3. **Phong cách phản hồi (Direct Response):**
   - Trả lời trực tiếp và đầy đủ nội dung nhận được từ Gemini 4 High.
   - Tuyệt đối KHÔNG cần phải thêm các câu rào đón dài dòng (như *"Tôi đã chuyển câu hỏi đến Gemini Web..."*, *"Dưới đây là câu trả lời của Gemini 4..."*), trừ khi người dùng yêu cầu đối chiếu so sánh.
