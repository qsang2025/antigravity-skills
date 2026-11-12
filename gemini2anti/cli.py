"""
Giao diện dòng lệnh (CLI) chính của công cụ gemini2anti.
Cung cấp các lệnh quản trị, kiểm tra kết nối, chat tương tác, khởi chạy MCP và Proxy.
"""

import sys
import os
import asyncio
import subprocess
import argparse
import json
import shutil
from pathlib import Path

from gemini2anti.config import (
    get_gemini_credentials,
    get_gemini_account_pool,
    extract_cookies_from_browser,
    get_default_model,
    HAS_ROOKIEPY,
)
from gemini2anti.client import bridge


def cmd_check(args):
    """Kiểm tra và hiển thị tình trạng Cookie và tài khoản Gemini Web."""
    print("=" * 70)
    print("🔍 KIỂM TRA KẾT NỐI VÀ XÁC THỰC GOOGLE GEMINI WEB (gemini.google.com/app)")
    print("=" * 70)

    # 1. Quét cookies trong các trình duyệt
    print("\n[1] Quét Cookie từ các trình duyệt cục bộ:")
    if not HAS_ROOKIEPY:
        print("  ⚠️ Thư viện rookiepy chưa được cài đặt. Không thể quét cookie tự động.")
    else:
        for b in ["edge", "chrome", "firefox", "brave"]:
            cks = extract_cookies_from_browser(b)
            if cks.get("__Secure-1PSID"):
                print(f"  ✅ {b.upper()}: Tìm thấy Cookie hợp lệ (__Secure-1PSID, TS: {bool(cks.get('__Secure-1PSIDTS'))})")
            else:
                print(f"  ❌ {b.upper()}: Không tìm thấy Cookie Gemini")

    # 2. Kiểm tra Multi-Account Cookie Pool
    pool = get_gemini_account_pool()
    print(f"\n[2] Multi-Account Cookie Pool ({len(pool)} tài khoản được phát hiện):")
    if not pool:
        print("  ❌ Không có Cookie hợp lệ nào được phát hiện trong cấu hình.")
        print("  👉 Hướng dẫn: Hãy mở Microsoft Edge hoặc Chrome, đăng nhập https://gemini.google.com/app")
        print("     hoặc điền GEMINI_SECURE_1PSID vào file .env.")
        return 1

    for idx, acc in enumerate(pool, 1):
        ts_status = "Có" if acc.psidts else "Không"
        cc_status = "Có" if acc.psidcc else "Không"
        print(f"  [{idx}] {acc.name} (ID: {acc.id})")
        print(f"      - Nguồn: {acc.source}")
        print(f"      - PSID : {acc.masked_psid()} (TS: {ts_status}, CC: {cc_status})")

    # 3. Kết nối thử nghiệm với máy chủ Google Gemini Web
    print("\n[3] Đang kết nối kiểm tra toàn bộ Cookie Pool với Google Gemini Web...")
    try:
        async def _test_conn():
            status = await bridge.get_status(check_all=True)
            summary = status.get("pool_summary", {})
            active_id = status.get("active_account_id")

            print("  🎉 KẾT NỐI THÀNH CÔNG!")
            print(f"  - Trạng thái Pool : Total: {summary.get('total')}, Active: {summary.get('active')}, "
                  f"Rate Limited: {summary.get('rate_limited')}, Auth Error: {summary.get('auth_error')}")
            print(f"  - Chiến lược Pool : {summary.get('strategy')}")
            print(f"  - Tài khoản Active: {active_id}")
            print(f"  - Model mặc định  : {status.get('default_model')}")
            print(f"  - Model khả dụng  : {', '.join(status.get('available_models', []))}")

            accounts = status.get("accounts", [])
            if accounts:
                print("\n  📋 CHI TIẾT TỪNG TÀI KHOẢN TRONG POOL:")
                for acc in accounts:
                    is_active_str = "⭐ [ACTIVE HIỆN TẠI]" if acc.get("is_active") else "  [DỰ PHÒNG]"
                    status_str = acc.get("status")
                    print(f"    {is_active_str} {acc.get('name')} (ID: {acc.get('id')}) | Trạng thái: {status_str}")
                    if acc.get("last_error"):
                        print(f"        ⚠️ Lỗi: {acc.get('last_error')}")
                    quotas = acc.get("quotas", {})
                    if quotas:
                        for qname, qval in quotas.items():
                            print(f"        • Quota {qname}: Còn {qval.get('remaining')}/{qval.get('total')} credits (Reset: {qval.get('reset_time')})")

        asyncio.run(_test_conn())
    except Exception as e:
        print(f"  ❌ Lỗi khi khởi tạo phiên làm việc với Gemini Web: {e}")
        return 1

    print("\n✅ Multi-Account Pool đã sẵn sàng để tích hợp vào Antigravity / agy!")
    return 0


def cmd_chat(args):
    """Trò chuyện trực tiếp với Gemini Web trong Terminal."""
    model = args.model or get_default_model()
    extended_thinking = args.thinking

    print("=" * 70)
    print(f"💬 TRÒ CHUYỆN VỚI GOOGLE GEMINI WEB ({model.upper()})")
    print("   Gõ 'exit' hoặc 'quit' để thoát. Gõ 'clear' để bắt đầu phiên mới.")
    if extended_thinking:
        print("   🧠 Chế độ Extended Thinking (Suy nghĩ sâu): BẬT")
    print("=" * 70)

    async def _interactive():
        session_id = "cli_session"
        while True:
            try:
                user_input = input("\n👤 Bạn: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nĐã thoát phiên chat.")
                break

            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Tạm biệt!")
                break
            if user_input.lower() == "clear":
                await bridge.reset_session(session_id)
                print("🧹 Đã làm mới phiên hội thoại.")
                continue

            print(f"🤖 Gemini ({model}): ", end="", flush=True)
            try:
                res = await bridge.chat(
                    message=user_input,
                    session_id=session_id,
                    model=model,
                    extended_thinking=extended_thinking
                )
                print(res.get("text", ""))
                images = res.get("images", [])
                if images:
                    print("\n[Ảnh đính kèm]:")
                    for img in images:
                        print(f"  - {img}")
            except Exception as e:
                print(f"\n❌ Lỗi phản hồi: {e}")

    asyncio.run(_interactive())
    return 0


def cmd_mcp(args):
    """Khởi chạy MCP Server qua stdio."""
    from gemini2anti.mcp_server import main as mcp_main
    mcp_main()
    return 0


def cmd_serve(args):
    """Khởi chạy OpenAI-compatible proxy server."""
    from gemini2anti.proxy_server import start_proxy
    print(f"🚀 Khởi chạy OpenAI-compatible Proxy Server tại http://{args.host}:{args.port}")
    start_proxy(host=args.host, port=args.port)
    return 0


def cmd_install_mcp(args):
    """Tự động đăng ký MCP Server vào Antigravity CLI (agy)."""
    server_name = args.name or "gemini-web"
    user_home = Path.home()
    target_dir = user_home / ".gemini" / "antigravity" / "mcp" / server_name
    target_dir.mkdir(parents=True, exist_ok=True)
    server_script = target_dir / "server.py"

    server_code = """#!/usr/bin/env python3
# Autogenerated MCP Runner for gemini-web
from gemini2anti.mcp_server import main

if __name__ == "__main__":
    main()
"""
    server_script.write_text(server_code, encoding="utf-8")

    print(f"📦 Đang đăng ký MCP Server '{server_name}' vào Antigravity CLI (agy)...")
    print(f"   Script: {server_script}")

    # Đăng ký vào mcp_config.json cho IDE và Desktop App
    mcp_config_path = user_home / ".gemini" / "config" / "mcp_config.json"
    mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = {"mcpServers": {}}
    if mcp_config_path.exists():
        try:
            cfg = json.loads(mcp_config_path.read_text(encoding="utf-8"))
            if "mcpServers" not in cfg:
                cfg["mcpServers"] = {}
        except Exception:
            cfg = {"mcpServers": {}}

    cfg["mcpServers"][server_name] = {
        "command": sys.executable,
        "args": [str(server_script)],
        "env": {"PYTHONIOENCODING": "utf-8"}
    }
    mcp_config_path.write_text(json.dumps(cfg, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ Đã lưu cấu hình vào: {mcp_config_path}")

    # Đăng ký qua agy CLI nếu có
    has_agy = bool(shutil.which("agy"))
    if has_agy:
        subprocess.run(["agy", "mcp", "remove", server_name], capture_output=True, text=True)
        subprocess.run(["agy", "mcp", "add", server_name, sys.executable, str(server_script)], capture_output=True, text=True)
        print("  ✅ Đã đăng ký đồng bộ vào Antigravity CLI (agy).")

    print("🎉 ĐĂNG KÝ THÀNH CÔNG VÀO ANTIGRAVITY!")
    print("\nHiện tại bạn có thể sử dụng các tool sau trong mọi phiên agy, App hoặc Antigravity IDE:")
    print("  - gemini_web_ask(prompt, model, extended_thinking)")
    print("  - gemini_web_chat(message, session_id, model)")
    print("  - gemini_web_deep_research(topic)")
    print("  - gemini_web_account_info()")
    print("  👉 Lệnh kích hoạt nhanh: /kg4 <nội dung>")
    return 0



def cmd_export_env(args):
    """Xuất Cookie hiện hành ra file .env."""
    psid, psidts, psidcc, source = get_gemini_credentials()
    if not psid:
        print("❌ Không tìm thấy Cookie nào để xuất.")
        return 1

    target_env = Path(".env")
    env_content = f"""# Tự động xuất từ: {source}
GEMINI_SECURE_1PSID={psid}
GEMINI_SECURE_1PSIDTS={psidts or ''}
GEMINI_SECURE_1PSIDCC={psidcc or ''}
GEMINI_DEFAULT_MODEL=gemini-pro
"""
    target_env.write_text(env_content, encoding="utf-8")
    print(f"✅ Đã xuất thông tin Cookie thành công vào: {target_env.resolve()}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="gemini2anti",
        description="Cầu nối mô hình AI từ Google Gemini Web (gemini.google.com/app) vào Antigravity / agy"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Lệnh chức năng")

    # Subcommand: check
    subparsers.add_parser("check", help="Kiểm tra cookies, quota và kết nối với Google Gemini Web")

    # Subcommand: chat
    p_chat = subparsers.add_parser("chat", help="Trò chuyện tương tác với Gemini Web trong Terminal")
    p_chat.add_argument("--model", "-m", default="gemini-4", help="Model muốn dùng (mặc định: gemini-4 / Gemini 4 High)")
    p_chat.add_argument("--thinking", "-t", action="store_true", default=True, help="Chế độ suy nghĩ mở rộng (Extended Thinking / High) - Mặc định: True")
    p_chat.add_argument("--no-thinking", dest="thinking", action="store_false", help="Tắt chế độ suy nghĩ mở rộng")

    # Subcommand: mcp
    subparsers.add_parser("mcp", help="Chạy MCP Server (stdio) cho Antigravity")

    # Subcommand: serve
    p_serve = subparsers.add_parser("serve", help="Khởi chạy OpenAI-compatible API Proxy Server")
    p_serve.add_argument("--host", default="127.0.0.1", help="Địa chỉ IP lắng nghe (mặc định: 127.0.0.1)")
    p_serve.add_argument("--port", "-p", type=int, default=8000, help="Cổng lắng nghe (mặc định: 8000)")

    # Subcommand: install-mcp
    p_inst = subparsers.add_parser("install-mcp", help="Tự động đăng ký MCP server vào Antigravity CLI (agy)")
    p_inst.add_argument("--name", default="gemini-web", help="Tên MCP Server (mặc định: gemini-web)")

    # Subcommand: export-env
    subparsers.add_parser("export-env", help="Trích xuất cookies từ trình duyệt và lưu ra file .env")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        return 0

    commands = {
        "check": cmd_check,
        "chat": cmd_chat,
        "mcp": cmd_mcp,
        "serve": cmd_serve,
        "install-mcp": cmd_install_mcp,
        "export-env": cmd_export_env,
    }

    return commands[args.subcommand](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
