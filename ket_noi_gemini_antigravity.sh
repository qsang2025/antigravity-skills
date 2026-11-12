#!/usr/bin/env bash
# ==============================================================================
# KẾT NỐI GEMINI 4 ARGON VỚI ANTIGRAVITY (LINUX / MACOS)
# ==============================================================================

set -e

# Chuyển đến thư mục chứa script
cd "$(dirname "$0")"

echo "=============================================================================="
echo "  ĐANG KHỞI TẠO HỆ THỐNG KẾT NỐI GEMINI 4 ARGON VỚI ANTIGRAVITY..."
echo "=============================================================================="
echo ""

# Tìm Python 3
if command -v python3 >/dev/null 2>&1; then
    PY_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PY_CMD=python
else
    echo "[LỖI] Không tìm thấy Python trên hệ thống của bạn!"
    echo "👉 Vui lòng cài đặt Python 3 (ví dụ: brew install python hoặc sudo apt install python3 python3-pip)"
    exit 1
fi

echo "Sử dụng: $($PY_CMD --version)"
echo ""

$PY_CMD install_gemini_antigravity.py

echo ""
echo "[HOÀN TẤT] Hệ thống đã sẵn sàng! Mở Antigravity và gõ /kg4 để trải nghiệm."
