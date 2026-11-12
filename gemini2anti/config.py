"""
Quản lý cấu hình và bóc tách Cookie cho Gemini Web (gemini.google.com/app).
Hỗ trợ cả trích xuất tự động từ trình duyệt (Edge, Chrome, Firefox, Brave...) và cấu hình thủ công.
Hỗ trợ Multi-Account Cookie Pool (nhiều tài khoản với hậu tố _1.._N hoặc tự động quét trình duyệt).
"""

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Tải cấu hình từ .env tại thư mục làm việc hoặc thư mục dự án
load_dotenv(override=False)

try:
    import rookiepy
    HAS_ROOKIEPY = True
except ImportError:
    HAS_ROOKIEPY = False


@dataclass
class GeminiAccountConfig:
    """Cấu hình cho một tài khoản Gemini Web trong Cookie Pool."""
    id: str
    name: str
    psid: str
    psidts: str = ""
    psidcc: str = ""
    source: str = ""

    def masked_psid(self) -> str:
        """Trả về chuỗi rút gọn an toàn của PSID để log/hiển thị."""
        if not self.psid:
            return "***"
        if len(self.psid) > 12:
            return f"{self.psid[:6]}...{self.psid[-4:]}"
        return "***"


def extract_cookies_from_browser(browser_name: str = "edge") -> Dict[str, str]:
    """
    Trích xuất cookies của Google từ trình duyệt được chỉ định.
    Hỗ trợ: edge, chrome, firefox, brave, opera, vivaldi.
    """
    if not HAS_ROOKIEPY:
        return {}

    browser_map = {
        "edge": rookiepy.edge,
        "chrome": rookiepy.chrome,
        "firefox": rookiepy.firefox,
        "brave": rookiepy.brave,
        "opera": rookiepy.opera,
        "vivaldi": rookiepy.vivaldi,
    }

    getter = browser_map.get(browser_name.lower())
    if not getter:
        return {}

    try:
        cookies = getter(["google.com"])
        res = {}
        for c in cookies:
            name = c.get("name")
            value = c.get("value")
            if name in ["__Secure-1PSID", "__Secure-1PSIDTS", "__Secure-1PSIDCC"]:
                res[name] = value
        return res
    except Exception:
        return {}


def get_gemini_account_pool(include_browser: Optional[bool] = None) -> List[GeminiAccountConfig]:
    """
    Trích xuất toàn bộ danh sách tài khoản Gemini Web khả dụng vào Multi-Account Pool.
    
    Thứ tự nạp:
    1. Biến môi trường đơn lẻ truyền thống (GEMINI_SECURE_1PSID, GEMINI_SECURE_1PSIDTS, GEMINI_SECURE_1PSIDCC)
    2. Biến môi trường đánh số _1, _2, ..., _N (GEMINI_SECURE_1PSID_1, GEMINI_SECURE_1PSIDTS_1, ...)
    3. Trình duyệt tự động (Edge, Chrome, Firefox, Brave...) nếu include_browser bật hoặc cấu hình GEMINI_AUTO_BROWSER_COOKIES
    
    Khử trùng lặp theo giá trị PSID.
    """
    pool: List[GeminiAccountConfig] = []
    seen_psids: Dict[str, int] = {}

    def add_or_merge(acc: GeminiAccountConfig):
        if not acc.psid or not acc.psid.strip():
            return
        clean_psid = acc.psid.strip()
        if clean_psid in seen_psids:
            idx = seen_psids[clean_psid]
            existing = pool[idx]
            if not existing.psidts and acc.psidts:
                existing.psidts = acc.psidts
            if not existing.psidcc and acc.psidcc:
                existing.psidcc = acc.psidcc
            return
        seen_psids[clean_psid] = len(pool)
        pool.append(acc)

    # 1. Biến môi trường đơn lẻ truyền thống
    env_psid = os.getenv("GEMINI_SECURE_1PSID", "").strip()
    env_psidts = os.getenv("GEMINI_SECURE_1PSIDTS", "").strip()
    env_psidcc = os.getenv("GEMINI_SECURE_1PSIDCC", "").strip()
    env_name = os.getenv("GEMINI_ACCOUNT_NAME", "").strip() or "Primary (.env)"

    if env_psid:
        add_or_merge(GeminiAccountConfig(
            id="account_default",
            name=env_name,
            psid=env_psid,
            psidts=env_psidts,
            psidcc=env_psidcc,
            source="env:GEMINI_SECURE_1PSID",
        ))

    # 2. Biến môi trường đánh số _1, _2, ..., _N
    numbered_keys = []
    for k in os.environ:
        m = re.match(r"^GEMINI_SECURE_1PSID_(\d+)$", k)
        if m:
            numbered_keys.append((int(m.group(1)), k))
    numbered_keys.sort(key=lambda x: x[0])

    for idx_num, k in numbered_keys:
        psid = os.getenv(k, "").strip()
        psidts = os.getenv(f"GEMINI_SECURE_1PSIDTS_{idx_num}", "").strip()
        psidcc = os.getenv(f"GEMINI_SECURE_1PSIDCC_{idx_num}", "").strip()
        name = os.getenv(f"GEMINI_ACCOUNT_NAME_{idx_num}", "").strip() or f"Account #{idx_num} (.env)"
        if psid:
            add_or_merge(GeminiAccountConfig(
                id=f"account_{idx_num}",
                name=name,
                psid=psid,
                psidts=psidts,
                psidcc=psidcc,
                source=f"env:GEMINI_SECURE_1PSID_{idx_num}",
            ))

    # 3. Trình duyệt tự động
    auto_enabled = os.getenv("GEMINI_AUTO_BROWSER_COOKIES", "true").lower() in ["1", "true", "yes"]
    custom_sources = os.getenv("GEMINI_BROWSER_SOURCES", "").strip()
    preferred_browser = os.getenv("GEMINI_PREFERRED_BROWSER", "edge").lower()

    should_scan_browser = False
    if include_browser is True:
        should_scan_browser = True
    elif include_browser is False:
        should_scan_browser = False
    else:
        # include_browser is None: quét nếu auto_enabled hoặc có custom sources hoặc pool chưa có tài khoản nào
        if auto_enabled or custom_sources or not pool:
            should_scan_browser = True

    if should_scan_browser and HAS_ROOKIEPY:
        if custom_sources:
            browsers = [b.strip().lower() for b in custom_sources.split(",") if b.strip()]
        else:
            browsers = [preferred_browser] + [b for b in ["edge", "chrome", "firefox", "brave"] if b != preferred_browser]

        for b in browsers:
            cks = extract_cookies_from_browser(b)
            b_psid = cks.get("__Secure-1PSID", "").strip()
            b_psidts = cks.get("__Secure-1PSIDTS", "").strip()
            b_psidcc = cks.get("__Secure-1PSIDCC", "").strip()
            if b_psid:
                add_or_merge(GeminiAccountConfig(
                    id=f"browser_{b}",
                    name=f"Browser ({b.upper()})",
                    psid=b_psid,
                    psidts=b_psidts,
                    psidcc=b_psidcc,
                    source=f"browser:{b}",
                ))

    return pool


def get_gemini_credentials() -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """
    Lấy thông tin đăng nhập Gemini Web (tương thích ngược 100%).
    Trả về tuple: (psid, psidts, psidcc, source_description)
    """
    pool = get_gemini_account_pool()
    if pool:
        first = pool[0]
        return first.psid, first.psidts or None, first.psidcc or None, first.source

    return None, None, None, "Không tìm thấy Cookie đăng nhập Gemini"


def get_default_model() -> str:
    """Trả về model mặc định được cấu hình."""
    return os.getenv("GEMINI_DEFAULT_MODEL", "gemini-4")


def get_default_extended_thinking() -> bool:
    """
    Trả về chế độ suy nghĩ mở rộng mặc định (Extended Thinking / High reasoning).
    Mặc định luôn là True (Gemini 4 High).
    """
    val = os.getenv("GEMINI_EXTENDED_THINKING", "true").lower()
    return val in ["1", "true", "yes", "high", "on"]


def get_proxy() -> Optional[str]:
    """Trả về proxy nếu có."""
    proxy = os.getenv("GEMINI_PROXY", "").strip()
    return proxy if proxy else None
