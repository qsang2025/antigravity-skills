#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chuyển hướng tương thích ngược (Backward Compatibility Forwarder)
Tự động gọi tới bộ cài đặt tổng hợp: install.py
"""

import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_DIR))

import install

if __name__ == "__main__":
    sys.exit(install.main() or 0)
