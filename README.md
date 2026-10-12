# Evo AI Agents Labs — локальная среда

Лабораторный практикум по AI-агентам: MCP, A2A, A2UI, LLM-агенты и боты-интеграторы.
Реальные темы и каталоги лабораторных — в [LABS.md](LABS.md) и [ASSIGNMENTS.md](ASSIGNMENTS.md).

> **Репозиторий:** https://github.com/Voyager7777/evo-ai-agents-labs

## Быстрый старт

### 1. Требования

- Docker 24+, Docker Compose 2.20+
- 16 GB RAM (минимум), 50 GB свободного места

### 2. Развёртывание

```bash
cp .env.example .env      # отредактируйте .env (токены Telegram/Mattermost)

# Запуск нужной лабораторной (профили):
docker compose -f docker-compose.local.yaml --profile lab1  up -d --build   # MCP-сервер (Python)
docker compose -f docker-compose.local.yaml --profile lab2  up -d --build   # ADK-агент + A2A
docker compose -f docker-compose.local.yaml --profile lab3  up -d --build   # LangChain-агент + A2A
docker compose -f docker-compose.local.yaml --profile lab4  up -d --build   # Smolagents-агент + A2A
docker compose -f docker-compose.local.yaml --profile lab5  up -d --build   # CrewAI-агент + A2A
docker compose -f docker-compose.local.yaml --profile lab6  up -d --build   # Strands-агент + A2A
docker compose -f docker-compose.local.yaml --profile lab7  up -d --build   # Mattermost-бот
docker compose -f docker-compose.local.yaml --profile lab8  up -d --build   # Telegram-бот
docker compose -f docker-compose.local.yaml --profile lab9  up -d --build   # MCP-сервер (Go)
docker compose -f docker-compose.local.yaml --profile lab10 up -d --build   # A2UI-рендерер

# LLM-инфраструктура (нужна агентам лаб. 2–6):
docker compose -f docker-compose.local.yaml up -d ollama
docker exec -it pis-ollama ollama pull llama3.2

# Настройка Ollama (опционально):
#   Модель по умолчанию — llama3.2 (~2 ГБ). Другие: `ollama pull qwen2.5:7b` и т.п.
#   Порт/хост задаются переменными OLLAMA_HOST (по умолчанию 0.0.0.0:11434).
#   Автовыгрузка модели из памяти: OLLAMA_KEEP_ALIVE=10m (по умолчанию 5m).
#   Параллельные запросы: OLLAMA_NUM_PARALLEL=2.
#   Для контейнера — через environment в docker-compose.local.yaml (сервис ollama).
#   Проверка: curl http://localhost:11434/api/tags ; тест: curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"привет","stream":false}'
#   Нативный запуск (без Docker): установите Ollama с ollama.com, затем `ollama serve` и `ollama pull llama3.2`.

# Проверка доступности сервисов:
./check.sh          # bash / Git Bash
.\check.ps1         # PowerShell
```

### 3. Остановка

```bash
docker compose -f docker-compose.local.yaml down            # остановить всё
docker compose -f docker-compose.local.yaml down -v         # с очисткой volumes
```

## Сервисы и порты

| Сервис | Каталог | Порт хоста | Описание |
|--------|---------|-----------|----------|
| Ollama | — | 11434 | LLM (llama3.2) |
| Lab 1: lab1-mcp-server | `lab1-mcp-finance-lab/` | 8000 | MCP-сервер фин. инструментов (FastMCP, Python) |
| Lab 2: lab2-adk-agent | `lab2-adk-agent/` | 8002 | ADK-агент + A2A-сервер |
| Lab 3: lab3-langchain-agent | `lab3-langchain-agent/` | 8003 | LangChain-агент + A2A-сервер |
| Lab 4: lab4-smolagents-agent | `lab4-smolagents-agent/` | 8004 | Smolagents-агент + A2A-сервер |
| Lab 5: lab5-crewai-agent | `lab5-crewai-agent/` | 8005 | CrewAI-агент + A2A-сервер |
| Lab 6: lab6-strands-agent | `lab6-strands-agent/` | 8006 | Strands-агент (meta-tools) + A2A-сервер |
| Lab 7: lab7-mattermost-bot | `lab7-mattermost-bot-for-agents/` | — (outbound) | Mattermost-бот → A2A + OTel |
| Lab 8: lab8-telegram-bot | `lab8-telegram-bot-for-agents/` | — (long-polling) | Telegram-бот → A2A |
| Lab 9: lab9-mcp-server-go | `lab9-mcp-finance-go/` | 8100 | MCP-сервер фин. инструментов (Go) |
| Lab 10: lab10-a2ui-renderer | `lab10-a2a-a2ui-renderer/` | 3000 | A2UI-рендерер (React + nginx) |

Агенты лаб. 2–6 внутри контейнера слушают `$PORT` (по умолчанию 10000); проброс на хост — см. таблицу.
Переменные агентов: `MCP_URL` (адрес MCP-сервера, напр. `http://host.docker.internal:8000/mcp`), `LLM_API_KEY`, `LLM_API_BASE` (по умолчанию `https://foundation-models.api.cloud.ru/v1`), `LLM_MODEL`, `OTEL_EXPORTER_OTLP_ENDPOINT`.
Для локального Ollama: `LLM_API_BASE=http://host.docker.internal:11434/v1`, `LLM_API_KEY=dummy`.

## Типовая связка (лаб. 1 + 3 + 10)

```bash
# 1. MCP-сервер
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build
# 2. Агент (в .env/compose укажите MCP_URL=http://host.docker.internal:8000/mcp)
docker compose -f docker-compose.local.yaml --profile lab3 up -d --build
# 3. Фронтенд
docker compose -f docker-compose.local.yaml --profile lab10 up -d --build
# затем в http://localhost:3000 укажите URL агента: http://localhost:8003
```

## Управление

```bash
# Логи
docker compose -f docker-compose.local.yaml logs -f lab1-mcp-server

# Статус
docker compose -f docker-compose.local.yaml ps

# Перезапуск сервиса
docker compose -f docker-compose.local.yaml restart lab1-mcp-server

# Зайти в контейнер
docker exec -it pis-lab1-mcp /bin/bash
```

## Тестирование

### Lab 1 / Lab 9: MCP-серверы

MCP по streamable HTTP требует JSON-RPC-сессию (`initialize` → `tools/list`). Проще всего проверить через инспектор:

```bash
npx @modelcontextprotocol/inspector   # UI; transport: HTTP, URL: http://localhost:8000/mcp
# Lab 9 (Go) — то же на http://localhost:8100/mcp
```

### Лабы 2–6: A2A-агенты

```bash
# Agent Card
curl -s http://localhost:8003/.well-known/agent-card.json
```

### Lab 10: A2UI-рендерер

Откройте http://localhost:3000 и укажите URL A2A-агента.

## Troubleshooting

- **Сервисы не запускаются** — `docker compose -f docker-compose.local.yaml logs`
- **Ollama не отвечает** — проверьте `docker exec -it pis-ollama ollama list`, при необходимости `pull llama3.2`
- **Telegram-бот не работает** — проверьте `TELEGRAM_BOT_TOKEN` в `.env`, затем `docker logs pis-lab8-tg-bot`
- **Mattermost-бот** — нужны `MATTERMOST_URL`, `MATTERMOST_TOKEN`, `A2A_BASE_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`
- **Агент не видит MCP-сервер** — из контейнера хост доступен как `host.docker.internal`, а сервисы compose — по именам (`http://lab1-mcp-server:8000/mcp`)

## Скрипты

- `.\check.ps1 [host]` (PowerShell) — проверка доступности сервисов (Ollama 11434, Lab 1 :8000, Lab 2–6 :8002–8006, Lab 9 :8100, Lab 10 :3000)

## Безопасность

- `.env` с токенами не коммитить (уже в `.gitignore`)
- Для production — внешние LLM/секреты, а не локальный Ollama

## Лицензия

MIT