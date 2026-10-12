# Lab 4 — SmolAgents Agent (A2A)

Агент на базе **smolagents** (`CodeAgent`) с инструментами из MCP-сервера
(лаб. 1), публикующий A2A-интерфейс (`message/send`). LLM подключается через
`LiteLLMModel` (Ollama, OpenAI и др.).

## Переменные окружения

| Переменная | Назначение | Пример |
|---|---|---|
| `LLM_MODEL` | Модель в формате LiteLLM | `ollama_chat/llama3.2:3b` |
| `LLM_API_BASE` | Базовый URL LLM (без `/v1` для Ollama) | `http://localhost:11434` |
| `LLM_API_KEY` | Ключ API (для Ollama — любой) | `dummy` |
| `MCP_URL` | URL MCP-сервера (streamable-http) | `http://localhost:8000/mcp` |
| `PORT` | Порт A2A-сервера | `10000` |
| `URL_AGENT` | Публичный URL агента в AgentCard | `http://localhost:10000` |
| `AGENT_NAME` | Имя агента | `SmolAgents Agent` |
| `AGENT_SYSTEM_PROMPT` | Системный промпт | `Ты полезный AI-ассистент...` |

## Запуск локально (без Docker)

```bash
# 1. Поднять MCP-сервер (лаб. 1) на :8000
cd ../lab1-mcp-finance-lab && uv run python src/server.py

# 2. Запустить агента
cd ../lab4-smolagents-agent
MCP_URL=http://localhost:8000/mcp \
PORT=8004 \
LLM_API_KEY=dummy \
LLM_API_BASE=http://localhost:11434 \
LLM_MODEL=ollama_chat/llama3.2:3b \
uv run python src/start_a2a.py
```

> **Важно (Windows):** при наличии системного прокси задайте
> `NO_PROXY=localhost,127.0.0.1`, иначе запросы к MCP и LLM будут уходить в прокси.

## Запуск в Docker

### Сборка образа

```bash
docker build -t lab4-smolagents-agent .
```

### Запуск контейнера

```bash
docker run --rm -p 8004:10000 \
  -e MCP_URL=http://host.docker.internal:8000/mcp \
  -e LLM_API_BASE=http://host.docker.internal:11434 \
  -e LLM_MODEL=ollama_chat/llama3.2:3b \
  -e LLM_API_KEY=dummy \
  --add-host=host.docker.internal:host-gateway \
  lab4-smolagents-agent
```

### Через docker compose (рекомендуется)

Из корня репозитория:

```bash
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build
docker compose -f docker-compose.local.yaml up -d ollama
docker compose -f docker-compose.local.yaml --profile lab4 up -d --build
```

Агент будет доступен на `http://localhost:8004`.

## Проверка

```bash
# Agent Card
curl http://localhost:8004/.well-known/agent-card.json

# Запрос к агенту
curl -X POST http://localhost:8004/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","kind":"message","messageId":"m1","parts":[{"kind":"text","text":"2+2?"}]}}}'
```

## Структура

```
src/
├── agent.py              # SmolAgents CodeAgent и MCP-инструменты
├── a2a_wrapper.py        # Обёртка агента под A2A
├── agent_task_manager.py # AgentExecutor для A2A
└── start_a2a.py          # Точка входа (A2A-сервер)
```
