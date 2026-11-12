#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BỘ CÀI ĐẶT TOÀN DIỆN: ANTIGRAVITY SKILLS & GEMINI 4 WEB (ALL-IN-ONE)
=============================================================================
Hỗ trợ: Antigravity IDE, Antigravity Desktop App, Antigravity CLI (agy).
Hoạt động trên mọi hệ điều hành (Windows, macOS, Linux) và bất kỳ thư mục nào.

Tự động cài đặt & cấu hình:
1. Thư viện Python lõi
2. Cookie Google Gemini Web & Quản lý Multi-Account Pool
3. MCP Server 'gemini-web' (Gemini 4 Argon Extended Thinking)
4. Toàn bộ Slash Commands (/kg4, /qw, /quota-workflow)
5. Toàn bộ Thư viện Skills (kg4, quota-workflow, docx, xlsx, pptx, pdf)
=============================================================================
"""

import sys
import os
import shutil
import json
import subprocess
from pathlib import Path

# Cấu hình UTF-8 cho console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Thư mục gốc của repository (xác định động 100%)
REPO_DIR = Path(__file__).resolve().parent

def get_effective_python() -> Path:
    """Tự động phát hiện hoặc khởi tạo virtualenv trong .venv để đảm bảo an toàn và độc lập."""
    venv_dir = REPO_DIR / ".venv"
    if sys.platform == "win32":
        venv_py = venv_dir / "Scripts" / "python.exe"
    else:
        venv_py = venv_dir / "bin" / "python"
    
    if venv_py.exists():
        return venv_py
    
    # Nếu uv có sẵn và chưa có .venv, tạo .venv
    if shutil.which("uv"):
        try:
            subprocess.run(["uv", "venv", str(venv_dir)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if venv_py.exists():
                return venv_py
        except Exception:
            pass
            
    return Path(sys.executable)

PYTHON_EXE = get_effective_python()

# Thư mục cấu hình toàn cục của Antigravity
HOME_DIR = Path.home()
GEMINI_DIR = HOME_DIR / ".gemini"
CONFIG_DIR = GEMINI_DIR / "config"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp_config.json"
GLOBAL_WORKFLOWS_DIR = CONFIG_DIR / "global_workflows"
GLOBAL_SKILLS_DIR = CONFIG_DIR / "skills"


def print_banner():
    print("=" * 76)
    print("  🚀 BỘ CÀI ĐẶT TOÀN DIỆN: ANTIGRAVITY SKILLS & GEMINI 4 WEB SUITE")
    print("  ⭐ Hỗ trợ: Antigravity IDE | Desktop App | Antigravity CLI (agy)")
    print(f"  📂 Thư mục dự án: {REPO_DIR}")
    print(f"  🐍 Python runtime: {PYTHON_EXE}")
    print("  👤 Bản quyền: Copyright (c) 2026 Dương Nguyễn Quốc Sáng & NDKBVH")
    print("=" * 76)


def check_and_install_dependencies():
    """Kiểm tra và tự động cài đặt các thư viện Python cần thiết."""
    print("\n[Bước 1/6] Kiểm tra và cài đặt các thư viện Python...")
    global PYTHON_EXE
    PYTHON_EXE = get_effective_python()

    # Thử kiểm tra thư viện với PYTHON_EXE
    check_code = "import gemini_webapi, mcp, dotenv; print('OK')"
    try:
        res = subprocess.run([str(PYTHON_EXE), "-c", check_code], capture_output=True, text=True)
        if res.returncode == 0 and "OK" in res.stdout:
            print("  ✅ Các thư viện cần thiết đã sẵn sàng!")
            return True
    except Exception:
        pass

    req_file = REPO_DIR / "requirements.txt"
    if not req_file.exists():
        print(f"  ❌ Không tìm thấy {req_file}")
        return False

    # Ưu tiên cài qua uv nếu có
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", str(PYTHON_EXE), "-r", str(req_file)]
    else:
        cmd = [str(PYTHON_EXE), "-m", "pip", "install", "-r", str(req_file)]

    try:
        subprocess.check_call(cmd)
        print("  ✅ Các thư viện cần thiết đã cài đặt thành công!")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi khi cài đặt thư viện: {e}")
        return False



def setup_cookie_and_env():
    """Kiểm tra cookie đăng nhập từ các trình duyệt và khởi tạo .env."""
    print("\n[Bước 2/6] Kiểm tra tài khoản Google Gemini Web...")
    if str(REPO_DIR) not in sys.path:
        sys.path.insert(0, str(REPO_DIR))

    try:
        from gemini2anti.config import extract_cookies_from_browser, get_gemini_credentials
        
        # Thử quét cookie từ các trình duyệt phổ biến
        found_browser = None
        for b in ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]:
            cookies = extract_cookies_from_browser(b)
            if cookies.get("__Secure-1PSID") and cookies.get("__Secure-1PSIDTS"):
                found_browser = b.upper()
                print(f"  ✅ Phát hiện phiên đăng nhập Google Gemini hợp lệ từ trình duyệt: {found_browser}")
                break

        psid, psidts, psidcc, source = get_gemini_credentials()
        if psid and psidts:
            print(f"  🔑 Nguồn xác thực: {source}")
            # Tự động xuất .env nếu chưa có
            env_file = REPO_DIR / ".env"
            if not env_file.exists():
                env_content = (
                    "# Tự động tạo bởi Antigravity Installer\n"
                    f"GEMINI_SECURE_1PSID={psid}\n"
                    f"GEMINI_SECURE_1PSIDTS={psidts}\n"
                    f"GEMINI_SECURE_1PSIDCC={psidcc or ''}\n"
                    "GEMINI_DEFAULT_MODEL=gemini-4\n"
                    "GEMINI_EXTENDED_THINKING=true\n"
                    "GEMINI_AUTO_BROWSER_COOKIES=true\n"
                )
                env_file.write_text(env_content, encoding="utf-8")
                print("  📝 Đã tạo file .env cấu hình cục bộ.")
            return True
        else:
            print("  ⚠️ CHÚ Ý: Chưa tìm thấy phiên đăng nhập Google Gemini trên trình duyệt.")
            print("  👉 Vui lòng mở trình duyệt Microsoft Edge, Chrome hoặc Firefox,")
            print("     đăng nhập vào: https://gemini.google.com/app")
            print("     Sau khi đăng nhập xong, chạy lại file này để hoàn tất kết nối!")
            return True
    except Exception as e:
        print(f"  ⚠️ Cảnh báo kiểm tra cookie: {e}")
        return True


def register_mcp_server():
    """Đăng ký MCP Server gemini-web vào cấu hình của Antigravity."""
    print("\n[Bước 3/6] Đăng ký MCP Server 'gemini-web' vào Antigravity...")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config_data = {"mcpServers": {}}
    if MCP_CONFIG_FILE.exists():
        try:
            config_data = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
            if "mcpServers" not in config_data:
                config_data["mcpServers"] = {}
        except Exception as e:
            print(f"  ⚠️ Đọc file mcp_config.json cũ gặp lỗi ({e}), khởi tạo mới.")
            config_data = {"mcpServers": {}}

    run_mcp_script = REPO_DIR / "run_mcp.py"
    if not run_mcp_script.exists():
        print(f"  ❌ Không tìm thấy script runner {run_mcp_script}")
        return False

    config_data["mcpServers"]["gemini-web"] = {
        "command": str(PYTHON_EXE),
        "args": [str(run_mcp_script)],
        "env": {
            "PYTHONIOENCODING": "utf-8"
        }
    }

    try:
        MCP_CONFIG_FILE.write_text(json.dumps(config_data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"  ✅ Đã lưu cấu hình MCP vào: {MCP_CONFIG_FILE}")
    except Exception as e:
        print(f"  ❌ Không thể ghi file {MCP_CONFIG_FILE}: {e}")
        return False

    # Đồng bộ sang các thư mục cấu hình biến thể nếu có
    extra_dirs = [
        GEMINI_DIR / "antigravity" / "mcp",
        GEMINI_DIR / "antigravity-ide",
        GEMINI_DIR / "antigravity-cli" / "mcp"
    ]
    for ed in extra_dirs:
        try:
            if ed.parent.exists():
                ed.mkdir(parents=True, exist_ok=True)
                target_json = ed / "mcp_config.json" if ed.is_dir() and not ed.name == "mcp" else None
                if target_json:
                    target_json.write_text(json.dumps(config_data, indent=4, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return True


def install_slash_commands():
    """Cài đặt toàn bộ Slash Commands (/kg4, /qw, /quota-workflow) vào Antigravity."""
    print("\n[Bước 4/6] Cài đặt các lệnh Slash Commands vào Antigravity...")
    GLOBAL_WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

    def safe_copy_file(src_path: Path, dst_path: Path):
        dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")

    workflows_to_install = [
        ("kg4.md", REPO_DIR / "workflows" / "kg4.md"),
        ("qw.md", REPO_DIR / "workflows" / "qw.md"),
        ("quota-workflow.md", REPO_DIR / "workflows" / "quota-workflow.md"),
    ]

    for wf_name, wf_path in workflows_to_install:
        if wf_path.exists():
            safe_copy_file(wf_path, GLOBAL_WORKFLOWS_DIR / wf_name)
            print(f"  ✅ Đã cài đặt Workflow: /{wf_name.replace('.md', '')} -> ~/.gemini/config/global_workflows/{wf_name}")
        else:
            print(f"  ⚠️ Bỏ qua {wf_name} (không tìm thấy tại {wf_path})")

    return True


def install_skills_library():
    """Cài đặt toàn bộ Skills vào Antigravity toàn cục (~/.gemini/config/skills/)."""
    print("\n[Bước 5/6] Cài đặt toàn bộ Thư viện Skills vào Antigravity...")
    GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    skills_map = {
        "kg4": REPO_DIR / "skills" / "kg4",
        "quota-workflow": REPO_DIR / "quota-workflow",
        "docx": REPO_DIR / ".agents" / "skills" / "docx",
        "xlsx": REPO_DIR / ".agents" / "skills" / "xlsx",
        "pptx": REPO_DIR / ".agents" / "skills" / "pptx",
        "pdf": REPO_DIR / ".agents" / "skills" / "pdf",
    }

    def copy_dir_recursive(src: Path, dst: Path):
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            target = dst / item.name
            if item.is_dir():
                copy_dir_recursive(item, target)
            else:
                try:
                    target.write_bytes(item.read_bytes())
                except Exception:
                    shutil.copyfile(item, target)

    for skill_name, skill_path in skills_map.items():
        if skill_path.exists() and skill_path.is_dir():
            target_dir = GLOBAL_SKILLS_DIR / skill_name
            try:
                copy_dir_recursive(skill_path, target_dir)
                print(f"  ✅ Đã cài đặt Skill: @{skill_name} -> ~/.gemini/config/skills/{skill_name}/")
            except Exception as e:
                print(f"  ⚠️ Lỗi khi sao chép skill {skill_name}: {e}")
        else:
            print(f"  ⚠️ Không tìm thấy thư mục skill {skill_name} tại {skill_path}")

    return True


def test_live_connection():
    """Kiểm tra kết nối thời gian thực đến mô hình Gemini 4 Argon Web."""
    print("\n[Bước 6/6] Kiểm tra kết nối thời gian thực tới Gemini 4 Argon...")
    try:
        import asyncio
        from gemini2anti.client import bridge

        async def _test():
            res = await bridge.generate("Xin chào Gemini 4, bạn đã sẵn sàng chưa?", model="gemini-4")
            return res.get("text", "")

        text = asyncio.run(_test())
        if text:
            print("  🎉 KẾT NỐI GEMINI 4 ARGON THÀNH CÔNG RỰC RỠ!")
            print(f"  🤖 Phản hồi thử nghiệm: {text[:160]}...")
            return True
        else:
            print("  ⚠️ Chưa nhận được phản hồi từ Gemini 4.")
            return False
    except Exception as e:
        print(f"  ⚠️ Lưu ý kết nối: {e}")
        print("  (Bạn có thể mở Antigravity và gõ /kg4 để trải nghiệm thực tế bất cứ lúc nào).")
        return True


def main():
    print_banner()

    if not check_and_install_dependencies():
        print("\n❌ Cài đặt thất bại ở bước cài đặt thư viện.")
        return 1

    # Nếu đang chạy bằng python hệ thống nhưng có .venv, tự động re-exec vào .venv
    venv_dir = REPO_DIR / ".venv"
    if venv_dir.exists() and Path(sys.prefix).resolve() != venv_dir.resolve():
        effective_py = get_effective_python()
        if effective_py.exists():
            os.environ["VIRTUAL_ENV"] = str(venv_dir)
            os.execv(str(effective_py), [str(effective_py)] + sys.argv)

    setup_cookie_and_env()

    if not register_mcp_server():
        print("\n❌ Cài đặt thất bại ở bước đăng ký MCP Server.")
        return 1

    install_slash_commands()
    install_skills_library()
    test_live_connection()

    print("\n" + "=" * 76)
    print("  🎊 CHÚC MỪNG! BẠN ĐÃ CÀI ĐẶT THÀNH CÔNG ANTIGRAVITY SKILLS SUITE!")
    print("=" * 76)
    print("  👉 CÁC LỆNH SỬ DỤNG TRÊN ANTIGRAVITY (IDE, App, agy CLI):")
    print("     1. Trò chuyện & giải toán với Gemini 4 High (Web):")
    print("        /kg4 <nội dung câu hỏi hoặc yêu cầu>")
    print("        Ví dụ: /kg4 Phân tích kiến trúc vi dịch vụ và viết Dockerfile")
    print("")
    print("     2. Điều phối tác vụ lớn tiết kiệm Quota Pro (quota-workflow):")
    print("        /qw <mô tả tác vụ lớn>")
    print("        Ví dụ: /qw Nâng cấp cơ sở dữ liệu và viết unit tests")
    print("")
    print("     3. Xử lý tài liệu văn phòng tiêu chuẩn:")
    print("        Tự động hỗ trợ các định dạng .docx, .xlsx, .pptx, .pdf qua skills")
    print("=" * 76 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
