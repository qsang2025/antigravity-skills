#!/usr/bin/env bash
# ==============================================================================
# SCRIPT KHOI DONG CAI DAT ANTIGRAVITY SKILLS & GEMINI 4 WEB CHO LINUX / MACOS
# ==============================================================================

set -e

# Chuyen den thu muc chua script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================================================="
echo "  🚀 ĐANG KHỞI TẠO BỘ CÀI ĐẶT ANTIGRAVITY SKILLS & GEMINI 4 WEB..."
echo "=============================================================================="
echo ""

# Kiem tra trinh thuc thi Python
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "❌ Lỗi: Không tìm thấy Python trên máy tính của bạn!"
    echo "👉 Vui lòng cài đặt Python 3.10+ từ https://www.python.org hoặc package manager."
    exit 1
fi

echo "Sử dụng trình thực thi: $PY_CMD"
echo ""

# Chay bo cai dat tong hop
$PY_CMD install.py
