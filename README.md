# 🚀 Antigravity Skills & Gemini 4 Web Integration Suite

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://www.python.org/)
[![Antigravity](https://img.shields.io/badge/Antigravity-IDE%20%7C%20App%20%7C%20CLI-purple.svg)](https://antigravity.google)
[![Gemini](https://img.shields.io/badge/Gemini%20Web-Gemini%204%20Argon-orange.svg)](https://gemini.google.com/app)

Bộ công cụ và thư viện kỹ năng toàn diện cho hệ sinh thái **Google Antigravity** (Antigravity IDE, Desktop App, và CLI `agy`). 

Hợp nhất trực tiếp sức mạnh mô hình **Google Gemini 4 High (Gemini 4 Argon kèm Extended Thinking)** từ tài khoản [Google Gemini Web](https://gemini.google.com/app) cùng hệ thống kỹ năng chuẩn hoá (**Agent Skills**) giúp giải phóng giới hạn quota, tự động hoá tác vụ lập trình phức tạp và thao tác tài liệu chuyên nghiệp.

---

## 🌟 Điểm Nổi Bật

- ⚡ **1-Click Tự Động Kết Nối & Cài Đặt**: Chạy `ket_noi_antigravity.bat` (Windows) hoặc `./ket_noi_antigravity.sh` (Linux/macOS) — Tự động cài đặt thư viện, quét cookie trình duyệt, cấu hình MCP Server và đăng ký toàn bộ Slash Commands & Skills vào Antigravity.
- 🧠 **Mô hình Gemini 4 High (Argon Extended Thinking)**: Luôn mặc định kích hoạt chế độ suy luận mở rộng cao nhất từ tài khoản Google Gemini Web, phân tích code và giải quyết bài toán hóc búa vượt trội.
- 💰 **Kiến Trúc Tiết Kiệm Quota Đỉnh Cao (`quota-workflow` v4.0)**:
  - Lập kế hoạch (Planning) bằng Gemini 4 High Web qua MCP: **Tiêu tốn 0% Antigravity Pro quota!**
  - Thực thi (Execution) từng bước an toàn bằng các Cheap Model Sub-agents (`Gemini 3.8 Flash`).
- 💬 **Hệ Thống Lệnh Slash Tức Thì**:
  - `/kg4 <câu hỏi>`: Tham vấn trực tiếp trí tuệ suy luận sâu của Gemini 4 Web trong bất kỳ khung chat nào.
  - `/qw <tác vụ>` hoặc `/quota-workflow <tác vụ>`: Tự động kích hoạt quy trình tác vụ lớn (>30 phút, ≥3 bước).
- 🍪 **Multi-Account Cookie Pool & Zero-Config Auto-Failover**: Tự động nhận diện cookie từ Microsoft Edge, Chrome, Firefox, Brave, Opera. Hỗ trợ xoay vòng nhiều tài khoản và tự động chuyển đổi khi gặp rate-limit.
- 📄 **Bộ Kỹ Năng Tài Liệu Văn Phòng Tiêu Chuẩn (Anthropic Apache 2.0)**: Tích hợp sẵn `docx`, `xlsx`, `pptx`, `pdf` tối ưu riêng cho Antigravity.
- 🔌 **Tích Hợp Kép (Dual Integration)**:
  - **Native MCP Server**: Cung cấp các công cụ `gemini_web_ask`, `gemini_web_chat`, `gemini_web_deep_research`, `gemini_web_account_info`.
  - **OpenAI-Compatible Proxy**: Hỗ trợ endpoint `/v1/chat/completions` (Streaming & Non-streaming) tại `http://127.0.0.1:8000/v1`.

---

## 📚 Danh Mục Kỹ Năng (Skills Catalog)

| Kỹ năng / Lệnh | Mô tả | Khi nào nên dùng |
| :--- | :--- | :--- |
| **[/kg4](skills/kg4/SKILL.md)** | Kích hoạt trực tiếp Gemini 4 High (Argon Extended Thinking) qua MCP `gemini-web` | Khi cần phân tích thuật toán khó, kiến trúc hệ thống hoặc cần câu trả lời từ Gemini 4 Web. |
| **[quota-workflow](quota-workflow/SKILL.md)** | Lập kế hoạch với Gemini 4 Web (0% Pro quota), điều phối thực thi bằng Flash sub-agents | Tác vụ lớn ước tính >30 phút hoặc có ≥3 bước phụ thuộc, cần bảo toàn quota Pro. |
| **[docx](.agents/skills/docx/SKILL.md)** | Tạo, đọc, chỉnh sửa và phân tích tài liệu Word (`.docx`, `.dotx`) | Bất kỳ tác vụ nào liên quan đến soạn thảo văn bản Word hoặc báo cáo văn phòng. |
| **[xlsx](.agents/skills/xlsx/SKILL.md)** | Tạo, đọc, sửa và tính toán bảng tính Excel (`.xlsx`, `.xlsm`, `.csv`) kèm công thức | Bất kỳ tác vụ xử lý bảng biểu, dữ liệu số liệu hoặc định dạng bảng tính. |
| **[pptx](.agents/skills/pptx/SKILL.md)** | Thiết kế, trích xuất và tùy biến bài thuyết trình Slide (`.pptx`, `.potx`) | Bất kỳ tác vụ nào tạo hoặc biên tập bài thuyết trình PowerPoint. |
| **[pdf](.agents/skills/pdf/SKILL.md)** | Đọc, trích xuất text/bảng, chia tách, ghép trang, xoay và điền biểu mẫu PDF | Mọi thao tác xử lý tập tin tài liệu định dạng PDF. |

---

## 🚀 Hướng Dẫn Cài Đặt Nhanh (1-Click Setup)

### Bước 1: Chuẩn bị trình duyệt
Mở trình duyệt bất kỳ (**Microsoft Edge**, **Chrome** hoặc **Firefox**) và đảm bảo bạn đã đăng nhập vào tài khoản [https://gemini.google.com/app](https://gemini.google.com/app).

### Bước 2: Tải repository về máy
```bash
git clone https://github.com/qsang2025/antigravity-skills.git
cd antigravity-skills
```

### Bước 3: Chạy cài đặt tự động 1-Click

#### 🪟 Trên Windows:
> **Click đúp (Double-click)** vào file:
> ```cmd
> ket_noi_antigravity.bat
> ```

#### 🍎 Trên macOS / 🐧 Linux:
Mở Terminal tại thư mục dự án và chạy:
```bash
chmod +x ket_noi_antigravity.sh
./ket_noi_antigravity.sh
```

#### 🐍 Hoặc chạy trực tiếp bằng Python (Mọi hệ điều hành):
```bash
python install.py
```

Bộ cài sẽ tự động:
1. Cài đặt các thư viện Python cần thiết (`gemini_webapi`, `mcp`, `python-dotenv`, v.v.).
2. Quét cookie đăng nhập Google Gemini từ trình duyệt và khởi tạo file `.env`.
3. Đăng ký MCP Server `gemini-web` vào `~/.gemini/config/mcp_config.json`.
4. Cài đặt toàn bộ Slash Commands (`/kg4`, `/qw`, `/quota-workflow`) vào `~/.gemini/config/global_workflows/`.
5. Đồng bộ toàn bộ Skills (`kg4`, `quota-workflow`, `docx`, `xlsx`, `pptx`, `pdf`) vào `~/.gemini/config/skills/`.
6. Kiểm tra kết nối thời gian thực đến Gemini 4 Argon Web.

---

## 🎯 Cách Sử Dụng Trong Antigravity

Sau khi chạy bộ cài xong, hãy mở **Antigravity IDE**, **Desktop App** hoặc **agy CLI**, tại khung chat bạn có thể sử dụng ngay:

### 1. Trò chuyện & Suy luận cùng Gemini 4 High:
```text
/kg4 <câu hỏi hoặc yêu cầu cần thực hiện>
```
*Ví dụ:*
- `/kg4 Viết cho tôi một module microservices bằng Python FastAPI kèm Dockerfile`
- `/kg4 Tối ưu hóa thuật toán sau đây giúp tôi`

### 2. Kích hoạt quy trình tác vụ lớn tiết kiệm Quota:
```text
/qw <mô tả nhiệm vụ lớn>
```
*Ví dụ:*
- `/qw Nâng cấp toàn bộ hệ thống xác thực từ JWT sang OAuth2 PKCE và viết unit tests`

---

## 🛠️ Bộ Công Cụ Dòng Lệnh (CLI Management)

Bộ công cụ `gemini2anti.py` cung cấp giao diện CLI quản trị mạnh mẽ:

| Lệnh CLI | Mô tả |
| :--- | :--- |
| `python gemini2anti.py check` | Kiểm tra trạng thái cookie, số credits còn lại và quota Gemini 4 |
| `python gemini2anti.py export-env` | Tự động xuất cookie trình duyệt ra file cấu hình `.env` |
| `python gemini2anti.py install-mcp` | Đăng ký lại MCP Server vào Antigravity |
| `python gemini2anti.py chat` | Trò chuyện trực tiếp với Gemini 4 trên Terminal |
| `python gemini2anti.py serve --port 8000` | Khởi chạy OpenAI-compatible API Proxy tại port 8000 |

---

## 📁 Cấu Trúc Thư Mục Repository

```text
antigravity-skills/
├── .agents/skills/              # Bộ kỹ năng Office Native (docx, xlsx, pptx, pdf)
├── skills/                      # Danh mục kỹ năng Agent Skills (kg4, ...)
│   └── kg4/
├── workflows/                   # Slash commands toàn cục (/kg4, /qw, /quota-workflow)
│   ├── kg4.md
│   ├── qw.md
│   └── quota-workflow.md
├── quota-workflow/              # Kỹ năng Quota Workflow v4.0 (Templates & Examples)
│   ├── SKILL.md
│   ├── WORKFLOW.md
│   ├── templates/
│   └── examples/
├── gemini2anti/                 # Lõi xử lý Python (Bridge, Cookie Pool, MCP, Proxy)
│   ├── client.py
│   ├── config.py
│   ├── mcp_server.py
│   └── proxy_server.py
├── tests/                       # Unit tests tự động
│   └── test_pool.py
├── install.py                   # Bộ cài đặt tự động 1-Click đa nền tảng
├── ket_noi_antigravity.bat      # Script 1-Click cho Windows
├── ket_noi_antigravity.sh       # Script 1-Click cho Linux/macOS
├── run_mcp.py                   # Điểm chạy Antigravity MCP Server
├── run_proxy.py                 # Điểm chạy OpenAI Proxy Server
├── gemini2anti.py               # CLI công cụ điều khiển
├── requirements.txt             # Danh sách dependencies
├── AGENTS.md                    # Quy tắc điều phối dành cho Antigravity AI Agents
└── LICENSE                      # MIT License
```

---

## 📄 Bản Quyền & Giấy Phép (License)

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
- Tác quyền tổng thể: Copyright (c) 2026 **Dương Nguyễn Quốc Sáng** & **NDKBVH**.
- Các kỹ năng xử lý tài liệu Office (`docx`, `xlsx`, `pptx`, `pdf`): Tham chiếu từ chuẩn của **Anthropic** (Apache 2.0).
