# Лабораторная работа 4. Агент на SmolAgents (Code Agent)

> | | |
> |---|---|
> | **Каталог** | `lab4-smolagents-agent/` |
> | **Точка входа** | `src/start_a2a.py` |
> | **Технологии** | Python 3.12, SmolAgents ≥ 0.1 (Hugging Face), A2A SDK, LiteLLM, OpenInference, Docker |
> | **Ориентировочное время** | 3–5 часов |

---

## 1. Цель работы

Создать лёгковесного агента на базе **SmolAgents** от Hugging Face — минималистичного
фреймворка с акцентом на простоту и эффективность — и подключить его к A2A. Сравнить подход
SmolAgents с LangChain из лабораторной работы 3.

---

## 2. Теоретическая часть

### Code Agent против Tool Calling Agent

| | Tool Calling Agent | Code Agent |
|---|---|---|
| Как действует | Выбирает готовый инструмент и передаёт аргументы | Пишет фрагмент Python-кода и исполняет его |
| Шаги на задачу | Много (цикл «рассуждение → вызов → ответ») | Мало (один блок кода решает составную задачу) |
| Гибкость | Ограничена набором инструментов | Практически любая вычислительная задача |
| Расход токенов | Выше | Ниже |

### Почему меньше вызовов LLM

Code Agent объединяет несколько вызовов инструментов в один фрагмент кода вместо цикла
«рассуждение → один tool call → ответ» на каждом шаге. Это даёт сокращение числа шагов
и вызовов LLM **примерно на 30 %** — это видно в трейсах Phoenix.

### Меры безопасности

- **Sandboxed execution** — выполнение кода в изолированной среде (например, E2B).
- **`max_iterations`** — жёсткий лимит длины цикла агента.
- **Изоляция контейнера** — в AI Agents агент работает в отдельном окружении без доступа
  к файловой системе хоста.

### ⚠️ Замечание для Intel Mac

SmolAgents имеет транзитивную зависимость от `torch`, который **не поддерживает Intel Mac
(x86_64) с macOS 14+**. На этой платформе `uv sync` может завершиться ошибкой.

**Решение:** использовать Docker для разработки и развёртывания — Docker-образ работает
на Linux, где `torch` поддерживается полностью.

---

## 3. Задание

1. Изучить `agent.py`: тип агента (`CodeAgent`), его инструменты и модель.
2. Запустить агента: `LLM_API_KEY=dummy uv run python src/start_a2a.py`.
3. Проверить на задачах, требующих написания кода:
   - «посчитай 17-е простое число»;
   - «построй таблицу амортизации на 12 месяцев»;
   - «вычисли факториал числа 10».
4. Сравнить с лаб. 3: подсчитать число шагов и вызовов LLM на одинаковой задаче.
5. **Самостоятельное задание** (раздел 6).
6. Собрать образ и развернуть агента в AI Agents.

---

## 4. Этапы выполнения

### Этап 1. Подготовка

```bash
cd lab4-smolagents-agent
uv sync          # на Intel Mac используйте Docker
```

### Этап 2. Запуск агента

```bash
LLM_API_KEY=dummy uv run python src/start_a2a.py
```

> Для litellm-агентов используйте модель **с** префиксом:
> `LLM_MODEL=ollama_chat/llama3.2:3b`

### Этап 3. Проверка Code Agent

Отправить задачи, требующие генерации кода, и наблюдать сгенерированный и исполненный код:

```
Пользователь: Вычисли факториал числа 10
Агент:        [Пишет и выполняет Python-код]
              Факториал 10 = 3628800
```

### Этап 4. Сравнение с лабораторной работой 3

Включить телеметрию Phoenix на обоих агентах, выполнить **одинаковую задачу** и сравнить:

| Метрика | LangChain (лаб. 3) | SmolAgents (лаб. 4) |
|---|---|---|
| Число шагов агента | измерить | измерить |
| Число вызовов LLM | измерить | измерить |
| Время выполнения | измерить | измерить |
| Простота API | длиннее | короче |

### Этап 5. Самостоятельное задание

См. раздел 6.

### Этап 6. Сборка образа

```bash
docker buildx build --platform linux/amd64 -t smolagents-agent .
```

### Этап 7. Публикация

```bash
docker tag smolagents-agent:latest localhost:5000/smolagents-agent-repo:v1.0.0
docker push localhost:5000/smolagents-agent-repo:v1.0.0
```

### Этап 8. Создание агента в UI

1. Запустить контейнер локально (docker compose --profile labN).
2. Создать нового агента.
3. Указать Docker-образ из Artifact Registry.
4. Настроить переменные окружения.
5. Выбрать MCP-серверы (опционально).
6. Сохранить и запустить агента.

---

## 5. Ключевые инженерные решения

### Определение CodeAgent

```python
# src/agent.py
from smolagents import CodeAgent, Tool
from litellm import completion

def create_smolagents_agent(mcp_urls=None):
    def llm_call(messages, **kwargs):
        """Обертка для вызова LLM через LiteLLM."""
        response = completion(
            model=os.getenv("LLM_MODEL", "gpt-4"),
            messages=messages,
            api_base=os.getenv("LLM_API_BASE"),
            api_key=os.getenv("LLM_API_KEY"),
            **kwargs)
        return response.choices[0].message.content

    tools = get_mcp_tools(mcp_urls)
    system_prompt = os.getenv("AGENT_SYSTEM_PROMPT",
        "Ты полезный AI-ассистент. Используй доступные инструменты "
        "для решения задач пользователя.")

    agent = CodeAgent(tools=tools, llm=llm_call,
                      system_prompt=system_prompt,
                      max_iterations=15)
    return agent
```

- `llm_call` — единая точка подключения к Foundation Models через LiteLLM.
- `max_iterations=15` ограничивает длину цикла и защищает от зацикливания
  и бесконечного расхода токенов.

### Адаптация MCP-инструмента

```python
def create_mcp_tool(mcp_url: str, tool_name: str,
                    tool_description: str) -> Tool:
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
                function=mcp_tool_func)
```

> Разница с LangChain: объект `Tool` создаётся с полем `function=`,
> а не `func=`. Это частая причина ошибок при переносе кода между фреймворками.

### A2A-обёртка

`SmolAgentsA2AWrapper` преобразует интерфейс SmolAgents-агента в A2A-совместимый формат:

- поддержка streaming через `run_stream` (если доступен);
- управление сессиями и историей диалога;
- обработка ошибок.

### Отличия от других фреймворков

1. **Простота** — минимальный API и зависимости.
2. **Code Agents** — агент пишет и выполняет Python-код.
3. **Эффективность** — уменьшает количество шагов и вызовов LLM на ~30 %.
4. **Безопасность** — поддержка sandboxed execution (E2B).

---

## 6. Самостоятельное задание

Добавить агенту **собственный tool** — Python-функцию с декоратором `@tool`, например конвертер
валют с фиксированными курсами:

```python
from smolagents import tool

@tool
def currency_converter(amount: float, rate: float) -> str:
    """Конвертирует сумму по фиксированному курсу.

    Args:
        amount (float): исходная сумма.
        rate (float): курс перевода.
    """
    return f"{amount * rate:.2f}"
```

Добавить инструмент в `tools`, передать в `CodeAgent(tools=[...])` и проверить, что агент
корректно его вызывает по запросу вида «переведи 100 долларов в рубли по курсу 95».

---

## 7. Структура проекта

```
lab4-smolagents-agent/
├── src/
│   ├── agent.py               # Определение SmolAgents-агента
│   ├── a2a_wrapper.py         # Обёртка для A2A-протокола
│   ├── agent_task_manager.py  # Интеграция с A2A executor
│   └── start_a2a.py           # Точка входа приложения
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 8. Контрольные вопросы

1. Чем Code Agent отличается от Tool Calling Agent и когда каждый уместен?
2. Почему SmolAgents сокращает число вызовов LLM примерно на 30 % и как это проявляется
   в трейсах?
3. Какие меры безопасности применяются при выполнении сгенерированного кода
   (sandbox, E2B, лимиты итераций)?
4. Когда стоит выбрать SmolAgents, а когда LangChain?
5. Чем отличается создание `Tool` в SmolAgents от создания `Tool` в LangChain?

---

## 9. Критерии приёмки

- [ ] `CodeAgent` создан, модель подключена через LiteLLM.
- [ ] Агент решает задачи на генерацию и исполнение кода.
- [ ] Число шагов и вызовов LLM сравнено с лаб. 3 (таблица заполнена).
- [ ] Собственный `@tool` добавлен и корректно вызывается (самостоятельное задание).
- [ ] Образ `smolagents-agent:v1.0.0` развёрнут в AI Agents.

---

## 10. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| `uv sync` падает на Intel Mac | `torch` не поддерживает x86_64 macOS 14+ | Работать в Docker |
| Ошибки выполнения кода | Промпт не разрешает выполнение кода, нет изоляции | Проверить системный промпт, использовать sandbox |
| Модель не найдена | Нет префикса `ollama_chat/` для litellm | Добавить префикс к `LLM_MODEL` |
| Агент зациклился | Слишком сложная задача | Уменьшить `max_iterations`, разбить задачу |
| `Tool` не принимается | Передано поле `func` вместо `function` | Использовать `function=mcp_tool_func` |

---

## 12. Как тестировать лабораторную

### 12.1. Запуск агента

**Локально (без Docker):**

```powershell
cd lab4-smolagents-agent
uv sync
cp .env.example .env
# Для локального Ollama:
LLM_API_KEY=dummy uv run python src/start_a2a.py
```

> ⚠️ На Intel Mac `uv sync` может упасть из-за `torch`. Используйте Docker.

**Через Docker Compose:**

```powershell
# 1. Поднять Ollama (если не запущена)
docker compose -f docker-compose.local.yaml up -d ollama
docker exec -it pis-ollama ollama pull llama3.2

# 2. Поднять MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 3. Поднять Smolagents-агент
docker compose -f docker-compose.local.yaml --profile lab4 up -d --build
```

Агент запустится на порту **8004** (внутренний порт контейнера 10000).

### 12.2. Проверка доступности

```powershell
# Agent Card
curl http://localhost:8004/.well-known/agent-card.json

# Проверка через check.ps1 (из корня репозитория)
.\check.ps1
# Должно показать: [OK] Lab 4: Smolagents A2A
```

### 12.3. Проверка Code Agent

Отправить JSON-RPC-запрос агенту:

```powershell
curl -X POST http://localhost:8004/ -H "Content-Type: application/json" -d '{
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

# 2. Запустить Smolagents-агент (лаб. 4)
docker compose -f docker-compose.local.yaml --profile lab4 up -d --build

# 3. Отправить запрос, требующий MCP-инструмент
curl -X POST http://localhost:8004/ -H "Content-Type: application/json" -d '{
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

### 12.6. Сравнение с LangChain (лаб. 3)

Включить телеметрию Phoenix на обоих агентах, выполнить одинаковую задачу и сравнить:

| Метрика | LangChain (лаб. 3) | SmolAgents (лаб. 4) |
|---|---|---|
| Число шагов агента | измерить | измерить |
| Число вызовов LLM | измерить | измерить |
| Время выполнения | измерить | измерить |
| Простота API | длиннее | короче |

### 12.7. GUI-интерфейс

```powershell
# 1. Запустить MCP-сервер (лаб. 1)
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build

# 2. Запустить Smolagents-агент (лаб. 4)
docker compose -f docker-compose.local.yaml --profile lab4 up -d --build

# 3. Запустить GUI
cd ..\gui
/c/Users/voyag/AppData/Local/Programs/Python/Python312/python.exe server.py
# Открыть http://localhost:8080, вкладка Lab 4 — SmolAgents
```

В GUI выбрать вкладку **Lab 4 — SmolAgents**, ввести сообщение в чат и нажать **Отправить**. Агент напишет и выполнит Python-код, затем вернёт результат.

### 12.8. Сборка и публикация

```powershell
docker buildx build --platform linux/amd64 -t smolagents-agent .
docker tag smolagents-agent:latest localhost:5000/smolagents-agent:v1.0.0
docker push localhost:5000/smolagents-agent:v1.0.0
```