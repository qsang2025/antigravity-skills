# Hướng Dẫn Tích Hợp Model Gemini 4 Cho Antigravity

Dự án này tích hợp trực tiếp mô hình **Gemini 4 High (Gemini 4 Argon kèm Extended Thinking)** từ Google Gemini Web ([gemini.google.com/app](https://gemini.google.com/app)) vào Antigravity IDE và Antigravity CLI (`agy`).

## ⚠️ Nguyên Tắc Hoạt Động (Mandatory Rule)
1. **Phân biệt 2 tầng model:**
   - **Primary Model (Cửa sổ chat IDE):** Là model được chọn trên giao diện Antigravity (như Gemini 3.8 Flash, Claude Sonnet 4.6) - đóng vai trò điều phối tác vụ và gọi công cụ.
   - **Gemini 4 High Model (Web Engine):** Là mô hình chuyên gia thế hệ mới nhất từ tài khoản Google Gemini Web với suy luận sâu mở rộng (Extended Thinking), hoạt động qua MCP Server `gemini-web`.
2. **Tự động ủy quyền cho Gemini 4 High:**
   - Khi người dùng hỏi ý kiến, yêu cầu giải quyết bài toán phức tạp, hoặc muốn có phản hồi từ Gemini 4 / Gemini Web, Agent **BẮT BUỘC** gọi tool `gemini_web_ask(prompt=query, model="gemini-4", extended_thinking=True)` để lấy câu trả lời suy luận sâu từ Google Gemini Web trước khi trả lời người dùng.
3. **Lệnh Rút Gọn `/kg4` và `/g4` (Slash Command):**
   - Khi prompt người dùng bắt đầu bằng `/kg4`, `/g4`, `"""/kg4"""`, `"""/g4"""`, hoặc `kg4:`, `g4:` (ví dụ `/kg4 giải bài toán này...`), Agent **BẮT BUỘC** trích xuất toàn bộ câu hỏi đằng sau, lập tức gọi `gemini_web_ask(prompt=query, model="gemini-4", extended_thinking=True)` (Gemini 4 High) và trả về kết quả trực tiếp từ Gemini 4 mà không cần câu dẫn rườm rà (không cần giải thích việc chuyển tiếp).

## Các công cụ AI sẵn có:
- **MCP Server `gemini-web`**:
  - `gemini_web_ask(prompt)`: Hỏi đáp trực tiếp với **Gemini 4 High** (mặc định `model="gemini-4"`, `extended_thinking=True`).
  - `gemini_web_chat(message, session_id)`: Trò chuyện nhiều lượt có lưu trạng thái với **Gemini 4 High** (`extended_thinking=True`).
  - `gemini_web_deep_research(topic)`: Khởi chạy nghiên cứu chuyên sâu đa nguồn.
  - `gemini_web_account_info()`: Kiểm tra quota và tình trạng tài khoản.
- **OpenAI Proxy Server**: `http://127.0.0.1:8000/v1` (Model: `gemini-4`, mặc định bật Extended Thinking).

