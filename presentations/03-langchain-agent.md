# Лабораторная работа 3. Агент на LangChain с интеграцией MCP

> | | |
> |---|---|
> | **Каталог** | `lab3-langchain-agent/` |
> | **Точка входа** | `src/start_a2a.py` |
> | **Технологии** | Python 3.12, LangChain ≥ 0.3, langchain-openai, A2A SDK ≥ 0.3.4, LiteLLM, OpenInference, Docker |
> | **Порт** | `PORT` (например, `10003`) |
> | **Ориентировочное время** | 4–6 часов |

---

## 1. Цель работы

Создать агента на базе **LangChain** — одного из самых популярных фреймворков для AI-агентов,
освоить интеграцию LangChain-агента с MCP-серверами и развернуть агента в платформе AI Agents
через протокол A2A.

---

## 2. Теоретическая часть

### AgentExecutor и цикл ReAct

LangChain реализует цикл **ReAct** (Reason + Act): модель рассуждает, выбирает инструмент,
наблюдает результат и повторяет, пока не сформирует ответ.

```python
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools,
                               verbose=True, max_iterations=15)
```

- `create_openai_tools_agent` связывает модель, инструменты и промпт в план;
- `AgentExecutor` выполняет цикл, ограниченный `max_iterations` (защита от зацикливания).

### Составная схема промпта

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),                    # системный промпт
    MessagesPlaceholder(variable_name="chat_history"),   # история диалога
    ("human", "{input}"),                         # запрос пользователя
    MessagesPlaceholder(variable_name="agent_scratchpad"),  # размышления агента
])
```

`agent_scratchpad` — место, где накапливаются промежуточные вызовы инструментов.

### Зачем нужен LiteLLM

LiteLLM унифицирует обращение к разным провайдерам LLM за одним интерфейсом `completion(...)`.
В этой лабораторной он используется для доступа к локальной LLM (Ollama, OpenAI-совместимый API).
Отсюда же следует формат модели с префиксом `ollama_chat/` для litellm-агентов.

---

## 3. Задание

1. Изучить `agent.py`: как строится `AgentExecutor`, как задаются инструменты и промпт.
2. Разобрать механизм преобразования MCP-инструментов в LangChain Tools.
3. Запустить стек локально: MCP-сервер из лаб. 1 + агент.
4. Проверить streaming: убедиться, что ответы приходят потоково через A2A.
5. Изучить интеграцию OpenInference-телеметрии: какие трейсы генерируются при вызове инструментов.
6. **Самостоятельное задание** (раздел 6).
7. Собрать образ и развернуть агента в AI Agents.

---

## 4. Этапы выполнения

### Этап 1. Подготовка

```bash
cd lab3-langchain-agent
uv sync
```

### Этап 2. Запуск MCP-сервера (лабораторная работа 1)

```bash
cd lab1-mcp-finance-lab
uv run python src/server.py     # порт 8000
```

### Этап 3. Запуск агента

```bash
cd lab3-langchain-agent
MCP_URL=http://localhost:8000/sse PORT=10003 \
  LLM_API_KEY=dummy uv run python src/start_a2a.py
```

> ⚠️ Для `ChatOpenAI` используйте модель **без** префикса:
> `LLM_MODEL=llama3.2:3b`

### Этап 4. Проверка работы агента

Отправить финансовый запрос, например:

```
Пользователь: Рассчитай график аннуитетного кредита на 1 000 000 рублей под 12% годовых на 5 лет
Агент: Использую инструмент: loan_schedule_annuity
       [Результат расчёта графика платежей]
```

### Этап 5. Проверка streaming

Убедиться, что ответ агента приходит потоково через A2A — то есть чанки отправляются
по мере генерации, а не одним блоком в конце.

### Этап 6. Изучение телеметрии

Включить телеметрию (`ENABLE_PHOENIX=true`, `PHOENIX_ENDPOINT=…`) и посмотреть трейсы
вызовов инструментов в Phoenix: какие аргументы ушли, что вернулось, сколько заняло.

### Этап 7. Самостоятельное задание

См. раздел 6.

### Этап 8. Сборка и публикация

```bash
docker buildx build --platform linux/amd64 -t langchain-agent .
docker tag langchain-agent:latest localhost:5000/langchain-agent-repo:v1.0.0
docker push localhost:5000/langchain-agent-repo:v1.0.0
```

### Этап 9. Развёртывание

1. Запустить контейнер локально (docker compose --profile labN).
2. Создать нового агента.
3. Указать Docker-образ из Artifact Registry.
4. Настроить переменные окружения.
5. Выбрать MCP-серверы (опционально).
6. Сохранить и запустить агента.

---

## 5. Ключевые инженерные решения

### MCP-инструмент как LangChain Tool

```python
def create_mcp_tool(mcp_url: str, tool_name: str,
                    tool_description: str) -> Tool:
    """Создает LangChain Tool из MCP инструмента."""
    def mcp_tool_func(input_text: str) -> str:
        async def async_call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{mcp_url}/tools/{tool_name}/invoke",
                    json={"input": input_text},
                    headers={"Content-Type": "application/json"})
                response.raise_for_status()
                result = response.json()
                return str(result.get("content", result))
        return asyncio.run(async_call())

    return Tool(name=tool_name,
                description=tool_description,
                func=mcp_tool_func)
```

Список инструментов собирается из `MCP_URL`, разбитого по запятой:

```python
def get_mcp_tools(mcp_urls: Optional[str]) -> List[Tool]:
    tools = []
    if not mcp_urls:
        return tools
    for mcp_url in mcp_urls.split(','):
        mcp_url = mcp_url.strip()
        tools.append(create_mcp_tool(
            mcp_url, "loan_schedule_annuity",
            "Расчет графика аннуитетного кредита. Принимает сумму кредита, "
            "годовую ставку в процентах и срок в месяцах."))
        tools.append(create_mcp_tool(
            mcp_url, "loan_schedule_differential", "..."))
        tools.append(create_mcp_tool(
            mcp_url, "deposit_schedule_compound", "..."))
    return tools
```

> **Описание инструмента (`description`) критично:** именно по нему LLM решает, какой инструмент
> вызвать. Чем подробнее описание — тем точнее выбор.

### Сборка агента

```python
llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4"),
                 base_url=os.getenv("LLM_API_BASE"),
                 api_key=os.getenv("LLM_API_KEY"),
                 temperature=0.7)

tools = get_mcp_tools(mcp_urls)
system_prompt = os.getenv("AGENT_SYSTEM_PROMPT",
    "Ты полезный AI-ассистент. Используй доступные инструменты "
    "для решения задач пользователя.")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True,
                               handle_parsing_errors=True,
                               max_iterations=15)
```

`handle_parsing_errors=True` не даёт агенту «упасть», если модель вернула ответ
в неожиданном формате — executor попытается продолжить диалог.

### Отличия от Google ADK (лаб. 2)

1. **Фреймворк:** LangChain вместо Google ADK.
2. **Инструменты:** явное преобразование MCP-инструментов в `Tool`.
3. **Streaming:** `astream` вместо `run_async`.
4. **История:** хранение в памяти вместо `SessionService`.

---

## 6. Самостоятельное задание

Добавить в агента **второй инструмент** — например, поиск по Wikipedia или собственную функцию —
и продемонстрировать, что агент **выбирает нужный инструмент в зависимости от запроса**.

Ожидаемый результат — два сценария, где для разных вопросов вызываются разные инструменты:

| Запрос пользователя | Инструмент, который должен вызвать агент |
|---|---|
| «Рассчитай аннуитетный кредит 1 млн под 12% на 5 лет» | `loan_schedule_annuity` |
| «Кто такой Адам Смит?» | новый инструмент (Wikipedia / собственная функция) |

Зафиксировать в отчёте скриншоты обоих сценариев.

---

## 7. Структура проекта

```
lab3-langchain-agent/
├── src/
│   ├── agent.py               # Определение агента, адаптация MCP → Tool
│   ├── a2a_wrapper.py         # Обёртка для A2A-протокола (streaming)
│   ├── agent_task_manager.py  # Интеграция с A2A executor
│   └── start_a2a.py           # Точка входа приложения
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 8. Переменные окружения

| Переменная | Описание |
|---|---|
| `LLM_MODEL` | Название модели LLM (**без** префикса `ollama_chat/` для `ChatOpenAI`) |
| `LLM_API_BASE` | Базовый URL API для LLM |
| `LLM_API_KEY` | API-ключ для доступа к LLM |
| `AGENT_NAME` | Название агента |
| `AGENT_DESCRIPTION` | Описание агента |
| `AGENT_VERSION` | Версия агента |
| `AGENT_SYSTEM_PROMPT` | Системный промпт агента |
| `MCP_URL` | URL MCP-серверов (через запятую) |
| `URL_AGENT` | URL агента |
| `PORT` | Порт для запуска A2A-сервера |
| `PHOENIX_ENDPOINT` | Endpoint для Phoenix-телеметрии |
| `ENABLE_PHOENIX` | Включить телеметрию (`true` / `false`) |

---

## 9. Контрольные вопросы

1. Что такое `AgentExecutor` и как устроен цикл ReAct в LangChain?
2. Как MCP-инструмент адаптируется под интерфейс LangChain Tool и почему это проще,
   чем полноценный MCP-клиент?
3. Зачем нужен LiteLLM в этом проекте и как он связан с форматом `LLM_MODEL`
   `ollama_chat/`)?
4. Что показывает трейс OpenInference при вызове инструмента и как его читать в Phoenix?
5. Зачем в `ChatPromptTemplate` используется `MessagesPlaceholder("agent_scratchpad")`?

---

## 10. Критерии приёмки

- [ ] `AgentExecutor` построен, инструменты подключены из `MCP_URL`.
- [ ] Агент корректно отвечает на финансовый запрос, вызвав MCP-инструмент.
- [ ] Ответ приходит потоково (streaming) через A2A.
- [ ] Трейсы вызовов инструментов видны в Phoenix.
- [ ] Добавлен второй инструмент, маршрутизация продемонстрирована (самостоятельное задание).
- [ ] Образ `langchain-agent:v1.0.0` развёрнут в AI Agents.

---

## 12. Как тестировать лабораторную

### 12.1. Запуск агента

**Локально (без Docker):**

```powershell
cd lab3-langchain-agent
uv sync
cp .env.example .env
# Для локального Ollama:
LLM_API_KEY=dummy MCP_URL=http://localhost:8000/sse PORT=10003 uv run python src/start_a2a.py
```

**Через Docker Compose:**

```powershell
# 1. Поднять Ollama (если не запущена)
docker compose -f docker-compose.local.yaml up -d ollama
docker exec -it pis-ollama ollama pull llama3.2

# 2. Поднять MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 3. Поднять LangChain-агент
docker compose -f docker-compose.local.yaml --profile lab3 up -d --build
```

Агент запустится на порту **8003** (внутренний порт контейнера 10000).

### 12.2. Проверка доступности

```powershell
# Agent Card
curl http://localhost:8003/.well-known/agent-card.json

# Проверка через check.ps1 (из корня репозитория)
.\check.ps1
# Должно показать: [OK] Lab 3: LangChain A2A
```

### 12.3. Проверка A2A-взаимодействия

Отправить JSON-RPC-запрос агенту:

```powershell
curl -X POST http://localhost:8003/ -H "Content-Type: application/json" -d '{
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

# 2. Запустить LangChain-агент (лаб. 3)
docker compose -f docker-compose.local.yaml --profile lab3 up -d --build

# 3. Отправить запрос, требующий MCP-инструмент
curl -X POST http://localhost:8003/ -H "Content-Type: application/json" -d '{
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

### 12.6. Проверка телеметрии (Phoenix)

```powershell
# В .env или docker-compose.local.yaml:
# ENABLE_PHOENIX=true
# PHOENIX_ENDPOINT=https://your-phoenix-endpoint/v1/traces
```

Отправить запрос агенту, затем открыть Phoenix и посмотреть трейсы вызовов инструментов.

### 12.7. GUI-интерфейс

```powershell
# 1. Запустить MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 2. Запустить LangChain-агент (лаб. 3)
docker compose -f docker-compose.local.yaml --profile lab3 up -d --build

# 3. Запустить GUI
cd ..\gui
/c/Users/voyag/AppData/Local/Programs/Python/Python312/python.exe server.py
# Открыть http://localhost:8080, вкладка Lab 3 — LangChain
```

В GUI выбрать вкладку **Lab 3 — LangChain**, ввести сообщение в чат и нажать **Отправить**. Агент вызовет MCP-инструменты и ответит потоково.

### 12.8. Сборка и публикация

```powershell
docker buildx build --platform linux/amd64 -t langchain-agent .
docker tag langchain-agent:latest localhost:5000/langchain-agent:v1.0.0
docker push localhost:5000/langchain-agent:v1.0.0
```

---

## 13. Полезные ссылки

| Проблема | Причина | Решение |
|---|---|---|
| Агент не использует инструменты | Неверный `MCP_URL` или слабый промпт | Проверить URL, доступность MCP из контейнера, усилить `AGENT_SYSTEM_PROMPT` |
| Ошибки при streaming | Модель не поддерживает streaming или неверный `LLM_API_BASE` | Проверить endpoint и ключ |
| Phoenix пуст | Не задана телеметрия | Установить `ENABLE_PHOENIX=true` и `PHOENIX_ENDPOINT` |
| MCP-сервер недоступен из контейнера | Сетевые ограничения | Проверить сетевую доступность, использовать внутренний URL |
| Модель не найдена | Префикс `ollama_chat/` использован с `ChatOpenAI` | Убрать префикс для `ChatOpenAI` |