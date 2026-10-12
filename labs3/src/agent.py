"""Определение LangChain агента с поддержкой MCP инструментов."""
import os
import asyncio
import json
import uuid
from typing import List, Optional, Dict
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
import httpx


class MCPClient:
    """JSON-RPC клиент для streamable-http MCP сервера."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self._initialized = False

    async def _ensure_session(self):
        """Инициализирует MCP-сессию при первом вызове."""
        if self._initialized:
            return
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Шаг 1: initialize
            resp = await client.post(
                self.base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "langchain-agent", "version": "1"},
                    },
                },
                headers={"Accept": "application/json, text/event-stream"},
            )
            resp.raise_for_status()
            self.session_id = resp.headers.get("mcp-session-id")
            # Шаг 2: notifications/initialized
            headers = {"Accept": "application/json, text/event-stream"}
            if self.session_id:
                headers["mcp-session-id"] = self.session_id
            await client.post(
                self.base_url,
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                headers=headers,
            )
            self._initialized = True

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Вызывает MCP-инструмент через JSON-RPC tools/call."""
        await self._ensure_session()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Accept": "application/json, text/event-stream",
                       "Content-Type": "application/json"}
            if self.session_id:
                headers["mcp-session-id"] = self.session_id
            resp = await client.post(
                self.base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 10,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                },
                headers=headers,
            )
            resp.raise_for_status()
            body = resp.text
            # Парсим SSE-ответ: строки вида "data: {...}"
            result = None
            for line in body.splitlines():
                if line.startswith("data: "):
                    try:
                        msg = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if msg.get("id") == 10:
                        result = msg
                        break
            if result is None:
                # Попробуем как обычный JSON
                result = json.loads(body)
            r = result.get("result", {})
            # structuredContent содержит результат в structured_content
            sc = r.get("structuredContent", {})
            if isinstance(sc, dict) and "structured_content" in sc:
                return json.dumps(sc["structured_content"], ensure_ascii=False)
            # Fallback: content[0].text
            content = r.get("content", [])
            if content:
                return content[0].get("text", str(content))
            return json.dumps(sc, ensure_ascii=False)


# Глобальный реестр MCP-клиентов (по одному на URL)
_MCP_CLIENTS: Dict[str, MCPClient] = {}


def _get_client(mcp_url: str) -> MCPClient:
    if mcp_url not in _MCP_CLIENTS:
        _MCP_CLIENTS[mcp_url] = MCPClient(mcp_url)
    return _MCP_CLIENTS[mcp_url]


def create_mcp_tool(mcp_url: str, tool_name: str, tool_description: str) -> Tool:
    """Создает LangChain Tool из MCP инструмента."""

    def mcp_tool_func(input_text: str) -> str:
        """Вызывает MCP инструмент через JSON-RPC."""
        async def async_call():
            client = _get_client(mcp_url)
            # Парсим input_text как JSON, если возможно, иначе передаём как строку
            try:
                args = json.loads(input_text)
                if not isinstance(args, dict):
                    args = {"input": input_text}
            except (json.JSONDecodeError, TypeError):
                args = {"input": input_text}
            return await client.call_tool(tool_name, args)

        return asyncio.run(async_call())

    return Tool(
        name=tool_name,
        description=tool_description,
        func=mcp_tool_func
    )


def get_mcp_tools(mcp_urls: Optional[str]) -> List[Tool]:
    """Получает список инструментов из MCP серверов."""
    tools = []
    
    if not mcp_urls:
        return tools
    
    # Для упрощения, создаем базовые инструменты
    # В реальности нужно получать список инструментов через MCP протокол
    # Здесь используем примеры инструментов из lab1
    for mcp_url in mcp_urls.split(','):
        mcp_url = mcp_url.strip()
        # Примеры инструментов из finance MCP
        tools.append(create_mcp_tool(
            mcp_url,
            "loan_schedule_annuity",
            "Расчет графика аннуитетного кредита. Принимает сумму кредита, годовую ставку в процентах и срок в месяцах."
        ))
        tools.append(create_mcp_tool(
            mcp_url,
            "loan_schedule_differential",
            "Расчет графика дифференцированного кредита. Принимает сумму кредита, годовую ставку в процентах и срок в месяцах."
        ))
        tools.append(create_mcp_tool(
            mcp_url,
            "deposit_schedule_compound",
            "Расчет графика вклада с капитализацией. Принимает начальную сумму, годовую ставку в процентах, срок в месяцах и ежемесячные взносы."
        ))
    
    return tools


def create_langchain_agent(mcp_urls: Optional[str] = None):
    """Создает LangChain агента с инструментами."""
    
    # Создаем LLM через LiteLLM для унификации
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        base_url=os.getenv("LLM_API_BASE"),
        api_key=os.getenv("LLM_API_KEY"),
        temperature=0.7,
    )
    
    # Получаем инструменты из MCP
    tools = get_mcp_tools(mcp_urls)
    
    # Системный промпт
    system_prompt = os.getenv(
        "AGENT_SYSTEM_PROMPT",
        "Ты полезный AI-ассистент. Используй доступные инструменты для решения задач пользователя."
    )
    
    # Создаем промпт для агента
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Создаем агента
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Создаем executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=15,
    )
    
    return agent_executor


