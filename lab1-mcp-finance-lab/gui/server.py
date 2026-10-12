"""GUI-сервер для MCP Finance: веб-интерфейс поверх MCP-инструментов.

Раздаёт статический фронтенд и проксирует вызовы инструментов на MCP-сервер
(по умолчанию http://localhost:8000/mcp), скрывая детали JSON-RPC/сессий.
"""

import json
import os

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")
GUI_HOST = os.getenv("GUI_HOST", "127.0.0.1")
GUI_PORT = int(os.getenv("GUI_PORT", "8080"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "static", "index.html")

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _parse_sse(text: str) -> list:
    """Извлекает JSON-события из SSE-потока FastMCP."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            try:
                events.append(json.loads(line[5:].strip()))
            except json.JSONDecodeError:
                pass
    return events


async def _rpc(client: httpx.AsyncClient, session_id, method, params=None, msg_id=None):
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    if msg_id is not None:
        body["id"] = msg_id
    headers = dict(HEADERS)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    resp = await client.post(MCP_URL, json=body, headers=headers)
    resp.raise_for_status()
    return resp


async def call_tool(tool: str, arguments: dict) -> dict:
    """Полный цикл MCP-вызова: initialize -> initialized -> tools/call."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await _rpc(
            client,
            None,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "mcp-finance-gui", "version": "1.0"},
            },
            msg_id=1,
        )
        session_id = resp.headers.get("mcp-session-id", "")
        await _rpc(client, session_id, "notifications/initialized")
        resp = await _rpc(
            client,
            session_id,
            "tools/call",
            {"name": tool, "arguments": arguments},
            msg_id=2,
        )

    for event in _parse_sse(resp.text):
        if event.get("id") == 2:
            result = event.get("result", {})
            if result.get("isError"):
                text = ""
                for item in result.get("content", []):
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        break
                return {"ok": False, "error": text or "Ошибка вызова инструмента"}

            structured = result.get("structuredContent") or result.get("structured_content")
            # FastMCP кладёт в structuredContent сам ToolResult: {content, structured_content, meta}
            if isinstance(structured, dict) and "structured_content" in structured:
                structured = structured["structured_content"]
            if structured:
                return {"ok": True, "data": structured}

            # Fallback: текстовое содержимое (иногда это вложенный JSON)
            for item in result.get("content", []):
                if item.get("type") == "text":
                    raw = item.get("text", "")
                    try:
                        return {"ok": True, "data": json.loads(raw)}
                    except (json.JSONDecodeError, TypeError):
                        return {"ok": True, "data": {"raw_text": raw}}

    return {"ok": False, "error": "Пустой ответ от MCP-сервера"}


async def index(_request):
    return FileResponse(INDEX_PATH)


async def calc(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Некорректный JSON"}, status_code=400)

    tool = payload.get("tool", "")
    arguments = payload.get("arguments", {})
    if not tool:
        return JSONResponse({"ok": False, "error": "Не указан инструмент"}, status_code=400)

    try:
        result = await call_tool(tool, arguments)
    except httpx.HTTPError as e:
        return JSONResponse(
            {"ok": False, "error": f"MCP-сервер недоступен ({MCP_URL}): {e}"},
            status_code=502,
        )
    return JSONResponse(result)


async def health(_request):
    return JSONResponse({"status": "ok", "mcp_url": MCP_URL})


app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/calc", calc, methods=["POST"]),
        Route("/health", health),
    ]
)


def main():
    print("=" * 60)
    print("🖥  MCP FINANCE GUI")
    print("=" * 60)
    print(f"🌐 Интерфейс:  http://{GUI_HOST}:{GUI_PORT}")
    print(f"🔌 MCP-сервер: {MCP_URL}")
    print("=" * 60)
    uvicorn.run(app, host=GUI_HOST, port=GUI_PORT, log_level="warning")


if __name__ == "__main__":
    main()
