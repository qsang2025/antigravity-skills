#!/usr/bin/env python3
"""
Entrypoint khởi chạy OpenAI-Compatible HTTP Proxy Server.
"""
import sys
import argparse
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from gemini2anti.proxy_server import start_proxy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Khởi chạy OpenAI-compatible Proxy Server cho Gemini Web")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ host (mặc định: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Cổng port (mặc định: 8000)")
    args = parser.parse_args()

    print(f"🚀 Đang khởi động Gemini Web OpenAI Proxy tại http://{args.host}:{args.port}")
    print(f"   API Base URL: http://{args.host}:{args.port}/v1")
    print(f"   Kiểm tra sức khỏe: http://{args.host}:{args.port}/health")
    start_proxy(host=args.host, port=args.port)
