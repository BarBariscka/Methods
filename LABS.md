# Описание лабораторных работ

> **Репозиторий:** https://github.com/Voyager7777/evo-ai-agents-labs

Данный репозиторий содержит 10 лабораторных работ, посвящённых разработке, развёртыванию и интеграции AI-агентов и MCP-серверов для платформы [AI Agents](https://cloud.ru/products/evolution-ai-agents) на облаке [Evolution](https://cloud.ru/docs).

Лабораторные работы охватывают полный цикл работы с AI-агентами:

1. Создание MCP-серверов (инструментов для агентов) на Python и Go
2. Построение агентов на различных фреймворках (Google ADK, LangChain, SmolAgents, CrewAI, Strands Agents)
3. Интеграцию агентов в мессенджеры (Mattermost, Telegram)
4. Разработку веб-интерфейса для взаимодействия с агентами (A2UI)

---

## Общая таблица лабораторных работ

| № | Лабораторная работа | Язык | Ключевые технологии | Назначение |
|---|---------------------|------|---------------------|------------|
| 1 | [MCP-сервер финансовых расчётов](#лабораторная-работа-1-создание-mcp-сервера-финансовых-расчётов-python) | Python 3.12 | FastMCP, Docker, uv | MCP-сервер с инструментами расчёта кредитов и вкладов |
| 2 | [Агент на Google ADK](#лабораторная-работа-2-агент-на-google-adk) | Python 3.12 | Google ADK, A2A SDK, Docker | Запуск агента из Docker-образа в AI Agents |
| 3 | [Агент на LangChain](#лабораторная-работа-3-агент-на-langchain) | Python 3.12 | LangChain, A2A SDK, LiteLLM | Агент с интеграцией MCP-инструментов |
| 4 | [Агент на SmolAgents](#лабораторная-работа-4-агент-на-smolagents) | Python 3.12 | SmolAgents (Hugging Face), A2A SDK | Легковесный Code Agent |
| 5 | [Мульти-агентная команда на CrewAI](#лабораторная-работа-5-мульти-агентная-команда-на-crewai) | Python 3.12 | CrewAI, A2A SDK, LiteLLM | Команда взаимодействующих агентов |
| 6 | [Агент на Strands Agents с Meta-Tooling](#лабораторная-работа-6-агент-на-strands-agents-с-meta-tooling) | Python 3.12 | Strands Agents, A2A SDK | Агент, создающий инструменты на лету |
| 7 | [Mattermost-бот для A2A-агента](#лабораторная-работа-7-mattermost-бот-для-a2a-агента) | Python 3.10+ | mattermostdriver, A2A SDK, OpenTelemetry | Интеграция агента в Mattermost |
| 8 | [Telegram-бот для A2A-агента](#лабораторная-работа-8-telegram-бот-для-a2a-агента) | Python 3.13 | aiogram 3, A2A SDK, httpx | Интеграция агента в Telegram |
| 9 | [MCP-сервер финансовых расчётов на Go](#лабораторная-работа-9-mcp-сервер-финансовых-расчётов-на-go) | Go 1.21 | Go modules, Docker | MCP-сервер на Go с 5 инструментами |
| 10 | [A2UI Renderer](#лабораторная-работа-10-a2ui-renderer) | TypeScript/React | React, @json-render/core, A2UI | Веб-интерфейс с динамическим UI от агента |

---

## Лабораторная работа 1: Создание MCP-сервера финансовых расчётов (Python)

**Расположение:** [`lab1-mcp-finance-lab/`](lab1-mcp-finance-lab/)

### Цель работы

Освоить основы разработки MCP-сервисов (Model Context Protocol) с использованием фреймворка FastMCP: определить инструменты для финансовых расчётов, подготовить Docker-образ и развернуть его в облаке cloud.ru.

### Функциональность

MCP-сервер предоставляет инструменты для расчёта графиков выплат:

1. **Аннуитетный кредит** (`loan_schedule_annuity`) — фиксированный ежемесячный платёж и помесячный график
2. **Дифференцированный кредит** (`loan_schedule_differential`) — постоянная часть тела кредита и уменьшающиеся проценты
3. **Вклад с капитализацией** (`deposit_schedule_compound`) — график вклада с ежемесячной капитализацией и взносами
4. **Сравнение кредитов** (`compare_loan_schedules`) — сопоставление аннуитетной и дифференцированной схем

### Технологии

- Python 3.12, FastMCP
- Docker для контейнеризации
- uv для управления зависимостями
- pytest для тестирования (18 тестов)

### Запуск

```bash
cd lab1-mcp-finance-lab
uv run python src/server.py          # MCP-сервер на порту 8000
PYTHONPATH=src uv run pytest test/   # тесты
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab1 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 2: Агент на Google ADK

**Расположение:** [`lab2-adk-agent/`](lab2-adk-agent/)

### Цель работы

Освоить пошаговый процесс упаковки и запуска собственного агента в платформе AI Agents с использованием Docker и Google ADK (Agent Development Kit).

### Особенности

1. **Без файловой системы в рантайме** — все файлы и зависимости упаковываются на этапе сборки Docker-образа
2. **Автоматические переменные окружения** — AI Agents прокидывает готовые переменные в контейнер
3. **A2A-протокол** — агент доступен для взаимодействия через Agent-to-Agent

### Технологии

- Python 3.12, Google ADK, A2A SDK
- Docker для контейнеризации
- uv для управления зависимостями

### Запуск

```bash
cd lab2-adk-agent
LLM_API_KEY=<ключ> uv run python src/start_a2a.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab2 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 3: Агент на LangChain

**Расположение:** [`lab3-langchain-agent/`](lab3-langchain-agent/)

### Цель работы

Создать агента на базе **LangChain** — одного из самых популярных фреймворков для AI-агентов, освоить интеграцию LangChain-агента с MCP-серверами и развернуть его в AI Agents через протокол A2A.

### Особенности

1. **LangChain AgentExecutor** — стандартный подход LangChain к созданию агентов
2. **Интеграция с MCP** — преобразование MCP-инструментов в LangChain Tools
3. **Streaming** — потоковая передача ответов через A2A
4. **Телеметрия** — интеграция с OpenInference для отслеживания работы агента

### Технологии

- Python 3.12, LangChain (>=0.3.0), LangChain OpenAI
- A2A SDK (>=0.3.4), LiteLLM
- Docker для контейнеризации

### Запуск

```bash
cd lab3-langchain-agent
MCP_URL=http://localhost:8000/mcp PORT=10003 \
LLM_API_KEY=<ключ> uv run python src/start_a2a.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab3 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 4: Агент на SmolAgents

**Расположение:** [`lab4-smolagents-agent/`](lab4-smolagents-agent/)

### Цель работы

Создать легковесного агента на базе **SmolAgents** от Hugging Face — минималистичного фреймворка с акцентом на простоту и эффективность, подходящего для быстрого прототипирования.

### Особенности

1. **Легковесность** — минимальные зависимости и простой API
2. **Code Agents** — агент пишет и выполняет Python-код
3. **Эффективность** — сокращение числа шагов и вызовов LLM на ~30%
4. **Простая интеграция** — лёгкое подключение к A2A-протоколу

### Технологии

- Python 3.12, SmolAgents (>=0.1.0)
- A2A SDK (>=0.3.4), LiteLLM
- Docker для контейнеризации

### Запуск

```bash
cd lab4-smolagents-agent
LLM_API_KEY=<ключ> uv run python src/start_a2a.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab4 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 5: Мульти-агентная команда на CrewAI

**Расположение:** [`lab5-crewai-agent/`](lab5-crewai-agent/)

### Цель работы

Создать мульти-агентную команду (crew) на базе **CrewAI** — фреймворка, позволяющего нескольким специализированным AI-агентам совместно решать сложные задачи.

### Особенности

1. **Мульти-агентность** — несколько агентов работают вместе
2. **Распределение задач** — автоматическое распределение задач между агентами
3. **Delegation** — агенты могут делегировать задачи друг другу
4. **Структурированность** — чёткое разделение ролей (agents), задач (tasks) и команды (crew)

### Технологии

- Python 3.12, CrewAI (>=0.80.0), CrewAI Tools
- A2A SDK (>=0.3.4), LiteLLM
- Docker для контейнеризации

### Запуск

```bash
cd lab5-crewai-agent
LLM_API_KEY=<ключ> uv run python src/start_a2a.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab5 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 6: Агент на Strands Agents с Meta-Tooling

**Расположение:** [`lab6-strands-agent/`](lab6-strands-agent/)

### Цель работы

Создать агента на базе **Strands Agents** с возможностью **meta-tooling** — динамического создания инструментов на лету, что позволяет агенту самостоятельно расширять свои возможности без изменения кода.

### Особенности

1. **Meta-Tooling** — создание новых инструментов во время выполнения
2. **Динамическое расширение** — агент расширяет свои возможности самостоятельно
3. **Гибкость** — адаптация к новым задачам без изменения кода агента
4. **Инструменты для создания инструментов** — `load_tool`, `editor`, `shell`

### Технологии

- Python 3.12, Strands Agents (>=0.3.0)
- A2A SDK (>=0.3.4), LiteLLM
- Docker для контейнеризации

### Запуск

```bash
cd lab6-strands-agent
LLM_API_KEY=<ключ> uv run python src/start_a2a.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab6 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 7: Mattermost-бот для A2A-агента

**Расположение:** [`lab7-mattermost-bot-for-agents/`](lab7-mattermost-bot-for-agents/)

### Цель работы

Разработать бота для корпоративного мессенджера Mattermost, интегрированного с A2A-агентом, с поддержкой streaming-ответов, команд и полной телеметрии.

### Функциональность

1. **Ответы на упоминания** — бот отвечает на `@bot_name` в каналах
2. **Прямые сообщения** — поддержка приватных диалогов (DM)
3. **Команды** — `/a2a help`, `/a2a status` и другие
4. **Streaming** — потоковая передача ответов от A2A-агента
5. **Телеметрия** — полная интеграция с OpenInference и OpenTelemetry

### Технологии

- Python 3.10+, mattermostdriver
- A2A SDK, OpenTelemetry/OpenInference
- uv для управления зависимостями

### Запуск

```bash
cd lab7-mattermost-bot-for-agents
MATTERMOST_URL=<url> MATTERMOST_TOKEN=<токен> \
A2A_AGENT_URL=<url агента> uv run python bot.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab7 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 8: Telegram-бот для A2A-агента

**Расположение:** [`lab8-telegram-bot-for-agents/`](lab8-telegram-bot-for-agents/)

### Цель работы

Разработать бота на базе `aiogram 3` для взаимодействия с агентами по URL: быстрое подключение к агентной системе, переподключение и повторные попытки при ошибках.

### Функциональность

1. **Старт и меню** — разделы «Начать работу», «Помощь», «Подключиться по URL»
2. **Подключение по URL** — ввод URL агента прямо в чате
3. **Общение с агентом** — текстовые запросы и ответы
4. **Голосовые сообщения** — поддержка транскрипции
5. **Retry** — повтор запроса при ошибке
6. **История ошибок** — сводка последних ошибок для отладки

### Технологии

- Python 3.13, aiogram 3
- httpx, pydantic-settings, a2a SDK, OpenTelemetry
- Poetry / uv, Docker Compose

### Запуск

```bash
cd lab8-telegram-bot-for-agents
TELEGRAM_BOT_TOKEN=<токен> uv run python main.py
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab8 up -d --build` (см. [README.md](README.md)).

---

## Лабораторная работа 9: MCP-сервер финансовых расчётов на Go

**Расположение:** [`lab9-mcp-finance-go/`](lab9-mcp-finance-go/)

### Цель работы

Реализовать MCP-сервер для финансовых расчётов на языке Go — аналог лабораторной работы 1, демонстрирующий разработку MCP-сервисов в статически типизированной экосистеме.

### Функциональность

Сервер предоставляет 5 инструментов:

1. **`loan_schedule_annuity`** — расчёт аннуитетного кредита
2. **`loan_schedule_differential`** — расчёт дифференцированного кредита
3. **`deposit_schedule_compound`** — расчёт вклада с капитализацией
4. **`compare_loan_schedules`** — сравнение типов кредитов
5. **`investment_calculator`** — калькулятор инвестиций

Дополнительно: метрики Prometheus (`/metrics`) и health check (`/health`).

### Технологии

- Go >= 1.21, go modules
- Docker для контейнеризации

### Запуск

```bash
cd lab9-mcp-finance-go
go run ./cmd/server          # MCP-сервер на порту 8000
go test ./...                # тесты
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab9 up -d --build` (порт хоста 8100, см. [README.md](README.md)).

---

## Лабораторная работа 10: A2UI Renderer

**Расположение:** [`lab10-a2a-a2ui-renderer/`](lab10-a2a-a2ui-renderer/)

### Цель работы

Разработать React-приложение с нативной поддержкой протокола [A2UI](https://a2ui.org) — чат-интерфейс для взаимодействия с A2A-агентами, которые возвращают динамический UI.

### Особенности

1. **Модель adjacency list** — плоский список компонентов с ID-ссылками для эффективных патч-обновлений
2. **Рендеринг A2UI-компонентов** — Text, Button, TextInput, NumberInput, DateTimeInput, Card, Row, Column, Image, Switch, Checkbox, Slider, Divider
3. **Data binding** — привязка значений компонентов к модели данных
4. **Actions** — поддержка действий и обратных вызовов к серверу
5. **История** — сохранение чата и контекста в localStorage

### Технологии

- TypeScript, React, `@json-render/core`
- A2A-клиент (HTTP/SSE)
- Docker Compose, nginx

### Запуск

```bash
cd lab10-a2a-a2ui-renderer
npm install --legacy-peer-deps   # требуется Node 18
npm start                        # http://localhost:3000
```

Или через Docker: `docker compose -f docker-compose.local.yaml --profile lab10 up -d --build` (см. [README.md](README.md)).

URL A2A-сервера настраивается в шапке интерфейса и сохраняется в localStorage.

---

## Запуск полного стека локально

**Через Docker Compose (рекомендуется):**

```bash
cp .env.example .env
docker compose -f docker-compose.local.yaml --profile lab1  up -d --build   # MCP-сервер (порт 8000)
docker compose -f docker-compose.local.yaml --profile lab3  up -d --build   # LangChain-агент (порт 8003)
docker compose -f docker-compose.local.yaml --profile lab10 up -d --build   # A2UI-рендерер (порт 3000)
```

После этого в http://localhost:3000 укажите URL агента `http://localhost:8003`.
Проверка доступности сервисов: `.\check.ps1` (PowerShell).
Полное описание — в [README.md](README.md).

**Без Docker:**

1. **MCP-сервер** (лаб. 1): `cd lab1-mcp-finance-lab && uv run python src/server.py` (порт 8000)
2. **Агент** (например, лаб. 3): `cd lab3-langchain-agent && MCP_URL=http://localhost:8000/mcp PORT=10003 uv run python src/start_a2a.py`
3. **Фронтенд** (лаб. 10): `cd lab10-a2a-a2ui-renderer && npm start` (порт 3000, указать URL агента в интерфейсе)

## Общие переменные окружения для агентов (лаб. 2–6)

| Переменная | Назначение |
|------------|-----------|
| `LLM_API_KEY` | Ключ доступа к LLM |
| `LLM_API_BASE` | Базовый URL API (по умолчанию `https://foundation-models.api.cloud.ru/v1`) |
| `LLM_MODEL` | Модель (например, `Qwen/Qwen3-Coder-480B-A35B-Instruct`) |
| `MCP_URL` | URL MCP-сервера |
| `PORT` | Порт A2A-сервера |
| `URL_AGENT` | URL агента |
