# Лабораторная работа 2. Запуск агента из Docker-образа в AI Agents

> | | |
> |---|---|
> | **Каталог** | `lab2-adk-agent/` |
> | **Точка входа** | `src/start_a2a.py` |
> | **Технологии** | Python 3.12, Google ADK, A2A SDK, LiteLLM, Docker, uv |
> | **Ориентировочное время** | 3–5 часов |

---

## 1. Цель работы

Освоить полный путь агента до платформы: определение агента в **Google ADK** (Agent Development
Kit), обёртка в A2A-сервис, сборка Docker-образа и запуск агента в консоли **AI Agents**.

---

## 2. Теоретическая часть

### Два ключевых ограничения платформы

**1. Файловая система в рантайме недоступна.**
Агенты в AI Agents не должны работать с файловой системой во время выполнения. Все необходимые
файлы и зависимости нужно упаковывать на этапе сборки Docker-образа.

**2. Переменные окружения прокидываются автоматически.**
AI Agents автоматически передаёт готовые переменные окружения в контейнер — настраивать их
вручную для развёрнутого агента не нужно.

### Переменные окружения AI Agents

| Переменная | Описание |
|---|---|
| `PHOENIX_ENDPOINT` | Endpoint для просмотра трейсов агента, вида `https://{domain}/v1/traces` |
| `ENABLE_PHOENIX` | По умолчанию `True` |
| `AGENT_NAME` | Название агента (UI) — нужно для карточки агента A2A |
| `AGENT_DESCRIPTION` | Описание агента (UI) — нужно для карточки агента A2A |
| `AGENT_VERSION` | Версия (по умолчанию `v1.0.0`) |
| `EVOLUTION_SERVICE_ACCOUNT_KEY_ID` | `key_id` сервисного аккаунта для доступа к LLM в ML Inference |
| `EVOLUTION_SERVICE_ACCOUNT_KEY_SECRET` | `key_secret` сервисного аккаунта для доступа к LLM |
| `LLM_MODEL` | Модель с префиксом `ollama_chat/`, например `ollama_chat/llama3.2:3b` |
| `LLM_API_BASE` | `http://localhost:11434/v1 (Ollama)` |
| `LLM_API_KEY` | API-ключ для доступа к Foundation Models |
| `AGENT_SYSTEM_PROMPT` | Системный промпт агента |
| `URL_AGENT` | URL вида `http://localhost:10000 (локальный A2A-агент)` |
| `PORT` | Порт, на котором работает агент |
| `MCP_URL` | Список URL MCP-серверов через запятую, например `http://example.com/sse` |

### Что такое Google ADK

ADK предоставляет декларативные абстракции:

- **Agent** — имя, описание, инструкция, модель, список инструментов;
- **Toolset** — группа инструментов, в том числе подключение к MCP-серверам;
- **Session Service** — управление историей диалога;
- **Runner** — цикл исполнения задачи агента.

### Что такое A2A

Agent-to-Agent — протокол взаимодействия между агентами и клиентами. Агент публикует
**`AgentCard`** (имя, версия, URL, поддерживаемые форматы, список `skills`) и обрабатывает
задачи, отдавая результат потоково.

---

## 3. Задание

1. Изучить структуру проекта: `agent.py` (определение агента), `a2a_agent.py` (A2A-обёртка),
   `agent_task_manager.py` (менеджер задач), `start_a2a.py` (точка входа).
2. Запустить агента локально: `LLM_API_KEY=dummy uv run python src/start_a2a.py`.
3. Проверить взаимодействие по протоколу A2A: отправить сообщение, получить ответ,
   убедиться в поддержке streaming.
4. Изучить Dockerfile и объяснить, почему все зависимости упаковываются на этапе сборки.
5. **Самостоятельное задание** (раздел 6).
6. Собрать образ и развернуть агента в AI Agents.

---

## 4. Этапы выполнения

### Этап 1. Подготовка

```bash
cd lab2-adk-agent
uv sync
```

Настроить локально: `LLM_MODEL`, `LLM_API_BASE`, `LLM_API_KEY`, `MCP_URL`, `AGENT_SYSTEM_PROMPT`.

### Этап 2. Запуск агента локально

```bash
LLM_API_KEY=dummy uv run python src/start_a2a.py
```

### Этап 3. Проверка A2A

Отправить сообщение через A2A-клиент (или curl к A2A-endpoint), получить ответ
и потоковые чанки. Убедиться, что агент читает `MCP_URL` и видит инструменты MCP-сервера.

### Этап 4. Разбор Dockerfile

Обратить внимание на:

- отсутствие `COPY` файлов данных во время выполнения;
- установку всех зависимостей на этапе сборки;
- `CMD`, запускающий A2A-сервер на `0.0.0.0:$PORT`.

### Этап 5. Самостоятельное задание

См. раздел 6.

### Этап 6. Сборка образа

```bash
docker buildx build --platform linux/amd64 -t adk-agent .
```

### Этап 7. Публикация в реестр

```bash
docker tag adk-agent:latest localhost:5000/adk-agent:v1.0.0
docker push localhost:5000/adk-agent:v1.0.0
```

### Этап 8. Запуск агента локально (A2A-сервер)

1. Задать название агента.
2. Указать Docker-образ, загруженный ранее.
3. Ввести системный промпт.
4. Выбрать MCP-сервер с нужными инструментами.

### Этап 9. Использование агента

После создания общаться с агентом напрямую через UI чата. Проверить, что агент вызывает
инструменты MCP-сервера из лабораторной работы 1.

---

## 5. Ключевые инженерные решения

### Декларативное определение агента

`src/agent.py` целиком читается из переменных окружения — один образ переиспользуется
для разных агентов:

```python
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import SseConnectionParams, McpToolset

llm_model = LiteLlm(
    model=os.getenv("LLM_MODEL"),
    api_base=os.getenv("LLM_API_BASE"),
    api_key=os.getenv("LLM_API_KEY"))

worker_agent = Agent(
    model=llm_model,
    name=os.getenv('AGENT_NAME', 'Work Agent').replace(" ", '_'),
    description=os.getenv('AGENT_DESCRIPTION', 'This agent do work'),
    instruction=os.getenv("AGENT_SYSTEM_PROMPT"),
    tools=[McpToolset(
        connection_params=SseConnectionParams(url=url))
        for url in os.getenv("MCP_URL").split(',')],
)

root_agent = worker_agent
```

Обратите внимание: `MCP_URL` разбивается по запятой, и для каждого URL создаётся отдельный
`McpToolset`. Имя агента приводится к формату идентификатора через `.replace(" ", '_')`.

### A2A-обёртка и AgentCard

`src/start_a2a.py` публикует агента как A2A-сервис:

```python
agent_card = AgentCard(
    name=os.getenv('AGENT_NAME', 'Work Agent'),
    description=os.getenv('AGENT_DESCRIPTION', '...'),
    url=os.getenv('URL_AGENT'),
    version=os.getenv('AGENT_VERSION', '1.0.0'),
    default_input_modes=agent_wrapper.SUPPORTED_CONTENT_TYPES,
    default_output_modes=agent_wrapper.SUPPORTED_CONTENT_TYPES,
    capabilities=AgentCapabilities(streaming=True),   # ← включает streaming
    skills=[...],
)

request_handler = DefaultRequestHandler(
    agent_executor=agent_task_manager,
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(agent_card=agent_card,
                                 http_handler=request_handler)
app = server.build()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

uvicorn.run(app, host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
```

- `AgentCapabilities(streaming=True)` — **без этого флага потоковые ответы не передаются**.
- `CORS` middleware нужен, чтобы к агенту мог обращаться браузер (например, из лаб. 10).
- `AgentCard.skills` описывает возможности агента — именно из неё бот Mattermost
  (лаб. 7) берёт данные для команды `/a2a help`.

---

## 6. Самостоятельное задание

Изменить системный промпт агента — сделать его **финансовым консультантом**, который
использует инструменты из лабораторной работы 1:

- агент должен знать, когда вызывать `loan_schedule_annuity`,
  `loan_schedule_differential`, `compare_loan_schedules`;
- корректно переводить естественный язык («кредит 1 млн под 12% на 5 лет») в аргументы
  инструментов;
- подключить MCP-сервер из лаб. 1 через переменную `MCP_URL`.

Далее: собрать образ и развернуть агента в AI Agents, проверить работу в чате.

---

## 7. Структура проекта

```
lab2-adk-agent/
├── src/
│   ├── agent.py               # Определение агента (Google ADK)
│   ├── a2a_agent.py           # Реализация A2A-обёртки
│   ├── agent_task_manager.py  # Менеджер задач A2A
│   └── start_a2a.py           # Точка входа приложения
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 8. Контрольные вопросы

1. Что такое Google ADK и какие абстракции (Agent, Toolset, Session) он предоставляет?
2. Почему агенты в AI Agents не должны работать с файловой системой в рантайме
   и к чему это обязывает при написании Dockerfile?
3. Какие переменные окружения AI Agents прокидывает в контейнер автоматически
   и какие из них используются для `AgentCard`?
4. Как устроен протокол A2A: `AgentCard`, task store, streaming и роль метода `execute()`?
5. Зачем в примере вызывается `.replace(" ", '_')` для имени агента?

---

## 9. Критерии приёмки

- [ ] Агент запускается локально командой `start_a2a.py`.
- [ ] Ответ агента приходит по A2A, поддерживается streaming.
- [ ] В Dockerfile все зависимости устанавливаются на этапе сборки.
- [ ] Образ `adk-agent:v1.0.0` опубликован в Artifact Registry.
- [ ] Агент создан в UI AI Agents и работает в чате.
- [ ] Системный промпт переработан под финансового консультанта (самостоятельное задание).

---

## 10. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| Агент не стартует | Не заданы ключи LLM | Проверить `LLM_API_KEY` и `LLM_API_BASE` |
| Ошибка при `MCP_URL` | Переменная пуста, `.split(',')` вернёт пустой список | Задать `MCP_URL` или обработать пустое значение |
| Нет streaming | Не задана `AgentCapabilities(streaming=True)` | Добавить флаг в `AgentCard` |
| Образ не запускается | Собран под неверной платформой | Пересобрать с `--platform linux/amd64` |
| Агент не вызывает инструменты | Нет MCP-сервера или слабый промпт | Выбрать MCP-сервер в UI, усилить инструкции в `AGENT_SYSTEM_PROMPT` |

---

## 12. Как тестировать лабораторную

### 12.1. Запуск агента

**Локально (без Docker):**

```powershell
cd lab2-adk-agent
uv sync
cp .env.example .env
# Для локального Ollama:
LLM_API_KEY=dummy uv run python src/start_a2a.py
```

**Через Docker Compose:**

```powershell
# 1. Поднять Ollama (если не запущена)
docker compose -f docker-compose.local.yaml up -d ollama
docker exec -it pis-ollama ollama pull llama3.2

# 2. Поднять MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 3. Поднять ADK-агент
docker compose -f docker-compose.local.yaml --profile lab2 up -d --build
```

Агент запустится на порту **8002** (внутренний порт контейнера 10000).

### 12.2. Проверка доступности

```powershell
# Agent Card
curl http://localhost:8002/.well-known/agent-card.json

# Проверка через check.ps1 (из корня репозитория)
.\check.ps1
# Должно показать: [OK] Lab 2: ADK A2A
```

### 12.3. Проверка A2A-взаимодействия

Отправить JSON-RPC-запрос агенту:

```powershell
curl -X POST http://localhost:8002/ -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "kind": "message",
      "messageId": "msg-1",
      "parts": [
        {"kind": "text", "text": "Calculate the monthly payment for a loan of 1000000 rubles at 15 percent per year for 5 years using the annuity method. Use the loan_schedule_annuity tool and answer briefly."}
      ]
    }
  }
}'
```

Ожидаемый результат: `"state":"completed"` и текст с числом ежемесячного платежа (≈ 23 790 ₽).

### 12.4. Проверка streaming

Агент поддерживает streaming — ответ приходит чанками по мере генерации. Проверить можно через A2A-клиент или GUI-инспектор.

### 12.5. Сквозная проверка: агент + MCP-сервер

```powershell
# 1. Запустить MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 2. Запустить ADK-агент (лаб. 2)
docker compose -f docker-compose.local.yaml --profile lab2 up -d --build

# 3. Отправить запрос, требующий MCP-инструмент
curl -X POST http://localhost:8002/ -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "kind": "message",
      "messageId": "msg-1",
      "parts": [
        {"kind": "text", "text": "Сравни аннуитетный и дифференцированный кредиты на 500 000 ₽ под 12% на 3 года"}
      ]
    }
  }
}'
```

Ожидаемый результат: агент вызывает `compare_loan_schedules` и возвращает сравнение.

### 12.6. GUI-интерфейс

```powershell
# 1. Запустить MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 2. Запустить ADK-агент (лаб. 2)
docker compose -f docker-compose.local.yaml --profile lab2 up -d --build

# 3. Запустить GUI
cd ..\gui
/c/Users/voyag/AppData/Local/Programs/Python/Python312/python.exe server.py
# Открыть http://localhost:8080, вкладка Lab 2 — ADK Agent
```

В GUI выбрать вкладку **Lab 2 — ADK Agent**, ввести сообщение в чат и нажать **Отправить**. Агент ответит потоково.

### 12.7. Сборка и публикация

```powershell
docker buildx build --platform linux/amd64 -t adk-agent .
docker tag adk-agent:latest localhost:5000/adk-agent:v1.0.0
docker push localhost:5000/adk-agent:v1.0.0
```

---

## 13. Полезные ссылки

- Google Agent Development Kit: https://google.github.io/adk-docs/
- AI Agents (Yandex Cloud): https://yandex.cloud/ru/docs/ai-agents/
- Протокол A2A: https://a2a-protocol.org/
- Репозиторий с примерами: https://github.com/yandex-cloud-examples/yc-ai-agents-quickstart