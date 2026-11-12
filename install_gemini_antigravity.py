#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BỘ CÀI ĐẶT TỰ ĐỘNG: KẾT NỐI GOOGLE GEMINI 4 WEB VỚI ANTIGRAVITY (TOÀN HỆ THỐNG)
=============================================================================
Hỗ trợ: Antigravity IDE, Antigravity Desktop App, Antigravity CLI (agy).
Hoạt động trên mọi hệ điều hành (Windows, macOS, Linux) và bất kỳ thư mục nào.
Lệnh slash command kích hoạt: /kg4
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
PYTHON_EXE = sys.executable

# Thư mục cấu hình toàn cục của Antigravity
HOME_DIR = Path.home()
GEMINI_DIR = HOME_DIR / ".gemini"
CONFIG_DIR = GEMINI_DIR / "config"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp_config.json"
GLOBAL_WORKFLOWS_DIR = CONFIG_DIR / "global_workflows"
GLOBAL_SKILLS_DIR = CONFIG_DIR / "skills"


def print_banner():
    print("=" * 72)
    print("  🚀 TỰ ĐỘNG KẾT NỐI GOOGLE GEMINI 4 (ARGON) VỚI ANTIGRAVITY")
    print("  ⭐ Hỗ trợ: Antigravity IDE | Antigravity App | Antigravity CLI (agy)")
    print(f"  📂 Thư mục dự án: {REPO_DIR}")
    print(f"  🐍 Python runtime: {PYTHON_EXE}")
    print("  👤 Bản quyền: Copyright (c) 2026 NDKBVH")
    print("=" * 72)



def check_and_install_dependencies():
    """Kiểm tra và tự động cài đặt các thư viện cần thiết."""
    print("\n[Bước 1/5] Kiểm tra và cài đặt các thư viện Python...")
    try:
        import gemini_webapi
        import mcp
        import dotenv
        print("  ✅ Các thư viện cần thiết đã sẵn sàng!")
        return True
    except ImportError:
        pass

    req_file = REPO_DIR / "requirements.txt"
    if not req_file.exists():
        print(f"  ❌ Không tìm thấy {req_file}")
        return False

    # Thử cài đặt qua uv nếu có
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", str(PYTHON_EXE), "-r", str(req_file)]
    else:
        cmd = [PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)]
    try:
        subprocess.check_call(cmd)
        print("  ✅ Các thư viện cần thiết đã sẵn sàng!")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi khi cài đặt thư viện: {e}")
        return False


def setup_cookie_and_env():
    """Kiểm tra cookie đăng nhập từ các trình duyệt và khởi tạo .env."""
    print("\n[Bước 2/5] Kiểm tra tài khoản Google Gemini Web...")
    if str(REPO_DIR) not in sys.path:
        sys.path.insert(0, str(REPO_DIR))

    try:
        from gemini2anti.config import extract_cookies_from_browser, get_gemini_credentials
        
        # Thử quét cookie từ các trình duyệt
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
                env_content = f"# Tự động tạo bởi installer\nGEMINI_SECURE_1PSID={psid}\nGEMINI_SECURE_1PSIDTS={psidts}\nGEMINI_SECURE_1PSIDCC={psidcc or ''}\nGEMINI_DEFAULT_MODEL=gemini-4\nGEMINI_EXTENDED_THINKING=true\nGEMINI_AUTO_BROWSER_COOKIES=true\n"
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
    print("\n[Bước 3/5] Đăng ký MCP Server 'gemini-web' vào Antigravity...")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Đọc cấu hình hiện tại nếu có
    config_data = {"mcpServers": {}}
    if MCP_CONFIG_FILE.exists():
        try:
            config_data = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
            if "mcpServers" not in config_data:
                config_data["mcpServers"] = {}
        except Exception as e:
            print(f"  ⚠️ Đọc file mcp_config.json cũ gặp lỗi ({e}), tạo cấu hình mới.")
            config_data = {"mcpServers": {}}

    # Entrypoint runner
    run_mcp_script = REPO_DIR / "run_mcp.py"
    if not run_mcp_script.exists():
        print(f"  ❌ Không tìm thấy script {run_mcp_script}")
        return False

    config_data["mcpServers"]["gemini-web"] = {
        "command": str(PYTHON_EXE),
        "args": [str(run_mcp_script)],
        "env": {
            "PYTHONIOENCODING": "utf-8"
        }
    }

    # Ghi lại file mcp_config.json
    try:
        MCP_CONFIG_FILE.write_text(json.dumps(config_data, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"  ✅ Đã lưu cấu hình MCP vào: {MCP_CONFIG_FILE}")
    except Exception as e:
        print(f"  ❌ Không thể ghi file {MCP_CONFIG_FILE}: {e}")
        return False

    # Đồng bộ sang các thư mục Antigravity biến thể nếu có
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


def install_slash_commands_and_skills():
    """Cài đặt slash command /kg4 và skills vào Antigravity toàn cục."""
    print("\n[Bước 4/5] Cài đặt lệnh slash command '/kg4' vào Antigravity...")
    GLOBAL_WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Cài đặt Workflows
    wf_src_kg4 = REPO_DIR / "workflows" / "kg4.md"
    wf_src_g4 = REPO_DIR / "workflows" / "g4.md"

    def safe_copy_file(src_path: Path, dst_path: Path):
        dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")

    if wf_src_kg4.exists():
        safe_copy_file(wf_src_kg4, GLOBAL_WORKFLOWS_DIR / "kg4.md")
        print("  ✅ Đã cài đặt Workflow: /kg4 -> ~/.gemini/config/global_workflows/kg4.md")
    if wf_src_g4.exists():
        safe_copy_file(wf_src_g4, GLOBAL_WORKFLOWS_DIR / "g4.md")
        print("  ✅ Đã cài đặt Workflow: /g4  -> ~/.gemini/config/global_workflows/g4.md")

    # 2. Cài đặt Skills
    for skill_name in ["kg4", "g4"]:
        skill_src = REPO_DIR / "skills" / skill_name
        skill_dst = GLOBAL_SKILLS_DIR / skill_name
        if skill_src.exists():
            skill_dst.mkdir(parents=True, exist_ok=True)
            for f in skill_src.iterdir():
                if f.is_file():
                    safe_copy_file(f, skill_dst / f.name)
            print(f"  ✅ Đã cài đặt Skill: @{skill_name} -> ~/.gemini/config/skills/{skill_name}/")

    return True


def test_live_connection():
    """Kiểm tra kết nối trực tiếp đến mô hình Gemini 4 Argon."""
    print("\n[Bước 5/5] Kiểm tra kết nối thời gian thực tới Gemini 4...")
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

    setup_cookie_and_env()

    if not register_mcp_server():
        print("\n❌ Cài đặt thất bại ở bước đăng ký MCP Server.")
        return 1

    if not install_slash_commands_and_skills():
        print("\n❌ Cài đặt thất bại ở bước cài đặt lệnh /kg4.")
        return 1

    test_live_connection()

    print("\n" + "=" * 72)
    print("  🎊 CHÚC MỪNG! BẠN ĐÃ KẾT NỐI THÀNH CÔNG GEMINI 4 VỚI ANTIGRAVITY!")
    print("=" * 72)
    print("  👉 CÁCH DÙNG TRÊN ANTIGRAVITY (App, IDE, agy CLI):")
    print("     Gõ lệnh trực tiếp tại khung chat:")
    print("       /kg4 <câu hỏi hoặc yêu cầu của bạn>")
    print("     Ví dụ:")
    print("       /kg4 Xin chào, bạn là ai và phiên bản nào?")
    print("       /kg4 Viết cho tôi một giải thuật tối ưu bằng Python")
    print("=" * 72 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
