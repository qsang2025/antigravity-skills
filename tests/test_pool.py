"""
Unit tests cho Multi-Account Cookie Pool và Automatic Failover trong McpGemini2Antigravity.
"""

import os
import time
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gemini_webapi.exceptions import (
    AuthError,
    UsageLimitExceededError,
    TemporarilyBlockedError,
)

from gemini2anti.config import (
    GeminiAccountConfig,
    get_gemini_account_pool,
    get_gemini_credentials,
)
from gemini2anti.client import (
    AccountStatus,
    GeminiClientWrapper,
    AccountPoolManager,
    GeminiWebBridge,
)


class TestMultiAccountPool(unittest.IsolatedAsyncioTestCase):
    """Kiểm thử Multi-Account Pool: Cấu hình, Vòng đời và Tự động Failover."""

    def setUp(self):
        # Lưu bản sao biến môi trường để phục hồi sau mỗi test
        self._orig_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_single_account_backward_compatibility(self):
        """Kiểm thử tính tương thích ngược 100% với cấu hình đơn tài khoản truyền thống."""
        # Xóa các biến đánh số nếu có
        for k in list(os.environ.keys()):
            if k.startswith("GEMINI_SECURE_1PSID"):
                del os.environ[k]

        os.environ["GEMINI_SECURE_1PSID"] = "psid_single_test_12345"
        os.environ["GEMINI_SECURE_1PSIDTS"] = "psidts_single_test"
        os.environ["GEMINI_SECURE_1PSIDCC"] = "psidcc_single_test"
        os.environ["GEMINI_ACCOUNT_NAME"] = "Single Account"

        pool = get_gemini_account_pool(include_browser=False)
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool[0].id, "account_default")
        self.assertEqual(pool[0].name, "Single Account")
        self.assertEqual(pool[0].psid, "psid_single_test_12345")
        self.assertEqual(pool[0].masked_psid(), "psid_s...2345")

        creds = get_gemini_credentials()
        self.assertEqual(len(creds), 4)
        self.assertEqual(creds[0], "psid_single_test_12345")
        self.assertEqual(creds[1], "psidts_single_test")
        self.assertEqual(creds[2], "psidcc_single_test")
        self.assertEqual(creds[3], "env:GEMINI_SECURE_1PSID")

    def test_multi_account_numbered_env_and_deduplication(self):
        """Kiểm thử trích xuất biến môi trường đánh số _1.._N và cơ chế khử trùng lặp PSID."""
        for k in list(os.environ.keys()):
            if k.startswith("GEMINI_SECURE_1PSID"):
                del os.environ[k]

        # Cấu hình tài khoản mặc định và 3 tài khoản phụ
        os.environ["GEMINI_SECURE_1PSID"] = "psid_shared_key_11111"
        os.environ["GEMINI_SECURE_1PSIDTS"] = ""
        os.environ["GEMINI_ACCOUNT_NAME"] = "Primary"

        # Account _1 có cùng psid với primary nhưng có psidts -> phải được merge, không tạo duplicate
        os.environ["GEMINI_SECURE_1PSID_1"] = "psid_shared_key_11111"
        os.environ["GEMINI_SECURE_1PSIDTS_1"] = "psidts_enriched_11111"

        # Account _2 và _3 có psid khác biệt
        os.environ["GEMINI_SECURE_1PSID_2"] = "psid_unique_key_22222"
        os.environ["GEMINI_SECURE_1PSID_3"] = "psid_unique_key_33333"

        pool = get_gemini_account_pool(include_browser=False)
        self.assertEqual(len(pool), 3)

        # Kiểm tra tài khoản 1 đã được merge psidts
        self.assertEqual(pool[0].psid, "psid_shared_key_11111")
        self.assertEqual(pool[0].psidts, "psidts_enriched_11111")

        # Kiểm tra thứ tự các tài khoản tiếp theo
        self.assertEqual(pool[1].psid, "psid_unique_key_22222")
        self.assertEqual(pool[2].psid, "psid_unique_key_33333")

    def test_account_lifecycle_and_auto_recovery(self):
        """Kiểm thử vòng đời tài khoản: ACTIVE -> RATE_LIMITED -> Tự hồi phục ACTIVE khi hết cooldown."""
        cfg = GeminiAccountConfig(id="acc_test", name="Test Account", psid="psid_lifecycle_12345")
        wrapper = GeminiClientWrapper(config=cfg)

        self.assertEqual(wrapper.status, AccountStatus.ACTIVE)

        # Đánh dấu RATE_LIMITED với cooldown 10 giây
        now = time.time()
        wrapper.status = AccountStatus.RATE_LIMITED
        wrapper.cooldown_until = now + 10

        # Kiểm tra khi chưa hết thời gian cooldown
        recovered = wrapper.check_and_recover(now=now + 5)
        self.assertFalse(recovered)
        self.assertEqual(wrapper.status, AccountStatus.RATE_LIMITED)

        # Kiểm tra khi đã quá thời gian cooldown
        recovered = wrapper.check_and_recover(now=now + 11)
        self.assertTrue(recovered)
        self.assertEqual(wrapper.status, AccountStatus.ACTIVE)
        self.assertIsNone(wrapper.cooldown_until)

    async def test_failover_on_generate_rate_limit_and_auth_error(self):
        """
        Kiểm thử Automatic Failover cho generate():
        - Tài khoản 1 gặp lỗi Rate Limit (UsageLimitExceededError)
        - Tài khoản 2 gặp lỗi Auth (AuthError)
        - Tài khoản 3 thành công
        """
        bridge = GeminiWebBridge()
        
        cfg1 = GeminiAccountConfig(id="acc_1", name="Acc 1", psid="psid_1_123456789")
        cfg2 = GeminiAccountConfig(id="acc_2", name="Acc 2", psid="psid_2_123456789")
        cfg3 = GeminiAccountConfig(id="acc_3", name="Acc 3", psid="psid_3_123456789")

        w1 = GeminiClientWrapper(config=cfg1)
        w2 = GeminiClientWrapper(config=cfg2)
        w3 = GeminiClientWrapper(config=cfg3)

        bridge.pool._wrappers = [w1, w2, w3]
        bridge.pool._current_index = 0

        # Mock client cho từng tài khoản
        mock_client_1 = AsyncMock()
        mock_client_1.resolve_model = MagicMock(return_value="gemini-argon")
        mock_client_1.generate_content.side_effect = UsageLimitExceededError("Rate limit 429: Usage limit exceeded")

        mock_client_2 = AsyncMock()
        mock_client_2.resolve_model = MagicMock(return_value="gemini-argon")
        mock_client_2.generate_content.side_effect = AuthError("Auth error 401: Cookie expired or invalid")

        mock_client_3 = AsyncMock()
        mock_client_3.resolve_model = MagicMock(return_value="gemini-argon")
        mock_resp = MagicMock()
        mock_resp.text = "Phản hồi thành công từ Tài khoản 3!"
        mock_resp.images = []
        mock_resp.thoughts = None
        mock_client_3.generate_content.return_value = mock_resp

        async def fake_init(wrapper, force_refresh=False):
            if wrapper.config.id == "acc_1":
                wrapper.client = mock_client_1
            elif wrapper.config.id == "acc_2":
                wrapper.client = mock_client_2
            elif wrapper.config.id == "acc_3":
                wrapper.client = mock_client_3
            wrapper.initialized = True
            wrapper.status = AccountStatus.ACTIVE
            return wrapper.client

        with patch.object(bridge, "_init_wrapper_client", side_effect=fake_init):
            res = await bridge.generate(prompt="Xin chào Gemini")

            # Kiểm tra kết quả trả về từ Tài khoản 3
            self.assertEqual(res["text"], "Phản hồi thành công từ Tài khoản 3!")
            self.assertEqual(res["account_id"], "acc_3")

            # Kiểm tra trạng thái các tài khoản trong pool sau failover
            self.assertEqual(w1.status, AccountStatus.RATE_LIMITED)
            self.assertIsNotNone(w1.cooldown_until)
            self.assertEqual(w2.status, AccountStatus.AUTH_ERROR)
            self.assertEqual(w3.status, AccountStatus.ACTIVE)

    async def test_failover_on_generate_stream(self):
        """
        Kiểm thử Automatic Failover cho generate_stream() khi tài khoản đầu tiên bị lỗi 429
        ngay khi bắt đầu stream.
        """
        bridge = GeminiWebBridge()
        
        cfg1 = GeminiAccountConfig(id="acc_s1", name="Stream 1", psid="psid_s1_1234567")
        cfg2 = GeminiAccountConfig(id="acc_s2", name="Stream 2", psid="psid_s2_1234567")

        w1 = GeminiClientWrapper(config=cfg1)
        w2 = GeminiClientWrapper(config=cfg2)

        bridge.pool._wrappers = [w1, w2]
        bridge.pool._current_index = 0

        # Acc 1 ném exception khi gọi stream
        mock_client_1 = MagicMock()
        mock_client_1.generate_content_stream.side_effect = TemporarilyBlockedError("Temporarily blocked 429")

        # Acc 2 stream 2 chunks
        mock_client_2 = MagicMock()
        async def mock_stream_gen(**kwargs):
            chunk1 = MagicMock()
            chunk1.text = "Chào "
            yield chunk1
            chunk2 = MagicMock()
            chunk2.text = "Chào bạn!"
            yield chunk2

        mock_client_2.generate_content_stream = mock_stream_gen

        async def fake_init(wrapper, force_refresh=False):
            if wrapper.config.id == "acc_s1":
                wrapper.client = mock_client_1
            else:
                wrapper.client = mock_client_2
            wrapper.initialized = True
            wrapper.status = AccountStatus.ACTIVE
            return wrapper.client

        with patch.object(bridge, "_init_wrapper_client", side_effect=fake_init):
            chunks = []
            async for delta in bridge.generate_stream(prompt="Stream test"):
                chunks.append(delta)

            full_text = "".join(chunks)
            self.assertEqual(full_text, "Chào bạn!")
            self.assertEqual(w1.status, AccountStatus.RATE_LIMITED)
            self.assertEqual(w2.status, AccountStatus.ACTIVE)

    async def test_failover_on_chat_session_continuity(self):
        """
        Kiểm thử duy trì ngữ cảnh chat() khi xảy ra Failover sang tài khoản mới.
        """
        bridge = GeminiWebBridge()

        cfg1 = GeminiAccountConfig(id="acc_c1", name="Chat 1", psid="psid_c1_1234567")
        cfg2 = GeminiAccountConfig(id="acc_c2", name="Chat 2", psid="psid_c2_1234567")

        w1 = GeminiClientWrapper(config=cfg1)
        w2 = GeminiClientWrapper(config=cfg2)

        bridge.pool._wrappers = [w1, w2]
        bridge.pool._current_index = 0

        # Lượt 1: Acc 1 chat thành công
        chat_sess_1 = AsyncMock()
        resp1 = MagicMock()
        resp1.text = "Tôi là AI hỗ trợ."
        resp1.images = []
        chat_sess_1.send_message.return_value = resp1

        mock_client_1 = MagicMock()
        mock_client_1.resolve_model = MagicMock(return_value="gemini-argon")
        mock_client_1.start_chat.return_value = chat_sess_1

        # Lượt 2: Acc 1 ném UsageLimitExceededError
        chat_sess_2 = AsyncMock()
        resp2 = MagicMock()
        resp2.text = "Đã nhận ngữ cảnh trước và sẵn sàng tiếp tục!"
        resp2.images = []
        chat_sess_2.send_message.return_value = resp2

        mock_client_2 = MagicMock()
        mock_client_2.resolve_model = MagicMock(return_value="gemini-argon")
        mock_client_2.start_chat.return_value = chat_sess_2

        async def fake_init(wrapper, force_refresh=False):
            if wrapper.config.id == "acc_c1":
                wrapper.client = mock_client_1
            else:
                wrapper.client = mock_client_2
            wrapper.initialized = True
            wrapper.status = AccountStatus.ACTIVE
            return wrapper.client

        with patch.object(bridge, "_init_wrapper_client", side_effect=fake_init):
            # Lượt 1
            res1 = await bridge.chat("Xin chào", session_id="session_test")
            self.assertEqual(res1["text"], "Tôi là AI hỗ trợ.")
            self.assertEqual(res1["account_id"], "acc_c1")

            # Lượt 2: Cho Acc 1 ném lỗi
            chat_sess_1.send_message.side_effect = UsageLimitExceededError("Quota exhausted on Acc 1")

            res2 = await bridge.chat("Bạn có thể giúp tôi viết code không?", session_id="session_test")
            self.assertEqual(res2["text"], "Đã nhận ngữ cảnh trước và sẵn sàng tiếp tục!")
            self.assertEqual(res2["account_id"], "acc_c2")

            # Kiểm tra chat_sess_2 nhận được prompt có chứa lịch sử ngữ cảnh trước đó
            called_prompt = chat_sess_2.send_message.call_args[1]["prompt"]
            self.assertIn("[Previous conversation context]", called_prompt)
            self.assertIn("Xin chào", called_prompt)
            self.assertIn("Tôi là AI hỗ trợ.", called_prompt)
            self.assertIn("Bạn có thể giúp tôi viết code không?", called_prompt)

    async def test_all_accounts_exhausted_raises_error(self):
        """Kiểm thử khi toàn bộ tài khoản trong pool đều lỗi thì ném ngoại lệ rõ ràng."""
        bridge = GeminiWebBridge()
        cfg = GeminiAccountConfig(id="acc_fail", name="Acc Fail", psid="psid_fail_12345")
        w = GeminiClientWrapper(config=cfg)
        bridge.pool._wrappers = [w]

        mock_client = AsyncMock()
        mock_client.resolve_model = MagicMock(return_value="gemini-argon")
        mock_client.generate_content.side_effect = UsageLimitExceededError("Rate limit on all")

        async def fake_init(wrapper, force_refresh=False):
            wrapper.client = mock_client
            wrapper.initialized = True
            return wrapper.client

        with patch.object(bridge, "_init_wrapper_client", side_effect=fake_init):
            with self.assertRaises(RuntimeError) as ctx:
                await bridge.generate("Hello")
            self.assertIn("Toàn bộ 1 tài khoản trong pool đã thất bại", str(ctx.exception))

    async def test_concurrent_requests_thread_safety(self):
        """Kiểm thử an toàn đồng thời (Thread Safety) khi nhiều request đồng loạt gửi tới."""
        bridge = GeminiWebBridge()
        cfg1 = GeminiAccountConfig(id="acc_conc_1", name="Conc 1", psid="psid_conc_1")
        cfg2 = GeminiAccountConfig(id="acc_conc_2", name="Conc 2", psid="psid_conc_2")

        w1 = GeminiClientWrapper(config=cfg1)
        w2 = GeminiClientWrapper(config=cfg2)
        bridge.pool._wrappers = [w1, w2]

        mock_client_1 = AsyncMock()
        mock_client_1.resolve_model = MagicMock(return_value="gemini-argon")
        resp = MagicMock()
        resp.text = "Concurrent OK"
        resp.images = []
        resp.thoughts = None
        mock_client_1.generate_content.return_value = resp

        async def fake_init(wrapper, force_refresh=False):
            wrapper.client = mock_client_1
            wrapper.initialized = True
            return wrapper.client

        with patch.object(bridge, "_init_wrapper_client", side_effect=fake_init):
            tasks = [bridge.generate(f"Prompt {i}") for i in range(10)]
            results = await asyncio.gather(*tasks)
            self.assertEqual(len(results), 10)
            self.assertTrue(all(r["text"] == "Concurrent OK" for r in results))


if __name__ == "__main__":
    unittest.main()
