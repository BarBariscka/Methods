# Evo AI Labs — Unified GUI

Единый веб-интерфейс для лабораторных 1-4.

## Быстрый старт

```bash
cd gui
pip install -r requirements.txt
python server.py
```

Откройте http://127.0.0.1:8080 в браузере.

## Вкладки

| Вкладка | Лабораторная | Протокол | Описа |
|---------|-------------|----------|-------|
| Lab 1 — MCP Finance | lab1-mcp-finance-lab | MCP (JSON-RPC) | Финансовые калькуляторы: кредиты, вклады, инвестиции |
| Lab 2 — ADK Agent | lab2-adk-agent | A2A | Google ADK агент с MCP инструментами |
| Lab 3 — LangChain | lab3-langchain-agent | A2A | LangChain агент с MCP инструментами |
| Lab 4 — SmolAgents | lab4-smolagents-agent | A2A | HuggingFace SmolAgents агент |

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `GUI_PORT` | `8080` | Порт GUI сервера |
| `GUI_HOST` | `127.0.0.1` | Хост GUI сервера |
| `MCP_URL` | `http://localhost:8000/mcp` | URL MCP сервера (Lab 1) |
| `LAB2_URL` | `http://localhost:10000` | URL ADK агента |
| `LAB3_URL` | `http://localhost:10001` | URL LangChain агента |
| `LAB4_URL` | `http://localhost:10002` | URL SmolAgents агента |

## Запуск полного стека

```bash
# Terminal 1: MCP Server (Lab 1)
cd lab1-mcp-finance-lab
uv run python src/server.py

# Terminal 2: ADK Agent (Lab 2)
cd lab2-adk-agent
MCP_URL=http://localhost:8000/sse PORT=10000 uv run python src/start_a2a.py

# Terminal 3: LangChain Agent (Lab 3)
cd lab3-langchain-agent
MCP_URL=http://localhost:8000/mcp PORT=10001 uv run python src/start_a2a.py

# Terminal 4: SmolAgents (Lab 4)
cd lab4-smolagents-agent
MCP_URL=http://localhost:8000/mcp PORT=10002 uv run python src/start_a2a.py

# Terminal 5: GUI
cd gui
python server.py
```
