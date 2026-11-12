#!/usr/bin/env python3
"""
CLI Launcher cho gemini2anti.
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from gemini2anti.cli import main

if __name__ == "__main__":
    sys.exit(main() or 0)
