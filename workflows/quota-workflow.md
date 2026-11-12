---
name: quota-workflow
description: Kích hoạt quy trình Siêu Tiết Kiệm Quota v4.0. Tận dụng Gemini 4 Argon Web (Extended Thinking) qua MCP gemini-web lập kế hoạch (0% quota Pro) và điều phối subagents Flash thực thi tuần tự.
version: 4.0.0
---

# /quota-workflow - Quy Trình Siêu Tiết Kiệm Quota v4.0

$ARGUMENTS

---

## 🎯 Mục Đích
Kích hoạt toàn diện skill `quota-workflow v4.0` để giải quyết nhiệm vụ phức tạp mà **không tốn quota Pro của Antigravity**:
- Lập Plan kiến trúc sâu bằng **Gemini 4 Argon Web (Extended Thinking)** qua MCP `gemini-web` (Zero Pro Quota).
- Điều phối thực thi tuần tự bằng các **Subagents Flash (`Model: "flash"`)**.

---

## ⚡ Quy Tắc Thực Hiện Bắt Buộc (Mandatory Rules):
1. Đọc và tuân thủ skill `quota-workflow` (gọi `lookup_skill(skill_name: "quota-workflow")`).
2. Trích xuất nội dung nhiệm vụ từ `$ARGUMENTS`. Nếu `$ARGUMENTS` trống, hỏi lại người dùng mục tiêu cần thực hiện.
3. Chạy đúng quy trình 6 bước của v4.0:
   - **Bước 1 (Recon):** Điều động 1 subagent Recon (`Model: "flash"`, `TypeName: "self"`, `Workspace: "inherit"`) khảo sát repo, tạo `<date>-<task>-REQUEST.md` và `<task>-CONTEXT.md`.
   - **Bước 2 (Planning với Gemini 4 Web):** Đóng gói ngữ cảnh và gửi sang MCP `gemini_web_ask(prompt=..., model="gemini-4", extended_thinking=True)` để sinh Plan chi tiết.
   - **Bước 3 (Dual Gatekeeper Review):** Rà soát Checklist, lưu Plan vào `<repo>/.agents/plans/<date>-<task>.md` và dispatch subagent Flash đầu tiên trong cùng 1 turn.
   - **Bước 4 (Sequential Execution):** Điều phối các subagents Flash thực thi tuần tự từng cluster, commit progress sau mỗi bước.
   - **Bước 5 & 6 (Verify & Push):** Chạy kiểm thử, nghiệm thu và push lên Git.
