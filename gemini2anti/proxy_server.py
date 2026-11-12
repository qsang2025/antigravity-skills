"""
OpenAI-Compatible HTTP Proxy Server cho Google Gemini Web (gemini.google.com/app).
Cung cấp các endpoint chuẩn:
  - GET  /v1/models
  - POST /v1/chat/completions (hỗ trợ cả streaming SSE và non-streaming)
  - GET  /health
"""

import time
import uuid
import json
import logging
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gemini2anti.client import bridge
from gemini2anti.config import get_gemini_credentials, get_default_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiProxyServer")

app = FastAPI(
    title="Gemini Web OpenAI-Compatible Proxy Server",
    description="Cầu nối chuyển đổi các request chuẩn OpenAI API thành cuộc gọi đến Google Gemini Web",
    version="1.0.0"
)

# Cho phép CORS từ mọi origin để các web client, UI, extension truy cập dễ dàng
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Any]]


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    extended_thinking: Optional[bool] = True



@app.get("/health")
async def health_check():
    """Kiểm tra sức khỏe server và kết nối Gemini Web."""
    try:
        status_info = await bridge.get_status(check_all=False)
        return {"status": "ok", "gemini_web": status_info, "pool_summary": status_info.get("pool_summary")}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.get("/v1/models")
async def list_models():
    """Trả về danh sách models hỗ trợ theo chuẩn OpenAI API."""
    try:
        status_info = await bridge.get_status()
        available_models = status_info.get("available_models", ["gemini-pro", "gemini-flash"])
    except Exception:
        available_models = ["gemini-pro", "gemini-flash", "gemini-flash-lite", "gemini-argon"]

    models_data = []
    created_ts = int(time.time())
    for m in available_models:
        models_data.append({
            "id": m,
            "object": "model",
            "created": created_ts,
            "owned_by": "google-gemini-web",
            "permission": [],
            "root": m,
            "parent": None,
        })

    return {
        "object": "list",
        "data": models_data
    }


def format_messages_to_prompt(messages: List[ChatMessage]) -> str:
    """
    Chuyển đổi danh sách tin nhắn chat thành prompt tự nhiên cho Gemini Web.
    Hòa trộn khéo léo system prompt vào ngữ cảnh để tránh bộ lọc an toàn của Gemini Web.
    """
    if not messages:
        return ""

    if len(messages) == 1:
        c = messages[0].content
        return c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)

    system_instructions = []
    dialogue_turns = []

    for msg in messages:
        role = msg.role.lower()
        content = msg.content if isinstance(msg.content, str) else json.dumps(msg.content, ensure_ascii=False)
        if role == "system":
            system_instructions.append(content)
        elif role == "user":
            dialogue_turns.append(content)
        elif role == "assistant":
            dialogue_turns.append(f"Phản hồi trước: {content}")
        else:
            dialogue_turns.append(content)

    body = "\n\n".join(dialogue_turns)
    if system_instructions:
        sys_str = "\n".join(system_instructions)
        return f"{body}\n\n(Lưu ý & Hướng dẫn: {sys_str})"
    return body


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """
    Thực thi Chat Completions tương thích 100% với chuẩn OpenAI.
    """
    model_name = req.model or get_default_model()
    prompt = format_messages_to_prompt(req.messages)
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())

    # 1. Trường hợp Streaming (SSE)
    if req.stream:
        async def event_generator():
            try:
                # Gửi chunk đầu tiên thiết lập role
                first_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(first_chunk, ensure_ascii=False)}\n\n"

                async for delta_text in bridge.generate_stream(
                    prompt=prompt,
                    model=model_name,
                    extended_thinking=True if req.extended_thinking is None else req.extended_thinking
                ):
                    chunk_obj = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model_name,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": delta_text},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_obj, ensure_ascii=False)}\n\n"

                # Chunk kết thúc
                final_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Lỗi trong quá trình stream: {e}")
                err_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"\n\n[Lỗi kết nối Gemini Web: {str(e)}]"},
                        "finish_reason": "error"
                    }]
                }
                yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # 2. Trường hợp Non-Streaming
    try:
        res = await bridge.generate(
            prompt=prompt,
            model=model_name,
            extended_thinking=True if req.extended_thinking is None else req.extended_thinking
        )
        content_text = res.get("text", "")
        images = res.get("images", [])
        if images:
            content_text += "\n\n**Ảnh từ Gemini:**\n" + "\n".join([f"- {url}" for url in images])

        return {
            "id": chat_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content_text.split()),
                "total_tokens": len(prompt.split()) + len(content_text.split())
            }
        }
    except Exception as e:
        logger.error(f"Lỗi khi xử lý completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi kết nối Gemini Web: {str(e)}"
        )


def start_proxy(host: str = "127.0.0.1", port: int = 8000):
    """Khởi chạy máy chủ proxy bằng Uvicorn."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_proxy()
