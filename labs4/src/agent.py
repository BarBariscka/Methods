"""Определение SmolAgents агента с поддержкой MCP инструментов."""
import os
import json
import asyncio
from typing import Optional

import httpx
from smolagents import CodeAgent, Tool


def create_mcp_tool(mcp_url: str, tool_name: str, tool_description: str) -> Tool:
    """Создает SmolAgents Tool из MCP инструмента.

    В smolagents >= 1.24 инструменты создаются как подклассы Tool
    (через Tool.from_code), а не конструктором с аргументами.
    """
    tool_code = f'''
import httpx
import asyncio
from smolagents import Tool


class McpTool(Tool):
    name = "{tool_name}"
    description = """{tool_description}"""
    inputs = {{
        "input_text": {{
            "type": "string",
            "description": "Входные данные для инструмента в свободной форме"
        }}
    }}
    output_type = "string"

    def forward(self, input_text: str) -> str:
        async def async_call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "{mcp_url}/tools/{tool_name}/invoke",
                    json={{"input": input_text}},
                    headers={{"Content-Type": "application/json"}},
                )
                response.raise_for_status()
                result = response.json()
                return str(result.get("content", result))

        return asyncio.run(async_call())
'''
    return Tool.from_code(tool_code)


def get_mcp_tools(mcp_urls: Optional[str]):
    """Получает список инструментов из MCP серверов."""
    tools = []
    
    if not mcp_urls:
        return tools
    
    # Для упрощения, создаем базовые инструменты
    # В реальности нужно получать список инструментов через MCP протокол
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


def create_smolagents_agent(mcp_urls: Optional[str] = None):
    """Создает SmolAgents агента с инструментами."""
    from smolagents import LiteLLMModel

    # Модель через LiteLLM (нативная интеграция smolagents)
    model = LiteLLMModel(
        model_id=os.getenv("LLM_MODEL", "ollama_chat/llama3.2"),
        api_base=os.getenv("LLM_API_BASE"),
        api_key=os.getenv("LLM_API_KEY", "dummy"),
    )

    # Получаем инструменты из MCP
    tools = get_mcp_tools(mcp_urls)

    # Системный промпт
    system_prompt = os.getenv(
        "AGENT_SYSTEM_PROMPT",
        "Ты полезный AI-ассистент. Используй доступные инструменты для решения задач пользователя."
    )

    # Создаем агента (в smolagents >= 1.24: max_steps вместо max_iterations,
    # кастомный промпт передаётся через instructions)
    agent = CodeAgent(
        tools=tools,
        model=model,
        instructions=system_prompt,
        additional_authorized_imports=["math", "json"],
        max_steps=15,
    )

    return agent


