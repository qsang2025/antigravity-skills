# Quy Tắc Điều Phối & Kỹ Năng Chuẩn Cho Antigravity (AGENTS.md)

Repo này là **Bộ công cụ & Thư viện Kỹ năng Chuẩn hoá** cho hệ sinh thái Google Antigravity.
Tất cả các Agent khi hoạt động trong không gian này hoặc sử dụng kỹ năng từ repo này **BẮT BUỘC TUÂN THỦ** các nguyên tắc sau:

---

## 1. Tích Hợp & Ủy Quyền Model Gemini 4 High (Gemini Web)

Repo này tích hợp trực tiếp mô hình **Gemini 4 High (Gemini 4 Argon kèm Extended Thinking)** từ Google Gemini Web ([gemini.google.com/app](https://gemini.google.com/app)) vào Antigravity IDE và Antigravity CLI (`agy`) thông qua MCP Server `gemini-web`.

### ⚠️ Nguyên Tắc Bắt Buộc:
1. **Phân biệt 2 tầng model:**
   - **Primary Model (Cửa sổ chat IDE):** Là model được chọn trên giao diện Antigravity (Gemini 3.8 Flash, Claude Sonnet 4.6, v.v.) — đóng vai trò điều phối tác vụ và gọi công cụ.
   - **Gemini 4 High Model (Web Engine):** Là mô hình chuyên gia từ Google Gemini Web với suy luận mở rộng (Extended Thinking), hoạt động qua MCP Server `gemini-web`.
2. **Tự động ủy quyền cho Gemini 4 High:**
   - Khi người dùng hỏi ý kiến, yêu cầu giải quyết bài toán phức tạp, hoặc muốn có phản hồi từ Gemini 4 / Gemini Web, Agent **BẮT BUỘC** gọi tool `gemini_web_ask(prompt=query, model="gemini-4", extended_thinking=True)` để lấy câu trả lời suy luận sâu từ Google Gemini Web trước khi trả lời.
3. **Lệnh Rút Gọn `/kg4` (Slash Command):**
   - Khi prompt người dùng bắt đầu bằng `/kg4`, `"""/kg4"""`, hoặc `kg4:` (ví dụ: `/kg4 giải bài toán này...`), Agent **BẮT BUỘC** trích xuất toàn bộ câu hỏi đằng sau, lập tức gọi `gemini_web_ask(prompt=query, model="gemini-4", extended_thinking=True)` và trả về kết quả trực tiếp từ Gemini 4 mà không cần lời dẫn giải rườm rà.

---

## 2. Quy Tắc Điều Phối Tác Vụ Lớn Tiết Kiệm Quota (`quota-workflow` v4.0)

Với các tác vụ lớn (ước tính **> 30 phút** hoặc có **≥ 3 bước phụ thuộc**), hoặc khi người dùng gõ `/qw` / `/quota-workflow`:

### ⚠️ Nguyên Tắc Phân Vai & Quản Lý Quota:
1. **Quy Hoạch Cấp Cao (Planning - Zero Pro Quota):**
   - **Mode 1 (Ưu tiên số 1):** Gọi MCP `gemini_web_ask(prompt=planning_prompt, model="gemini-4", extended_thinking=True)` để lập kế hoạch sâu bằng Gemini 4 Argon Web mà **tiêu tốn 0% Antigravity Pro quota**!
   - **Mode 2 (Fallback Pro):** Nếu MCP offline, dùng 1 turn model `pro` của Antigravity để viết plan.
   - **Mode 3 (Fallback Flash):** Nếu hết quota Pro, model Flash lập plan và gắn tag `[LOW-CONFIDENCE-PLAN - REQUIRES USER REVIEW]`.
2. **Review & Dispatch trong cùng 1 turn:**
   - Master viết file Plan `<repo>/.agents/plans/<date>-<task>.md` bằng 1 lần gọi `write_to_file`.
   - Dispatch ngay Sub-agent đầu tiên trong **cùng 1 turn** để tiết kiệm lượt tương tác.
3. **Thực thi tuần tự bằng Cheap Sub-agents:**
   - Mọi tác vụ đọc duyệt, viết mã, chạy test, sửa lỗi đều giao cho sub-agent tier `flash` thực hiện.
   - Bắt buộc tham số rõ ràng: `TypeName: "self"`, `Workspace: "inherit"`, `Model: "flash"`. Tuyệt đối không dùng `TypeName: "research"` cho bước khảo sát mạng/ghi file.
4. **Kỷ luật Git & File Persistence:**
   - Chỉ chạy **tuần tự 1 sub-agent ghi file tại một thời điểm** trên cùng repo để tránh xung đột `.git`.
   - Lưu tiến độ liên tục vào file Plan. Hết quota là dừng lại, lưu trạng thái và báo cáo — không retry vô tận.

---

## 3. Thư Viện Kỹ Năng Văn Phòng Chuẩn (Office Document Skills)

Khi người dùng yêu cầu thao tác tài liệu:
- **`.docx` / `.dotx`**: Sử dụng skill `docx` (`.agents/skills/docx/SKILL.md`).
- **`.xlsx` / `.xlsm` / `.csv`**: Sử dụng skill `xlsx` (`.agents/skills/xlsx/SKILL.md`).
- **`.pptx` / `.potx`**: Sử dụng skill `pptx` (`.agents/skills/pptx/SKILL.md`).
- **`.pdf`**: Sử dụng skill `pdf` (`.agents/skills/pdf/SKILL.md`).

---

## 4. Các Công Cụ Sẵn Có

- **MCP Server `gemini-web`**:
  - `gemini_web_ask(prompt)`: Hỏi đáp trực tiếp với Gemini 4 High (`model="gemini-4"`, `extended_thinking=True`).
  - `gemini_web_chat(message, session_id)`: Trò chuyện nhiều lượt có lưu trạng thái.
  - `gemini_web_deep_research(topic)`: Nghiên cứu chuyên sâu đa nguồn.
  - `gemini_web_account_info()`: Kiểm tra quota và tình trạng tài khoản.
- **OpenAI Proxy Server**: `http://127.0.0.1:8000/v1` (Model: `gemini-4`, mặc định bật Extended Thinking).
