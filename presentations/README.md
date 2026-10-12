# Методические материалы: разработка AI-агентов и MCP-серверов

Курс из **10 лабораторных работ** по разработке, контейнеризации и развёртыванию AI-агентов
и MCP-серверов. Все работы запускаются локально (Ollama + Docker Compose).


> Локальный стенд: Ollama (LLM) + docker-compose.local.yaml (профили lab1..lab10).


---

## Цель курса

Сформировать практические навыки полного цикла работы с агентами:

1. **MCP-серверы** — описание инструментов для агента, валидация, тесты, метрики (лаб. 1, 9).
2. **Агенты** — пять фреймворков: Google ADK, LangChain, SmolAgents, CrewAI, Strands (лаб. 2–6).
3. **Каналы доставки** — Mattermost, Telegram, веб-интерфейс с динамическим UI (лаб. 7, 8, 10).

Сквозной сценарий курса:

```
пользователь → канал (UI / Telegram / Mattermost / Web)
             → A2A-агент
             → MCP-инструмент
             → вычисление
             → ответ с данными
```

## Аудитория и требования

- Студенты бакалавриата и магистратуры, инженеры и аналитики.
- **Обязательно:** Python 3.12, Git, базовое знание HTTP/JSON, Docker.
- **Дополнительно:** Go 1.21+ (лаб. 9), Node.js 18 (лаб. 10).
- **Доступы:** Ollama (LLM на :11434), Docker Desktop; облако cloud.ru — опционально.

---

## Карта лабораторных работ

| № | Лабораторная работа | Язык | Ключевые технологии | Назначение |
|---|---|---|---|---|
| 1 | [MCP-сервер финансовых расчётов](01-mcp-server-python.md) | Python 3.12 | FastMCP, Docker, uv | MCP-сервер с расчётом кредитов и вкладов |
| 2 | [Запуск агента из Docker-образа](02-google-adk-agent.md) | Python 3.12 | Google ADK, A2A SDK, Docker | Развёртывание агента в AI Agents |
| 3 | [Агент на LangChain](03-langchain-agent.md) | Python 3.12 | LangChain, A2A SDK, LiteLLM | Агент с интеграцией MCP-инструментов |
| 4 | [Агент на SmolAgents](04-smolagents-agent.md) | Python 3.12 | SmolAgents, A2A SDK | Лёгкий Code Agent |
| 5 | [Мульти-агентная команда на CrewAI](05-crewai-agent.md) | Python 3.12 | CrewAI, A2A SDK | Команда взаимодействующих агентов |
| 6 | [Strands Agents с Meta-Tooling](06-strands-meta-tooling.md) | Python 3.12 | Strands Agents, MCP | Агент, создающий инструменты на лету |
| 7 | [Mattermost-бот для A2A-агента](07-mattermost-bot.md) | Python 3.10+ | mattermostdriver, a2a SDK | Интеграция агента в Mattermost |
| 8 | [Telegram-бот для A2A-агента](08-telegram-bot.md) | Python 3.13 | aiogram 3, a2a, httpx | Интеграция агента в Telegram |
| 9 | [MCP-сервер финансовых расчётов на Go](09-mcp-server-go.md) | Go 1.21+ | go modules, Prometheus | MCP-сервер на Go с 5 инструментами |
| 10 | [A2UI Renderer](10-a2ui-renderer.md) | TypeScript / React | React, @json-render/core | Веб-интерфейс с динамическим UI |

---

## Архитектура лабораторного стенда

```
┌──────────────────────────────────────────────┐
│  КАНАЛ:  UI AI Agents · Telegram · Mattermost │  ← лаб. 7, 8, 10
│           · веб A2UI-рендерер                │
└───────────────────┬──────────────────────────┘
                    │  протокол A2A (JSON-RPC / SSE)
┌───────────────────▼──────────────────────────┐
│  АГЕНТ:  ADK · LangChain · SmolAgents        │  ← лаб. 2–6
│          CrewAI · Strands                    │
│  обёртка: AgentCard + streaming + сессии      │
└───────────────────┬──────────────────────────┘
                    │  протокол MCP
┌───────────────────▼──────────────────────────┐
│  MCP-СЕРВЕР:  finance (Python) · finance-go   │  ← лаб. 1, 9
│  5 инструментов: кредиты, вклад, инвестиции  │
└───────────────────┬──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│  LLM:  Foundation Models / ML Inference      │
└──────────────────────────────────────────────┘
```

**MCP** (Model Context Protocol) — протокол «агент ↔ инструменты»: агент получает описание
инструментов и вызывает их через сервер.
**A2A** (Agent-to-Agent) — протокол «агент ↔ агент или клиент»: агент публикует карточку
`AgentCard` и отвечает на задачи по HTTP/SSE.

**Наблюдаемость:** Phoenix / OpenTelemetry — трейсы; Prometheus `/metrics` — метрики.

---

---

## Настройка Ollama и подключение LLM

Все агенты (лаб. 2–6) работают с **локальной LLM через Ollama** — облачные доступы не нужны.

### 1. Установка и запуск Ollama

**Windows / macOS:** скачайте установщик с [ollama.com/download](https://ollama.com/download),
установите и запустите приложение (или в терминале: `ollama serve`).

**Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

**Через Docker:**

```bash
docker compose -f docker-compose.local.yaml up -d ollama
```

### 2. Скачивание модели

```bash
ollama pull llama3.2:3b        # ~2 ГБ, работает на 8 ГБ RAM
```

Проверка: `ollama list` — модель `llama3.2:3b` в списке.

### 3. Проверка, что Ollama отвечает

```bash
curl http://localhost:11434/api/tags
curl http://localhost:11434/api/generate -d '{"model":"llama3.2:3b","prompt":"2+2=?","stream":false}'
```

### 4. Подключение LLM к агентам (лаб. 2–6)

Настройки читаются из `.env` в каталоге лабы (или переменных окружения):

| Лабораторная | `LLM_MODEL` | `LLM_API_BASE` | `LLM_API_KEY` |
|---|---|---|---|
| 2 (ADK, litellm) | `ollama_chat/llama3.2:3b` | `http://localhost:11434` | `dummy` |
| 3 (LangChain, ChatOpenAI) | `llama3.2:3b` | `http://localhost:11434/v1` | `dummy` |
| 4–6 (litellm) | `ollama_chat/llama3.2:3b` | `http://localhost:11434` | `dummy` |

> ⚠️ **Формат имени модели зависит от клиента:**
> - `ChatOpenAI` (лаб. 3) — OpenAI-совместимый API Ollama (`/v1`), модель **без** префикса;
> - `litellm` (лаб. 2, 4–6) — нативный API Ollama, модель **с** префиксом `ollama_chat/`
>   (он включает поддержку function calling — без него агент не сможет вызывать MCP-инструменты);
> - из Docker-контейнеров Ollama доступна как `http://host.docker.internal:11434`.

### 5. Типовые ошибки

| Ошибка | Причина | Решение |
|---|---|---|
| `Cannot connect to host localhost:11434` | Ollama не запущена | `ollama serve` (или приложение Ollama) |
| `404 page not found` | litellm стучится в `/v1` вместо нативного API | `LLM_API_BASE=http://localhost:11434` (без `/v1`) и префикс `ollama_chat/` |
| `model not found` | Модель не скачана | `ollama pull llama3.2:3b` |
| `tool '...' not found` | Модель без function calling | использовать `ollama_chat/llama3.2:3b` |

---

## Как проверить работу лабораторной

### Lab 1 — MCP-сервер (порт 8000)

```bash
cd lab1-mcp-finance-lab
.venv/Scripts/python.exe src/server.py        # Windows; Linux/macOS: uv run python src/server.py
```

- SSE-транспорт: `curl http://localhost:8000/sse` → ответ `event: endpoint`;
- GUI: [http://localhost:8080](http://localhost:8080) → расчёт вклада/кредита;
- тесты: `PYTHONPATH=src uv run pytest test/`.

### Lab 2–6 — A2A-агенты (порты 10000+)

```bash
cd labN-...-agent
uv sync
.venv/Scripts/python.exe src/start_a2a.py     # или: uv run python src/start_a2a.py
```

1. **Карточка агента:** `curl http://localhost:10000/.well-known/agent-card.json` → JSON с `name`, `url`;
2. **Сквозной запрос** (агент + LLM + MCP-инструмент):

```bash
curl -X POST http://localhost:10000/ -H "Content-Type: application/json" --data-binary '{"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message":{"role":"user","kind":"message","messageId":"msg-1","parts":[{"kind":"text","text":"Calculate the monthly payment for a loan of 1000000 rubles at 15 percent per year for 5 years using the annuity method. Use the loan_schedule_annuity tool and answer briefly."}]}}}'
```

Ожидаемый результат: `"state":"completed"` и текст с числом ежемесячного платежа
(для этих параметров ≈ 23 790 ₽).

### Lab 9 — MCP-сервер на Go (порт 8100)

```bash
cd lab9-mcp-finance-go
go build ./... && go test ./...
```

### Lab 10 — A2UI-рендерер (порт 3000)

```bash
cd lab10-a2a-a2ui-renderer
npm install --legacy-peer-deps && npm start
```

Открыть [http://localhost:3000](http://localhost:3000), отправить запрос к A2A-агенту.

### Lab 7–8 — боты

Требуют токенов (`MATTERMOST_TOKEN`, `TELEGRAM_BOT_TOKEN` в `.env`) и запущенного A2A-агента
(`A2A_BASE_URL`). Проверка — диалог с ботом в канале и ответ с расчётом.

### Общая проверка всех сервисов

```powershell
.\check.ps1        # PowerShell: Ollama 11434, lab1 :8000, лаб. 2–6, lab9 :8100, lab10 :3000
```

---

## Типовой рабочий процесс

Эти шаги повторяются в лабораторных 2–6 и 9.

| Шаг | Действие | Команда / где |
|---|---|---|
| 1 | Получить доступы | Ollama (llama3.2), Docker Desktop |
| 2 | Подготовить проект | `git clone … && cd labN-*` |
| 3 | Установить зависимости | `uv sync` / `poetry install` / `npm install` |
| 4 | Запустить локально | проверить, что сервис поднимается и отвечает |
| 5 | Выполнить задание | изучить код, внести изменения |
| 6 | Прогнать тесты | `PYTHONPATH=src uv run pytest test/` / `go test ./...` |
| 7 | Собрать образ | `docker buildx build --platform linux/amd64 -t <имя> .` |
| 8 | Присвоить тег | `docker tag <имя> localhost:5000/<repo>:v1.0.0` |
| 9 | Опубликовать | `docker push localhost:5000/<repo>:v1.0.0` |
| 10 | Развернуть в AI Agents | UI: создать агента или MCP-сервер, указать образ |
| 11 | Проверить | диалог в чате, скриншоты, ответы на вопросы, commit |

---

## Общие переменные окружения

Агенты (лаб. 2–6) читают настройки из переменных окружения, которые платформа
подставляет в контейнер **автоматически**:

| Переменная | Назначение |
|---|---|
| `LLM_MODEL` | Модель, например `llama3.2:3b` |
| `LLM_API_BASE` | `http://localhost:11434/v1 (Ollama)` |
| `LLM_API_KEY` | Ключ доступа к Foundation Models |
| `AGENT_NAME` | Имя агента — попадает в `AgentCard` |
| `AGENT_DESCRIPTION` | Описание агента — попадает в `AgentCard` |
| `AGENT_VERSION` | Версия агента (по умолчанию `v1.0.0`) |
| `AGENT_SYSTEM_PROMPT` | Системный промпт агента |
| `MCP_URL` | Список URL MCP-серверов через запятую |
| `URL_AGENT` | Внешний URL агента вида `http://localhost:10000 (локальный A2A-агент)` |
| `PORT` | Порт A2A-сервера |
| `PHOENIX_ENDPOINT` | Endpoint телеметрии (Ariadne Phoenix) |
| `ENABLE_PHOENIX` | Флаг включения телеметрии (по умолчанию `true`) |
| `EVOLUTION_SERVICE_ACCOUNT_KEY_ID` | `key_id` сервисного аккаунта для ML Inference |
| `EVOLUTION_SERVICE_ACCOUNT_KEY_SECRET` | `key_secret` сервисного аккаунта для ML Inference |

При локальном запуске переменные задаются вручную:

```bash
MCP_URL=http://localhost:8000/sse PORT=10003 LLM_API_KEY=dummy uv run python src/start_a2a.py
```

---

## Важные предупреждения

> ⚠️ **В AI Agents агенты не должны работать с файловой системой в рантайме.**
> Все файлы, зависимости и каталоги упаковываются на этапе сборки Docker-образа.

- **Node.js 18 обязателен для лаб. 10**; установка — `npm install --legacy-peer-deps`.
- **Формат `LLM_MODEL` различается:**
  - для прямого `ChatOpenAI` (лаб. 3) — `llama3.2:3b` **без префикса**;
  - для litellm (лаб. 4–6) — `ollama_chat/llama3.2:3b` **с префиксом**.
- **Лаб. 4 на Intel Mac:** транзитивная зависимость `torch` не поддерживает x86_64 macOS 14+.
  Решение — работать в Docker (внутри Linux `torch` поддерживается полностью).
- **Лаб. 9:** точка входа `cmd/server/main.go` в текущем состоянии репозитория **отсутствует** —
  транспорт MCP (JSON-RPC + `/metrics` + `/health`) нужно реализовать самостоятельно.
- **Все образы собираются под `linux/amd64`** — облачная платформа не поддерживает arm64.
- Перед `docker push` пройдите аутентификацию в Artifact Registry
  (локальный реестр: docker run -d -p 5000:5000 registry:2).

---

## Запуск полного стека локально

**Через Docker Compose (рекомендуется):**

```bash
cp .env.example .env
docker compose -f docker-compose.local.yaml --profile lab1  up -d --build   # MCP-сервер (порт 8000)
docker compose -f docker-compose.local.yaml --profile lab3  up -d --build   # LangChain-агент (порт 8003)
docker compose -f docker-compose.local.yaml --profile lab10 up -d --build   # A2UI-рендерер (порт 3000)
```

Подробности — в [README.md](../README.md).

**Без Docker:**

```bash
# 1. MCP-сервер (лаб. 1) — порт 8000
cd lab1-mcp-finance-lab
uv run python src/server.py

# 2. Агент (например, лаб. 3) — порт 10003
cd lab3-langchain-agent
MCP_URL=http://localhost:8000/sse PORT=10003 \
  LLM_API_KEY=dummy uv run python src/start_a2a.py

# 3. Фронтенд (лаб. 10) — порт 3000
cd lab10-a2a-a2ui-renderer
source ~/.nvm/nvm.sh && nvm use 18
npm install --legacy-peer-deps && npm start

# Тесты
cd lab1-mcp-finance-lab && PYTHONPATH=src uv run pytest test/
cd lab9-mcp-finance-go  && go test ./...
```

---

## Итоговый проект

Собрать полный стек из выполненных лабораторных:

```
MCP-сервер (лаб. 1 или 9) → Агент (лаб. 2–6) → Канал (лаб. 7, 8 или 10)
```

**Требования:** сквозной сценарий «запрос пользователя → агент → MCP-инструмент → ответ с UI
или в чате», развёрнутый локально (docker compose --profile), с телеметрией.

---

## Общие требования к отчёту

По каждой лабораторной работе отчёт содержит:

1. Цель и описание выполненных заданий, включая самостоятельную часть.
2. Скриншоты и логи ключевых этапов.
3. Ссылка на код (репозиторий или коммит).
4. Ответы на контрольные вопросы.
5. Выводы: что освоено, какие проблемы возникли и как решены.

---

## Шпаргалка команд публикации

```bash
docker buildx build --platform linux/amd64 -t <имя> .
docker tag <имя> \
  localhost:5000/<repo>:v1.0.0
docker push localhost:5000/<repo>:v1.0.0
```