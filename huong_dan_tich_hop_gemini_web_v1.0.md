# HƯỚNG DẪN TÍCH HỢP MODEL AI TỪ GOOGLE GEMINI WEB VÀO ANTIGRAVITY & AGY CLI

> **Phiên bản:** 1.0  
> **Dự án:** `gemini2anti`  
> **Mục tiêu:** Cung cấp cầu nối 2 chiều đưa toàn bộ sức mạnh của các model AI từ tài khoản Google Gemini Web ([gemini.google.com/app](https://gemini.google.com/app)) vào sử dụng trực tiếp trong Antigravity IDE và Antigravity CLI (`agy`).

---

## 1. TỔNG QUAN GIẢI PHÁP

Google Gemini Web (`gemini.google.com/app`) là nơi người dùng sở hữu tài khoản Google có quyền truy cập vào các mô hình AI tiên tiến (Gemini Advanced, Gemini Pro, Gemini Flash, Gemini Thinking) với hạn ngạch sử dụng lớn mà không cần trả phí theo từng token API như Google AI Studio hay Google Cloud Vertex AI.

Bộ công cụ **`gemini2anti`** thiết lập cầu nối hoàn chỉnh thông qua 2 cơ chế chính:

```
+-------------------------------------------------------------------------+
|                  Google Gemini Web (gemini.google.com/app)              |
|        (Xác thực qua Session Cookies: __Secure-1PSID, __Secure-1PSIDTS) |
+-------------------------------------------------------------------------+
                                   ▲
                                   │ (HTTP/2 Batchexecute RPC Engine)
                                   ▼
+-------------------------------------------------------------------------+
|                          Lõi gemini2anti Core                           |
|       - Quản lý phiên làm việc, tự động trích xuất cookie trình duyệt    |
|       - Auto-refresh token, cơ chế tự động thử lại khi mất kết nối      |
+-------------------------------------------------------------------------+
                  ▲                                       ▲
                  │ (FastMCP stdio)                       │ (HTTP REST API)
                  ▼                                       ▼
+------------------------------------+ +-----------------------------------+
|     Antigravity MCP Server         | |    OpenAI-Compatible Proxy Server |
|  - Gắn trực tiếp vào Antigravity   | |  - http://127.0.0.1:8000/v1       |
|    IDE và Antigravity CLI (agy)    | |  - Tương thích OpenAI SDK,        |
|  - Các tool: gemini_web_ask,       | |    Continue, Cursor, LangChain,   |
|    gemini_web_chat, deep_research  | |    Aider, v.v.                    |
+------------------------------------+ +-----------------------------------+
```

---

## 2. TÍNH NĂNG NỔI BẬT

1. **Tự động bóc tách Cookie thông minh (Zero-Config):**
   - Tự động nhận diện và trích xuất cookie đăng nhập từ trình duyệt Microsoft Edge, Google Chrome, Firefox hoặc Brave.
   - Không yêu cầu người dùng phải mở DevTools copy cookie thủ công trừ khi muốn cấu hình tĩnh.

2. **Tích hợp bản địa với Antigravity & agy CLI qua MCP (Model Context Protocol):**
   - Đăng ký 1 lệnh duy nhất: `gemini2anti install-mcp`.
   - Cung cấp sẵn bộ MCP Tools chất lượng cao:
     - `gemini_web_ask`: Truy vấn đơn lẻ với tốc độ cao.
     - `gemini_web_chat`: Hội thoại nhiều lượt có ghi nhớ ngữ cảnh (Session persistence).
     - `gemini_web_deep_research`: Kích hoạt tính năng Deep Research từ tài khoản Gemini Web.
     - `gemini_web_account_info`: Kiểm tra số dư credit, hạn mức reset, model khả dụng.

3. **Cung cấp OpenAI-Compatible API Proxy Server:**
   - Cung cấp endpoint chuẩn `/v1/chat/completions` và `/v1/models`.
   - Hỗ trợ cả Non-Streaming và Streaming (Server-Sent Events - SSE).
   - Cho phép mọi extension, SDK hoặc agent hỗ trợ OpenAI API đều có thể trỏ vào sử dụng.

4. **Độ ổn định cao:**
   - Cơ chế tự động thử lại (Retry Backoff) xử lý triệt để hiện tượng ngắt kết nối SSL hoặc mạng chập chờn.
   - Bộ chuyển đổi prompt thông minh tránh kích hoạt bộ lọc bảo mật của Google Gemini Web.

---

## 3. CÀI ĐẶT & CHUẨN BỊ MÔI TRƯỜNG

### Bước 1: Yêu cầu hệ thống
- Python >= 3.11 (Hệ thống hiện tại đang sử dụng Python 3.12).
- Trình duyệt đã đăng nhập vào [gemini.google.com/app](https://gemini.google.com/app) (khuyên dùng Microsoft Edge hoặc Google Chrome).

### Bước 2: Cài đặt gói `gemini2anti`
Mở Terminal tại thư mục dự án:
```powershell
pip install -e .
```

### Bước 3: Kiểm tra kết nối
Chạy lệnh kiểm tra tự động:
```powershell
gemini2anti check
```
Kết quả hiển thị:
- Danh sách trình duyệt phát hiện được cookie hợp lệ.
- Trạng thái kiểm tra kết nối với máy chủ Google Gemini.
- Danh sách model khả dụng (`gemini-flash`, `gemini-pro`, `gemini-argon`) và số credit quota còn lại.

---

## 4. HƯỚNG DẪN KÍCH HOẠT VÀO ANTIGRAVITY & AGY CLI

### Cách 1: Đăng ký MCP Server (Khuyên dùng - Tiện lợi nhất)

Chạy lệnh tự động đăng ký:
```powershell
gemini2anti install-mcp
```

Sau khi chạy lệnh trên, MCP Server `gemini-web` sẽ được đăng ký vào danh sách của `agy`. Kiểm tra lại bằng lệnh:
```powershell
agy mcp list
```
Bạn sẽ thấy `gemini-web` ở trạng thái `enabled`.

**Cách sử dụng trong Antigravity IDE / CLI (`agy`):**
Trong quá trình pair-programming hoặc chat với Antigravity, bạn chỉ cần yêu cầu:
- *"Hãy hỏi model Gemini Web xem thuật toán này tối ưu như thế nào"*
- *"Dùng tool gemini_web_ask để phân tích đoạn code sau"*
- *"Bắt đầu phiên chat gemini_web_chat để cùng thảo luận kiến trúc"*
- *"Kích hoạt gemini_web_deep_research tìm hiểu về công nghệ WebAssembly"*

Agent Antigravity sẽ tự động gọi tool `gemini_web_ask` hoặc `gemini_web_chat` để lấy câu trả lời trực tiếp từ tài khoản Gemini Web của bạn.

---

### Cách 2: Chạy OpenAI-Compatible Proxy Server

Nếu bạn muốn sử dụng các model từ Gemini Web qua các công cụ ngoài hoặc cấu hình `base_url`:

Khởi chạy server:
```powershell
gemini2anti serve --port 8000
```
Hoặc:
```powershell
python run_proxy.py --port 8000
```

Các endpoint khả dụng:
- **Base URL:** `http://127.0.0.1:8000/v1`
- **Models Endpoint:** `GET http://127.0.0.1:8000/v1/models`
- **Chat Endpoint:** `POST http://127.0.0.1:8000/v1/chat/completions`
- **Health Check:** `GET http://127.0.0.1:8000/health`

**Ví dụ gọi bằng Python OpenAI SDK:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="sk-not-required"
)

response = client.chat.completions.create(
    model="auto",  # hoặc 'gemini-flash', 'gemini-pro'
    messages=[
        {"role": "user", "content": "Giải thích Decorator trong Python trong 2 câu ngắn gọn."}
    ],
    stream=False
)

print(response.choices[0].message.content)
```

---

### Cách 3: Chat trực tiếp trong Terminal

Để trò chuyện nhanh hoặc thử nghiệm mà không cần mở trình duyệt:
```powershell
gemini2anti chat
```
Các tùy chọn:
- `--model <name>`: Chọn model (`auto`, `gemini-pro`, `gemini-flash`). Mặc định là `auto`.
- `--thinking`: Bật chế độ suy nghĩ mở rộng (Extended Thinking).

---

## 5. CẤU HÌNH NÂNG CAO (NẾU CẦN THỦ CÔNG)

Nếu không muốn dùng cơ chế quét cookie tự động từ trình duyệt, bạn có thể xuất hoặc tạo file `.env`:

```powershell
gemini2anti export-env
```

Nội dung file `.env` được tạo ra:
```ini
GEMINI_AUTO_BROWSER_COOKIES=false
GEMINI_SECURE_1PSID=g.a000...
GEMINI_SECURE_1PSIDTS=sidts-...
GEMINI_SECURE_1PSIDCC=...
GEMINI_DEFAULT_MODEL=auto
GEMINI_PROXY=
```

**Cách lấy thủ công từ trình duyệt:**
1. Truy cập `https://gemini.google.com/app` và đăng nhập tài khoản Google.
2. Nhấn `F12` mở Developer Tools -> chuyển qua thẻ **Application** (hoặc **Storage**).
3. Tại menu bên trái, mở **Cookies** -> chọn `https://gemini.google.com`.
4. Tìm và sao chép giá trị của:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS`
   - `__Secure-1PSIDCC`
5. Dán vào file `.env` tương ứng.

---

## 6. DANH MỤC CÁC TỆP TIN TRONG DỰ ÁN

| Đường dẫn | Vai trò |
| :--- | :--- |
| `gemini2anti/cli.py` | Điểm điều khiển dòng lệnh đa năng (`check`, `chat`, `serve`, `install-mcp`, `export-env`) |
| `gemini2anti/client.py` | Lõi kết nối Gemini Web Engine, cơ chế retry, quản lý phiên và model |
| `gemini2anti/config.py` | Quản trị cấu hình, tích hợp bóc tách cookie tự động qua `rookiepy` |
| `gemini2anti/mcp_server.py` | Máy chủ Model Context Protocol (FastMCP) chuẩn hóa cho Antigravity / agy |
| `gemini2anti/proxy_server.py` | Máy chủ HTTP tương thích 100% chuẩn OpenAI API (FastAPI + Uvicorn) |
| `run_mcp.py` | Entrypoint độc lập chạy MCP Server |
| `run_proxy.py` | Entrypoint độc lập chạy OpenAI Proxy Server |
| `pyproject.toml` & `requirements.txt` | Cấu hình cài đặt gói pip |


---

## 7. KHUYẾN NGHỊ SỬ DỤNG & TUÂN THỦ QUY CHẾ GOOGLE

### 1. Về mặt Điều khoản Dịch vụ của Google (Google Terms of Service)
Nếu xét theo nghĩa đen và chặt chẽ nhất của quy chế: Cách làm này nằm ở "vùng xám" (grey zone) và về mặt kỹ thuật không được Google cấp phép chính thức.
- **Lý do:** Trong [Google Terms of Service](https://policies.google.com/terms) và [Google Generative AI Additional Terms of Service](https://policies.google.com/terms/generative-ai), Google có điều khoản cấm rõ: *"Không can thiệp, truy cập dịch vụ của chúng tôi bằng bất kỳ phương thức nào khác ngoài các giao diện được chúng tôi hỗ trợ công khai..."* (non-publicly supported interfaces / web automation / reverse engineering).
- Giao diện web `gemini.google.com` được thiết kế cho con người tương tác qua trình duyệt. Khi chúng ta trích xuất session/cookie để biến thành MCP Server cho Antigravity/CLI gọi tự động, về bản chất kỹ thuật đây là hình thức **Reverse Engineering Unofficial API**.
- Đối với nhu cầu lập trình/tự động hóa, Google yêu cầu nhà phát triển sử dụng kênh chính thống là **Google AI Studio** hoặc **Google Cloud Vertex AI** (dùng API Key chính thức).

### 2. Về mặt thực tế sử dụng (Dự án sạch & mục đích cá nhân)
Mặc dù về mặt kỹ thuật không thuộc kênh chính thống, nhưng bạn có thể an tâm ở các điểm sau:
- **Không có rủi ro pháp lý:** Bạn dùng để phục vụ công việc cá nhân, hỗ trợ lập trình dự án sạch, không phá hoại hệ thống, không trục lợi bằng cách mở dịch vụ bán lại API lậu, và không cào dữ liệu huấn luyện mô hình cạnh tranh. Google không bao giờ đi kiện tụng người dùng cá nhân trong trường hợp này.
- **Rủi ro duy nhất là ở cấp độ Tài khoản (Account Risk):**
  - **Văng phiên / Hết hạn Cookie:** Cookie web của Google có thời hạn hoặc sẽ bị vô hiệu hóa khi có sự thay đổi về IP, bảo mật.
  - **Cơ chế chống Bot tự động (Abuse Detection):** Nếu bạn gửi prompt quá dồn dập (ví dụ vòng lặp gọi hàng chục request/phút), hệ thống bảo mật của Google có thể nhận diện lưu lượng bất thường và tạm khóa/chặn tính năng Gemini của tài khoản đó, hoặc bắt giải CAPTCHA.

### 3. Khuyến nghị thực tế để an tâm sử dụng
- **Sử dụng tài khoản Google phụ (Secondary Account):** Tuyệt đối không dùng tài khoản Google chính (chứa Gmail làm việc lâu năm, Google Drive quan trọng, tài khoản liên kết Google Pay/ngân hàng) để trích xuất cookie web. Hãy dùng một tài khoản Google riêng biệt để đăng nhập Gemini Web và lấy session cho Antigravity. Nếu tài khoản này có bị gắn cờ hạn chế thì công việc chính của bạn hoàn toàn không bị ảnh hưởng.
- **Kiểm soát tần suất gọi:** Tránh các kịch bản loop tự động bắn request liên tục không có độ trễ nghỉ (delay).

