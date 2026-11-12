"""
Module lõi quản lý kết nối, Multi-Account Cookie Pool và Automatic Failover với Google Gemini Web.
Tự động chuyển tiếp yêu cầu sang tài khoản kế tiếp khi chạm giới hạn Quota (429) hoặc lỗi xác thực (AuthError).
"""

import os
import time
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, List, Optional, Any, Tuple

from gemini_webapi import GeminiClient
try:
    from gemini_webapi.exceptions import (
        AuthError,
        UsageLimitExceededError,
        TemporarilyBlockedError,
        APIError,
        TimeoutError,
    )
except ImportError:
    AuthError = UsageLimitExceededError = TemporarilyBlockedError = APIError = TimeoutError = Exception

from gemini2anti.config import (
    GeminiAccountConfig,
    get_gemini_account_pool,
    get_gemini_credentials,
    get_default_model,
    get_default_extended_thinking,
    get_proxy,
)

logger = logging.getLogger("gemini2anti.client")


class AccountStatus(str, Enum):
    """Trạng thái vòng đời của một tài khoản trong Cookie Pool."""
    ACTIVE = "ACTIVE"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_ERROR = "AUTH_ERROR"
    DISABLED = "DISABLED"


# Alias để hỗ trợ tương thích mã gọi
AccountState = AccountStatus


@dataclass
class GeminiClientWrapper:
    """Wrapper đóng gói một tài khoản Gemini Web kèm client và metadata trạng thái."""
    config: GeminiAccountConfig
    client: Optional[GeminiClient] = None
    status: AccountStatus = AccountStatus.ACTIVE
    initialized: bool = False
    fail_count: int = 0
    request_count: int = 0
    last_used: Optional[float] = None
    last_error: Optional[str] = None
    cooldown_until: Optional[float] = None
    reset_time: Optional[str] = None
    quotas: Dict[str, Any] = field(default_factory=dict)
    abuse_status: str = "clean"
    available_models: List[str] = field(default_factory=list)

    def check_and_recover(self, now: Optional[float] = None) -> bool:
        """
        Kiểm tra và tự động khôi phục tài khoản từ RATE_LIMITED về ACTIVE khi hết thời gian làm nguội (cooldown).
        """
        if self.status == AccountStatus.RATE_LIMITED and self.cooldown_until is not None:
            current_time = now if now is not None else time.time()
            if current_time >= self.cooldown_until:
                self.status = AccountStatus.ACTIVE
                self.cooldown_until = None
                self.last_error = None
                return True
        return False

    def to_dict(self, is_active: bool = False) -> Dict[str, Any]:
        """Xuất thông tin tài khoản dạng dictionary minh bạch."""
        cooldown_remaining = None
        if self.cooldown_until and self.status == AccountStatus.RATE_LIMITED:
            cooldown_remaining = max(0, int(self.cooldown_until - time.time()))

        return {
            "id": self.config.id,
            "name": self.config.name,
            "source": self.config.source,
            "masked_psid": self.config.masked_psid(),
            "status": self.status.value,
            "is_active": is_active,
            "initialized": self.initialized,
            "fail_count": self.fail_count,
            "request_count": self.request_count,
            "last_used": self.last_used,
            "quotas": self.quotas,
            "reset_time": self.reset_time,
            "cooldown_until": self.cooldown_until,
            "cooldown_remaining_seconds": cooldown_remaining,
            "last_error": self.last_error,
            "abuse_status": self.abuse_status,
            "available_models": self.available_models,
        }


class AccountPoolManager:
    """Quản lý danh sách các tài khoản Gemini Web trong Pool và chiến lược điều phối."""
    def __init__(self):
        self._wrappers: List[GeminiClientWrapper] = []
        self._current_index: int = 0
        self._lock = asyncio.Lock()
        self._strategy = os.getenv("GEMINI_POOL_STRATEGY", "active_first").lower().strip()
        self._default_cooldown = int(os.getenv("GEMINI_RATE_LIMIT_COOLDOWN", "1800"))
        self.reload_pool(force_reset=True)

    def reload_pool(self, force_reset: bool = False):
        """Nạp danh sách tài khoản từ config. Giữ nguyên trạng thái tài khoản cũ nếu force_reset=False."""
        configs = get_gemini_account_pool()
        if force_reset or not self._wrappers:
            self._wrappers = [GeminiClientWrapper(config=cfg) for cfg in configs]
            self._current_index = 0
            return

        old_by_psid = {w.config.psid: w for w in self._wrappers}
        new_wrappers = []
        for cfg in configs:
            if cfg.psid in old_by_psid:
                old_w = old_by_psid[cfg.psid]
                old_w.config = cfg
                new_wrappers.append(old_w)
            else:
                new_wrappers.append(GeminiClientWrapper(config=cfg))

        self._wrappers = new_wrappers
        if self._current_index >= len(self._wrappers):
            self._current_index = 0

    def get_candidate_wrappers(self) -> List[GeminiClientWrapper]:
        """
        Lấy danh sách các tài khoản ứng viên theo thứ tự ưu tiên.
        Tự động gọi check_and_recover() trên từng tài khoản.
        """
        for w in self._wrappers:
            w.check_and_recover()

        if not self._wrappers:
            return []

        n = len(self._wrappers)
        ordered = [self._wrappers[(self._current_index + i) % n] for i in range(n)]

        active_candidates = [w for w in ordered if w.status == AccountStatus.ACTIVE]
        if active_candidates:
            return active_candidates

        # Phương án dự phòng khẩn cấp: nếu tất cả tài khoản đều bị rate limited, lấy tài khoản có cooldown sớm nhất
        rate_limited = [w for w in self._wrappers if w.status == AccountStatus.RATE_LIMITED]
        if rate_limited:
            rate_limited.sort(key=lambda w: w.cooldown_until or float("inf"))
            return rate_limited

        return []

    def set_active_account(self, account_id: str):
        """Đặt tài khoản có account_id làm tài khoản hiện hành."""
        for idx, w in enumerate(self._wrappers):
            if w.config.id == account_id:
                self._current_index = idx
                break

    def advance_round_robin(self):
        """Chuyển sang tài khoản tiếp theo nếu cấu hình strategy=round_robin."""
        if self._strategy == "round_robin" and len(self._wrappers) > 1:
            self._current_index = (self._current_index + 1) % len(self._wrappers)

    def mark_account_status(
        self,
        account_id: str,
        status: AccountStatus,
        error_msg: str = "",
        cooldown_seconds: Optional[float] = None
    ):
        """Cập nhật trạng thái cho tài khoản và dịch chuyển con trỏ pool nếu cần."""
        for w in self._wrappers:
            if w.config.id == account_id:
                w.status = status
                w.fail_count += 1
                w.last_error = error_msg
                if status == AccountStatus.RATE_LIMITED:
                    cd = cooldown_seconds if cooldown_seconds is not None else self._default_cooldown
                    w.cooldown_until = time.time() + cd
                elif status == AccountStatus.AUTH_ERROR:
                    w.client = None
                    w.initialized = False
                break

        if len(self._wrappers) > 1:
            self._current_index = (self._current_index + 1) % len(self._wrappers)

    def get_summary(self) -> Dict[str, Any]:
        """Tóm tắt tổng quan trạng thái Multi-Account Pool."""
        return {
            "total": len(self._wrappers),
            "active": sum(1 for w in self._wrappers if w.status == AccountStatus.ACTIVE),
            "rate_limited": sum(1 for w in self._wrappers if w.status == AccountStatus.RATE_LIMITED),
            "auth_error": sum(1 for w in self._wrappers if w.status == AccountStatus.AUTH_ERROR),
            "disabled": sum(1 for w in self._wrappers if w.status == AccountStatus.DISABLED),
            "strategy": self._strategy,
        }


class GeminiWebBridge:
    """
    Quản lý phiên kết nối, xác thực, Multi-Account Cookie Pool và Automatic Failover với Gemini Web.
    """
    def __init__(self):
        self.pool = AccountPoolManager()
        self._client: Optional[GeminiClient] = None
        self._lock = asyncio.Lock()
        self._sessions: Dict[str, Any] = {}
        self._session_history: Dict[str, List[Dict[str, str]]] = {}
        self._session_account_map: Dict[str, str] = {}
        self._auth_source: str = ""
        self._available_models: List[str] = ["gemini-pro", "gemini-flash", "gemini-flash-lite", "gemini-argon"]

    def _classify_exception(self, exc: Exception) -> Tuple[bool, AccountStatus, Optional[float]]:
        """
        Phân loại ngoại lệ để quyết định cơ chế Failover.
        Trả về: (should_failover, target_status, cooldown_seconds)
        """
        cls_name = exc.__class__.__name__.lower()
        msg = str(exc).lower()
        full_err = f"{cls_name} {msg}"

        # 1. Kiểm tra lỗi Quota / Rate Limit
        if isinstance(exc, (UsageLimitExceededError, TemporarilyBlockedError)):
            return True, AccountStatus.RATE_LIMITED, None

        rate_limit_keywords = [
            "usagelimitexceeded", "temporarilyblocked", "429", "rate limit",
            "quota", "too many requests", "exhausted", "resource_exhausted",
            "usage limit", "limit exceeded"
        ]
        if any(kw in full_err for kw in rate_limit_keywords):
            return True, AccountStatus.RATE_LIMITED, None

        # 2. Kiểm tra lỗi Xác thực (Auth Error / Cookie hết hạn)
        if isinstance(exc, AuthError):
            return True, AccountStatus.AUTH_ERROR, None

        auth_keywords = [
            "autherror", "401", "403", "unauthenticated", "cookie", "expired",
            "login", "snlm0e", "failed to initialize", "invalid credentials", "forbidden"
        ]
        if any(kw in full_err for kw in auth_keywords):
            return True, AccountStatus.AUTH_ERROR, None

        return False, AccountStatus.ACTIVE, None

    async def _init_wrapper_client(
        self,
        wrapper: GeminiClientWrapper,
        force_refresh: bool = False
    ) -> GeminiClient:
        """Khởi tạo phiên GeminiClient cho một wrapper tài khoản cụ thể."""
        if wrapper.client and wrapper.initialized and not force_refresh:
            return wrapper.client

        psid = wrapper.config.psid
        psidts = wrapper.config.psidts
        psidcc = wrapper.config.psidcc
        proxy = get_proxy()

        client = GeminiClient(
            secure_1psid=psid,
            secure_1psidts=psidts,
            secure_1psidcc=psidcc,
            proxy=proxy,
        )

        last_err = None
        for attempt in range(2):
            try:
                await client.init(timeout=25)
                wrapper.client = client
                wrapper.initialized = True
                wrapper.status = AccountStatus.ACTIVE
                wrapper.last_error = None
                last_err = None
                break
            except Exception as e:
                last_err = e
                if attempt < 1:
                    await asyncio.sleep(1.0)

        if last_err is not None:
            wrapper.initialized = False
            wrapper.client = None
            raise last_err

        # Cập nhật danh sách models nếu có
        try:
            models = client.list_models()
            if models:
                wrapper.available_models = [m.model_name for m in models]
                self._available_models = wrapper.available_models
        except Exception:
            pass

        # Cập nhật thông tin quota
        try:
            if hasattr(client, "quotas") and client.quotas:
                quotas_info = {}
                for k, v in client.quotas.items():
                    quotas_info[k] = {
                        "remaining": getattr(v, "remaining", None),
                        "total": getattr(v, "total", None),
                        "reset_time": str(getattr(v, "reset_time", None)),
                    }
                    if getattr(v, "reset_time", None):
                        wrapper.reset_time = str(getattr(v, "reset_time", None))
                wrapper.quotas = quotas_info
        except Exception:
            pass

        if hasattr(client, "abuse_status"):
            wrapper.abuse_status = getattr(client, "abuse_status", "clean")

        return wrapper.client

    async def init_client(self, force_refresh: bool = False) -> GeminiClient:
        """
        Khởi tạo hoặc trả về client của tài khoản khả dụng hiện tại (hỗ trợ tương thích ngược).
        """
        candidates = self.pool.get_candidate_wrappers()
        if not candidates:
            # Thử reload lại pool từ config
            self.pool.reload_pool()
            candidates = self.pool.get_candidate_wrappers()

        if not candidates:
            raise ValueError(
                "Không tìm thấy Cookie đăng nhập Gemini hợp lệ trong Multi-Account Pool! "
                "Hãy đăng nhập https://gemini.google.com trên trình duyệt hoặc cấu hình GEMINI_SECURE_1PSID trong file .env."
            )

        last_err = None
        for wrapper in candidates:
            try:
                client = await self._init_wrapper_client(wrapper, force_refresh=force_refresh)
                self._client = client
                self._auth_source = wrapper.config.source
                self.pool.set_active_account(wrapper.config.id)
                return client
            except Exception as e:
                last_err = e
                should_failover, new_status, cd = self._classify_exception(e)
                if should_failover:
                    logger.warning(
                        f"[Pool Init Failover] Tài khoản '{wrapper.config.id}' gặp lỗi {new_status.value}: {e}. "
                        f"Thử tài khoản tiếp theo..."
                    )
                    self.pool.mark_account_status(wrapper.config.id, new_status, str(e), cd)
                else:
                    raise e

        raise last_err or RuntimeError("Không thể khởi tạo bất kỳ tài khoản nào trong Cookie Pool.")

    async def _execute_with_failover(self, operation_name: str, operation_factory) -> Any:
        """
        Hàm bao quát thực thi với cơ chế Automatic Failover đa tài khoản.
        """
        candidates = self.pool.get_candidate_wrappers()
        if not candidates:
            self.pool.reload_pool()
            candidates = self.pool.get_candidate_wrappers()

        if not candidates:
            raise RuntimeError("Multi-Account Pool: Không có tài khoản nào khả dụng để thực hiện tác vụ!")

        last_exc = None
        tried_accounts = []

        for wrapper in candidates:
            tried_accounts.append(wrapper.config.id)
            try:
                async with self._lock:
                    client = await self._init_wrapper_client(wrapper)
                    self._client = client
                    self._auth_source = wrapper.config.source
                    self.pool.set_active_account(wrapper.config.id)

                res = await operation_factory(wrapper, client)
                wrapper.last_used = time.time()
                wrapper.request_count += 1

                if self.pool._strategy == "round_robin":
                    self.pool.advance_round_robin()

                return res
            except Exception as exc:
                last_exc = exc
                should_failover, new_status, cd = self._classify_exception(exc)
                if should_failover:
                    logger.warning(
                        f"[Pool Failover - {operation_name}] Tài khoản '{wrapper.config.id}' ({wrapper.config.name}) "
                        f"gặp lỗi {new_status.value}: {exc}. Đang tự động chuyển sang tài khoản kế tiếp..."
                    )
                    self.pool.mark_account_status(wrapper.config.id, new_status, str(exc), cd)
                    continue
                else:
                    # Lỗi nghiệp vụ hoặc tham số không hợp lệ: không chuyển pool
                    raise exc

        raise RuntimeError(
            f"Multi-Account Pool: Toàn bộ {len(tried_accounts)} tài khoản trong pool đã thất bại ({', '.join(tried_accounts)}). "
            f"Lỗi cuối cùng: {last_exc}"
        ) from last_exc

    async def get_status(self, check_all: bool = True) -> Dict[str, Any]:
        """
        Lấy thông tin trạng thái pool, tài khoản active, quota, abuse status và các model khả dụng.
        Nếu check_all=True: kiểm tra và làm mới trạng thái mọi tài khoản trong pool.
        """
        # Đảm bảo pool đã được nạp
        if not self.pool._wrappers:
            self.pool.reload_pool()

        if check_all:
            for w in self.pool._wrappers:
                try:
                    await self._init_wrapper_client(w)
                except Exception as e:
                    should_failover, status, cd = self._classify_exception(e)
                    if should_failover:
                        self.pool.mark_account_status(w.config.id, status, str(e), cd)
                    else:
                        w.last_error = str(e)

        # Tìm wrapper đang active
        active_wrapper: Optional[GeminiClientWrapper] = None
        candidates = self.pool.get_candidate_wrappers()
        if candidates:
            active_wrapper = candidates[0]
        elif self.pool._wrappers:
            active_wrapper = self.pool._wrappers[self.pool._current_index % len(self.pool._wrappers)]

        active_account_id = active_wrapper.config.id if active_wrapper else None
        active_quotas = active_wrapper.quotas if active_wrapper else {}
        active_abuse = active_wrapper.abuse_status if active_wrapper else "unknown"
        active_source = active_wrapper.config.source if active_wrapper else self._auth_source

        models = active_wrapper.available_models if (active_wrapper and active_wrapper.available_models) else self._available_models

        # Xây dựng danh sách accounts minh bạch
        accounts_list = [
            w.to_dict(is_active=(w.config.id == active_account_id))
            for w in self.pool._wrappers
        ]

        summary = self.pool.get_summary()
        top_status = "connected" if summary["active"] > 0 else ("all_rate_limited" if summary["rate_limited"] > 0 else "error")

        return {
            "status": top_status,
            "auth_source": active_source,
            "abuse_status": active_abuse,
            "quotas": active_quotas,
            "available_models": models,
            "default_model": get_default_model(),
            "active_account_id": active_account_id,
            "pool_summary": summary,
            "accounts": accounts_list,
        }

    def _resolve_model(self, client: GeminiClient, model_name: Optional[str]) -> Optional[Any]:
        """Tìm model phù hợp trong registry của Gemini Web, mặc định tuyệt đối là Gemini 4 Argon."""
        if not model_name:
            model_name = get_default_model()

        name_clean = model_name.lower().strip()
        if name_clean in [
            "auto", "default", "gemini", "gemini-web", "current",
            "gemini-4", "gemini 4", "gemini4", "argon", "gemini-argon", "4-argon", "4 argon"
        ]:
            try:
                return client.resolve_model("gemini-argon")
            except Exception:
                pass

        alias_map = {
            "gemini-4": "gemini-argon",
            "gemini 4": "gemini-argon",
            "gemini4": "gemini-argon",
            "gemini-4-argon": "gemini-argon",
            "4-argon": "gemini-argon",
            "4 argon": "gemini-argon",
            "argon": "gemini-argon",
            "gemini-3.8-flash": "gemini-flash",
            "gemini-flash": "gemini-flash",
            "flash": "gemini-flash",
            "gemini-3.1-pro": "gemini-pro",
            "gemini-pro": "gemini-pro",
            "pro": "gemini-pro",
            "gemini-flash-lite": "gemini-flash-lite",
            "flash-lite": "gemini-flash-lite",
            "gpt-4": "gemini-argon",
            "gpt-4o": "gemini-flash",
            "claude-3-5-sonnet": "gemini-argon",
        }
        target = alias_map.get(name_clean, name_clean)
        try:
            return client.resolve_model(target)
        except Exception:
            try:
                return client.resolve_model("gemini-argon")
            except Exception:
                return None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
        files: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Tạo phản hồi hoàn chỉnh từ Gemini Web với cơ chế Automatic Failover.
        """
        if extended_thinking is None:
            extended_thinking = get_default_extended_thinking()

        async def _call(wrapper: GeminiClientWrapper, client: GeminiClient):
            resolved_model = self._resolve_model(client, model)
            response = await client.generate_content(
                prompt=prompt,
                model=resolved_model,
                extended_thinking=extended_thinking,
                files=files,
            )
            return {
                "text": response.text,
                "model": model or get_default_model(),
                "account_id": wrapper.config.id,
                "images": [getattr(img, "url", "") for img in getattr(response, "images", [])],
                "thoughts": getattr(response, "thoughts", None),
            }

        return await self._execute_with_failover("generate", _call)

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
        files: Optional[List[Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream từng mẩu phản hồi (token delta) từ Gemini Web kèm cơ chế Failover an toàn.
        """
        if extended_thinking is None:
            extended_thinking = get_default_extended_thinking()

        candidates = self.pool.get_candidate_wrappers()
        if not candidates:
            self.pool.reload_pool()
            candidates = self.pool.get_candidate_wrappers()

        if not candidates:
            raise RuntimeError("Multi-Account Pool: Không có tài khoản nào khả dụng để stream phản hồi!")

        last_exc = None
        for wrapper in candidates:
            started = False
            try:
                async with self._lock:
                    client = await self._init_wrapper_client(wrapper)
                    self._client = client
                    self._auth_source = wrapper.config.source
                    self.pool.set_active_account(wrapper.config.id)

                resolved_model = self._resolve_model(client, model)
                last_length = 0

                stream_iter = client.generate_content_stream(
                    prompt=prompt,
                    model=resolved_model,
                    extended_thinking=extended_thinking,
                    files=files,
                )

                async for chunk in stream_iter:
                    started = True
                    current_text = chunk.text or ""
                    if len(current_text) > last_length:
                        delta = current_text[last_length:]
                        last_length = len(current_text)
                        yield delta

                wrapper.last_used = time.time()
                wrapper.request_count += 1
                if self.pool._strategy == "round_robin":
                    self.pool.advance_round_robin()
                return

            except Exception as exc:
                last_exc = exc
                if started:
                    # Nếu stream đã bắt đầu xuất dữ liệu cho client, không thể restart ngầm vì sẽ trùng lặp token
                    raise exc

                should_failover, new_status, cd = self._classify_exception(exc)
                if should_failover:
                    logger.warning(
                        f"[Pool Failover Stream] Tài khoản '{wrapper.config.id}' gặp lỗi {new_status.value}: {exc}. "
                        f"Tự động chuyển tài khoản tiếp theo..."
                    )
                    self.pool.mark_account_status(wrapper.config.id, new_status, str(exc), cd)
                    continue
                else:
                    raise exc

        raise RuntimeError(
            f"Multi-Account Pool: Toàn bộ tài khoản trong pool đã thất bại khi stream. Lỗi: {last_exc}"
        ) from last_exc

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Gửi tin nhắn trong phiên hội thoại nhiều lượt (Multi-turn Chat Session).
        Tự động duy trì ngữ cảnh liền mạch khi xảy ra Failover giữa các tài khoản.
        """
        if extended_thinking is None:
            extended_thinking = get_default_extended_thinking()

        if session_id not in self._session_history:
            self._session_history[session_id] = []

        # Lưu tin nhắn người dùng vào lịch sử ngữ cảnh
        self._session_history[session_id].append({"role": "user", "content": message})

        async def _call(wrapper: GeminiClientWrapper, client: GeminiClient):
            resolved_model = self._resolve_model(client, model)

            current_account = self._session_account_map.get(session_id)
            need_new_session = (
                session_id not in self._sessions
                or current_account != wrapper.config.id
                or not hasattr(self._sessions[session_id], "send_message")
            )

            if need_new_session:
                chat_session = client.start_chat(model=resolved_model)
                self._sessions[session_id] = chat_session
                self._session_account_map[session_id] = wrapper.config.id

                # Nếu chuyển sang tài khoản mới và đã có lịch sử hội thoại trước đó, ghép ngữ cảnh
                history = self._session_history.get(session_id, [])
                if len(history) > 1:
                    context_chunks = ["[Previous conversation context]"]
                    # Ghép các lượt trước (trừ tin nhắn hiện tại)
                    for turn in history[:-1]:
                        role_str = "User" if turn["role"] == "user" else "Assistant"
                        context_chunks.append(f"{role_str}: {turn['content']}")
                    context_chunks.append("[Current user message]")
                    context_chunks.append(message)
                    prompt_to_send = "\n\n".join(context_chunks)
                else:
                    prompt_to_send = message
            else:
                chat_session = self._sessions[session_id]
                prompt_to_send = message

            response = await chat_session.send_message(
                prompt=prompt_to_send,
                extended_thinking=extended_thinking,
            )

            # Lưu câu trả lời trợ lý vào lịch sử
            self._session_history[session_id].append({"role": "assistant", "content": response.text})

            return {
                "text": response.text,
                "session_id": session_id,
                "account_id": wrapper.config.id,
                "model": model or get_default_model(),
                "images": [getattr(img, "url", "") for img in getattr(response, "images", [])],
            }

        return await self._execute_with_failover("chat", _call)

    async def reset_session(self, session_id: str = "default") -> bool:
        """Đặt lại phiên hội thoại và xóa lịch sử ngữ cảnh."""
        async with self._lock:
            found = False
            if session_id in self._sessions:
                del self._sessions[session_id]
                found = True
            if session_id in self._session_history:
                del self._session_history[session_id]
                found = True
            if session_id in self._session_account_map:
                del self._session_account_map[session_id]
                found = True
            return found

    async def deep_research(self, topic: str) -> Dict[str, Any]:
        """
        Kích hoạt tính năng Deep Research của Google Gemini Web với Failover.
        """
        async def _call(wrapper: GeminiClientWrapper, client: GeminiClient):
            result = await client.deep_research(topic)
            return {
                "topic": topic,
                "account_id": wrapper.config.id,
                "result": getattr(result, "text", str(result)),
            }

        return await self._execute_with_failover("deep_research", _call)


# Global singleton instance
bridge = GeminiWebBridge()
