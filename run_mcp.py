#!/usr/bin/env python3
"""
Entrypoint chạy MCP Server cho Antigravity / agy CLI.
"""
import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from gemini2anti.mcp_server import main

if __name__ == "__main__":
    main()
