# Лабораторная работа 3. Запуск агента LangChain из Docker-образа в AI Agents
## Слайды с пояснениями

---

## Слайд 1. Титульный

**Запуск агента LangChain из Docker-образа в AI Agents**

- Каталог: `lab3-langchain-agent/`
- Точка входа: `src/start_a2a.py`
- Технологии: Python 3.12, LangChain, langchain-mcp-adapters, A2A SDK, LiteLLM, Docker, uv
- Время: 3–5 часов

> **Пояснение:** В лаб. 2 мы использовали Google ADK. Теперь попробуем LangChain — самый популярный фреймворк для создания LLM-приложений. Сравним подходы и поймём, какой фреймворк лучше подходит для разных задач.

---

## Слайд 2. Цель работы

**Освоить полный путь агента на LangChain:**

- Определение агента через `create_agent`
- Подключение инструментов из MCP-сервера
- Обёртка в A2A-сервис
- Сборка Docker-образа и запуск в AI Agents

> **Пояснение:** LangChain — это "конструктор" для LLM-приложений. В отличие от ADK, где вы описываете агента декларативно, в LangChain вы явно управляете циклом: получаете историю → вызываете LLM → LLM возвращает tool_calls → агент вызывает инструменты → добавляет результаты в историю → снова вызывает LLM.

---

## Слайд 3. Что такое LangChain

**LangChain** — фреймворк для создания приложений на основе LLM.

**Ключевые абстракции:**
- **Chat Model** — обёртка над LLM (LiteLLM, OpenAI, Anthropic)
- **Tools** — функции, которые LLM может вызывать
- **Agent** — цикл: история → LLM → tool_calls → вызов инструментов → результат → снова LLM
- **MCP Adapters** — мост между MCP-сервером и LangChain Tools

> **Пояснение:** LangChain работает по принципу "LLM решает, что делать". Вы даёте LLM список инструментов и историю диалога. LLM возвращает `tool_calls` — список инструментов, которые нужно вызвать. LangChain сам вызывает эти инструменты и добавляет результаты в историю.

---

## Слайд 4. Определение агента через `create_agent`

```python
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

model = ChatLiteLLM(model=llm_model,
                    api_base=llm_api_base,
                    api_key=llm_api_key)

client = MultiServerMCPClient({
    "mcp-finance": {
        "transport": "sse",
        "url": mcp_url,
    }
})

tools = await client.get_tools()

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
)
```

> **Пояснение:** `MultiServerMCPClient` подключается к MCP-серверу и получает список инструментов. `create_agent` создаёт агента, который знает эти инструменты. `system_prompt` — инструкция для агента. В отличие от ADK, здесь нет `AgentCard` — всё это будет в A2A-обёртке.

---

## Слайд 5. A2A-обёртка и AgentCard

```python
agent_card = AgentCard(
    name=os.getenv('AGENT_NAME', 'Work Agent'),
    description=os.getenv('AGENT_DESCRIPTION', '...'),
    url=os.getenv('URL_AGENT'),
    version=os.getenv('AGENT_VERSION', '1.0.0'),
    default_input_modes=agent_wrapper.SUPPORTED_CONTENT_TYPES,
    default_output_modes=agent_wrapper.SUPPORTED_CONTENT_TYPES,
    capabilities=AgentCapabilities(streaming=True),
    skills=[...],
)

request_handler = DefaultRequestHandler(
    agent_executor=agent_task_manager,
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(agent_card=agent_card,
                                 http_handler=request_handler)
app = server.build()
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

uvicorn.run(app, host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
```

> **Пояснение:** A2A-обёртка идентична лаб. 2. Это показывает, что протокол A2A не зависит от фреймворка агента. Вы можете заменить ADK на LangChain, и A2A-код не изменится. `AgentCapabilities(streaming=True)` — без этого флага потоковые ответы не передаются.

---

## Слайд 6. Переменные окружения AI Agents

| Переменная | Описание |
|---|---|
| `PHOENIX_ENDPOINT` | Endpoint для просмотра трейсов агента |
| `AGENT_NAME` | Название агента (UI) |
| `AGENT_DESCRIPTION` | Описание агента (UI) |
| `LLM_MODEL` | Модель, например `ollama_chat/llama3.2:3b` |
| `LLM_API_BASE` | `http://localhost:11434/v1 (Ollama)` |
| `LLM_API_KEY` | API-ключ для доступа к Foundation Models |
| `AGENT_SYSTEM_PROMPT` | Системный промпт агента |
| `MCP_URL` | Список URL MCP-серверов через запятую |
| `PORT` | Порт, на котором работает агент |

> **Пояснение:** AI Agents сам подставляет эти переменные. Вам не нужно их настраивать в UI — они уже есть. Но вы должны их **читать** в коде через `os.getenv()`. `MCP_URL` — это список MCP-серверов, которые агент может использовать. Разбивается по запятой.

---

## Слайд 7. Запуск агента локально

```bash
cd lab3-langchain-agent
uv sync
LLM_API_KEY=dummy uv run python src/start_a2a.py
```

**Проверка A2A:**
Отправить сообщение через A2A-клиент (или curl к A2A-endpoint), получить ответ и потоковые чанки. Убедиться, что агент читает `MCP_URL` и видит инструменты MCP-сервера.

> **Пояснение:** Для локального запуска нужен ключ LLM. В AI Agents ключ подставляется автоматически через `EVOLUTION_SERVICE_ACCOUNT_KEY_ID` и `EVOLUTION_SERVICE_ACCOUNT_KEY_SECRET`. Если агент не вызывает инструменты — проверьте `MCP_URL` и `AGENT_SYSTEM_PROMPT`: промпт должен явно указывать агенту использовать инструменты MCP.

---

## Слайд 8. Разбор Dockerfile

**Обратить внимание на:**
- Отсутствие `COPY` файлов данных во время выполнения
- Установка всех зависимостей на этапе сборки
- `CMD`, запускающий A2A-сервер на `0.0.0.0:$PORT`

> **Пояснение:** Dockerfile для агента — это "печать торта": все ингредиенты (зависимости, код) смешиваются на этапе сборки. В рантайме — только готовый торт. Это значит: `pip install` или `uv sync` в Dockerfile, а не в `CMD`. `CMD` — только запуск сервера.

---

## Слайд 9. Сборка и публикация образа

```bash
docker buildx build --platform linux/amd64 -t langchain-agent .
docker tag langchain-agent:latest localhost:5000/langchain-agent:v1.0.0
docker push localhost:5000/langchain-agent:v1.0.0
```

> **Пояснение:** `--platform linux/amd64` обязателен. `docker tag` переименовывает образ в полный путь с реестром. `docker push` загружает образ в Artifact Registry. После этого AI Agents может его скачать и запустить.

---

## Слайд 10. Запуск агента локально (A2A-сервер)

1. Задать название агента
2. Указать Docker-образ, загруженный ранее
3. Ввести системный промпт
4. Выбрать MCP-сервер с нужными инструментами

> **Пояснение:** В UI вы выбираете Docker-образ из репозитория, указываете системный промпт (инструкцию для агента) и выбираете MCP-сервер. AI Agents сам подставит переменные окружения (ключи, URL, порт).

---

## Слайд 11. Самостоятельное задание

**Изменить системный промпт агента — сделать его финансовым консультантом:**

- Агент должен знать, когда вызывать `loan_schedule_annuity`, `loan_schedule_differential`, `compare_loan_schedules`
- Корректно переводить естественный язык («кредит 1 млн под 12% на 5 лет») в аргументы инструментов
- Подключить MCP-сервер из лаб. 1 через переменную `MCP_URL`

> **Пояснение:** Системный промпт — это "инструкция" для агента. Без него агент не знает, что он финансовый консультант. Пример промпта: "Ты финансовый консультант. Используй инструменты MCP-сервера для расчёта кредитов, вкладов и инвестиций. Если пользователь говорит 'кредит 1 млн под 12% на 5 лет', вызови `loan_schedule_annuity` с параметрами principal=1000000, annual_rate_percent=12, months=60."

---

## Слайд 12. Структура проекта

```
lab3-langchain-agent/
├── src/
│   ├── agent.py               # Определение агента (LangChain)
│   ├── a2a_agent.py           # Реализация A2A-обёртки
│   ├── agent_task_manager.py  # Менеджер задач A2A
│   └── start_a2a.py           # Точка входа приложения
├── Dockerfile
├── pyproject.toml
└── README.md
```

> **Пояснение:** `agent.py` — определение агента (модель, инструменты, system_prompt). `a2a_agent.py` — обёртка для A2A-протокола. `agent_task_manager.py` — менеджер задач, который передаёт запросы агенту и возвращает результат. `start_a2a.py` — точка входа, которая запускает A2A-сервер.

---

## Слайд 13. Критерии приёмки

- [ ] Агент запускается локально командой `start_a2a.py`
- [ ] Ответ агента приходит по A2A, поддерживается streaming
- [ ] В Dockerfile все зависимости устанавливаются на этапе сборки
- [ ] Образ `langchain-agent:v1.0.0` опубликован в Artifact Registry
- [ ] Агент создан в UI AI Agents и работает в чате
- [ ] Системный промпт переработан под финансового консультанта

> **Пояснение:** Streaming — это когда ответ приходит частями, а не одним блоком. Вы видите, как агент "печатает" ответ в реальном времени. Без `AgentCapabilities(streaming=True)` ответ придёт одним блоком в конце.

---

## Слайд 14. Типичные ошибки

| Проблема | Причина | Решение |
|---|---|---|
| Агент не стартует | Не заданы ключи LLM | Проверить `LLM_API_KEY` и `LLM_API_BASE` |
| Ошибка при `MCP_URL` | Переменная пуста, `.split(',')` вернёт пустой список | Задать `MCP_URL` или обработать пустое значение |
| Нет streaming | Не задана `AgentCapabilities(streaming=True)` | Добавить флаг в `AgentCard` |
| Образ не запускается | Собран под неверной платформой | Пересобрать с `--platform linux/amd64` |
| Агент не вызывает инструменты | Нет MCP-сервера или слабый промпт | Выбрать MCP-сервер в UI, усилить инструкции в `AGENT_SYSTEM_PROMPT` |

> **Пояснение:** Самая частая ошибка — "агент не вызывает инструменты". Это может быть по двум причинам: 1) MCP-сервер не выбран в UI, 2) системный промпт слишком слабый. Если промпт говорит "ты полезный ассистент", агент не знает, что он должен использовать инструменты. Нужно явно указать: "используй инструменты MCP-сервера для расчёта кредитов".

---

## Слайд 15. Контрольные вопросы

1. Что такое LangChain и какие абстракции (Chat Model, Tools, Agent) он предоставляет?
2. Почему агенты в AI Agents не должны работать с файловой системой в рантайме и к чему это обязывает при написании Dockerfile?
3. Какие переменные окружения AI Agents прокидывает в контейнер автоматически и какие из них используются для `AgentCard`?
4. Как устроен протокол A2A: `AgentCard`, task store, streaming и роль метода `execute()`?
5. Зачем в примере вызывается `.replace(" ", '_')` для имени агента?

> **Пояснение:** Вопросы проверяют понимание архитектуры. LangChain предоставляет абстракции: Chat Model (LLM), Tools (функции), Agent (цикл). Файловая система недоступна — значит, всё в Dockerfile. A2A — это протокол: AgentCard (документация), task store (задачи), streaming (потоковые ответы).

---

## Слайд 16. Итоги

**Что мы сделали:**
- Определили агента в LangChain
- Обернули его в A2A-сервис
- Собрали Docker-образ и запустили локально (docker compose --profile labN)
- Подключили MCP-сервер из лаб. 1

**Что дальше (лаб. 4):**
- Создадим агента на Strands Agents
- Сравним с LangChain и ADK
- Добавим интеграцию с MCP

> **Пояснение:** Лабораторная 3 — это альтернатива лаб. 2. Мы показали, что один и тот же агент можно реализовать на разных фреймворках. A2A-код не меняется — меняется только определение агента. В лаб. 4 мы попробуем третий фреймворк (Strands) и сравним все три.
