# Lab 1 — MCP Finance Server (Python / FastMCP)

MCP-сервер с финансовыми инструментами (кредиты, вклады, инвестиции).
Транспорт по умолчанию — **streamable-http** (эндпоинт `/mcp`), также
поддерживается **SSE** (эндпоинт `/sse`).

## Инструменты

| Инструмент | Назначение |
|---|---|
| `loan_schedule_annuity` | График аннуитетного кредита |
| `loan_schedule_differential` | График дифференцированного кредита |
| `deposit_schedule_compound` | График вклада с капитализацией |
| `compare_loan_schedules` | Сравнение аннуитетного и дифференцированного кредитов |
| `investment_calculator` | Расчёт доходности инвестиций |

## Переменные окружения

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `PORT` | Порт сервера | `8000` |
| `MCP_TRANSPORT` | Транспорт: `streamable-http` или `sse` | `streamable-http` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## Запуск локально (без Docker)

```bash
cd lab1-mcp-finance-lab
uv run python src/server.py
```

Сервер будет доступен на `http://localhost:8000`:

- `http://localhost:8000/mcp` — MCP (streamable-http)
- `http://localhost:8000/sse` — MCP (SSE)
- `http://localhost:8000/health` — health check
- `http://localhost:8000/metrics` — Prometheus-метрики

## Запуск в Docker

### Сборка образа

```bash
docker build -t lab1-mcp-finance .
```

### Запуск контейнера

```bash
docker run --rm -p 8000:8000 -e LOG_LEVEL=INFO lab1-mcp-finance
```

### Через docker compose (рекомендуется)

Из корня репозитория:

```bash
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build
```

Сервер будет доступен на `http://localhost:8000`.

## Проверка

```bash
# Health check
curl http://localhost:8000/health

# Инициализация MCP-сессии (streamable-http)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
```

## Структура

```
src/
├── server.py             # Точка входа, регистрация middleware и роутов
├── mcp_instance.py       # Единый экземпляр FastMCP
├── calculations.py       # Финансовые расчёты
├── validators.py         # Валидация входных данных
├── metrics.py            # Prometheus-метрики
├── tools/                # Реализация MCP-инструментов
├── middleware/           # Middleware (rate limiting, логирование, ошибки)
└── utils/                # Трейсинг и вспомогательные утилиты
```

