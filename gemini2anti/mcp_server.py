"""
MCP Server (Model Context Protocol) cho Google Gemini Web (gemini.google.com/app).
Tích hợp trực tiếp vào Antigravity IDE và Antigravity CLI (agy).
"""

import sys
import json
import logging
from typing import Optional
try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    from mcp.server.mcpserver import MCPServer as FastMCP

from gemini2anti.client import bridge

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiWebMCP")

mcp = FastMCP(
    name="gemini-web",
    instructions="Cầu nối tích hợp trực tiếp các model AI từ Google Gemini Web (gemini.google.com/app) vào Antigravity / agy"
)


@mcp.tool()
async def gemini_web_ask(
    prompt: str,
    model: str = "gemini-4",
    extended_thinking: bool = True
) -> str:
    """
    Gửi câu hỏi hoặc yêu cầu trực tiếp đến Google Gemini Web (gemini.google.com/app).
    Mặc định sử dụng model Gemini 4 High (Gemini 4 Argon kèm Extended Thinking suy luận sâu cao nhất).
    
    Args:
        prompt: Nội dung câu hỏi, prompt hoặc tài liệu cần phân tích.
        model: Tên model Gemini Web ('gemini-4' (mặc định - Gemini 4 Argon), 'gemini-flash', 'gemini-pro', 'auto').
        extended_thinking: Bật chế độ suy nghĩ mở rộng (Gemini Extended Thinking). Mặc định luôn là True (Gemini 4 High).
    
    Returns:
        Câu trả lời hoàn chỉnh từ Gemini Web kèm danh sách ảnh (nếu có).
    """
    try:
        res = await bridge.generate(prompt=prompt, model=model, extended_thinking=extended_thinking)
        text = res.get("text", "")
        images = res.get("images", [])
        if images:
            text += "\n\n**Ảnh đính kèm từ Gemini:**\n" + "\n".join([f"- {url}" for url in images])
        return text
    except Exception as e:
        logger.error(f"Lỗi khi gọi gemini_web_ask: {e}")
        return f"Lỗi kết nối Gemini Web: {str(e)}"


@mcp.tool()
async def gemini_web_chat(
    message: str,
    session_id: str = "default",
    model: str = "gemini-4",
    extended_thinking: bool = True
) -> str:
    """
    Trò chuyện nhiều lượt liên tục (Multi-turn Conversation) với Gemini Web.
    Mặc định sử dụng model Gemini 4 High (Gemini 4 Argon kèm Extended Thinking).
    Trạng thái ngữ cảnh hội thoại được lưu theo session_id.
    
    Args:
        message: Tin nhắn mới gửi cho Gemini Web.
        session_id: Định danh phiên trò chuyện (ví dụ: 'debug_task_1', 'review_code'). Mặc định là 'default'.
        model: Tên model Gemini Web ('gemini-4', 'gemini-flash', 'gemini-pro', 'auto').
        extended_thinking: Bật chế độ suy nghĩ mở rộng (Extended Thinking). Mặc định luôn là True (Gemini 4 High).
        
    Returns:
        Câu trả lời của Gemini Web trong phiên hội thoại.
    """
    try:
        res = await bridge.chat(message=message, session_id=session_id, model=model, extended_thinking=extended_thinking)
        text = res.get("text", "")
        images = res.get("images", [])
        if images:
            text += "\n\n**Ảnh đính kèm:**\n" + "\n".join([f"- {url}" for url in images])
        return text
    except Exception as e:
        logger.error(f"Lỗi khi gọi gemini_web_chat: {e}")
        return f"Lỗi phiên chat Gemini Web: {str(e)}"


@mcp.tool()
async def gemini_web_deep_research(topic: str) -> str:
    """
    Kích hoạt tính năng Deep Research từ tài khoản Google Gemini Web để nghiên cứu chuyên sâu về một đề tài phức tạp.
    
    Args:
        topic: Chủ đề hoặc bài toán cần Gemini Web nghiên cứu đa nguồn.
        
    Returns:
        Báo cáo kết quả nghiên cứu chi tiết từ Google Gemini.
    """
    try:
        res = await bridge.deep_research(topic=topic)
        return res.get("result", "")
    except Exception as e:
        logger.error(f"Lỗi khi chạy deep_research: {e}")
        return f"Lỗi Deep Research: {str(e)}"


@mcp.tool()
async def gemini_web_account_info() -> str:
    """
    Kiểm tra trạng thái Multi-Account Cookie Pool: quota còn lại, thời gian reset, danh sách model khả dụng, nguồn cookie và danh sách từng tài khoản trong pool.
    
    Returns:
        Bản tóm tắt JSON định dạng đẹp về tình trạng Multi-Account Pool và từng tài khoản.
    """
    try:
        status = await bridge.get_status(check_all=True)
        return json.dumps(status, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Lỗi kiểm tra thông tin tài khoản: {str(e)}"


@mcp.tool()
async def gemini_web_reset_session(session_id: str = "default") -> str:
    """
    Xóa lịch sử một phiên chat với Gemini Web để bắt đầu lại ngữ cảnh mới.
    
    Args:
        session_id: Tên phiên chat cần xóa.
    """
    success = await bridge.reset_session(session_id=session_id)
    if success:
        return f"Đã xóa thành công phiên chat '{session_id}'."
    return f"Không tìm thấy phiên chat '{session_id}' hoặc phiên đã trống."


def main():
    """Hàm khởi chạy MCP Server qua stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
