# Лабораторная работа 1. MCP-сервер финансовых расчётов

> | | |
> |---|---|
> | **Каталог** | `lab1-mcp-finance-lab/` |
> | **Точка входа** | `src/server.py` |
> | **Технологии** | Python 3.12, FastMCP ≥ 2.10, Pydantic, Prometheus Client, OpenTelemetry, uv, Docker |
> | **Порты** | MCP `8000/mcp`, метрики `8000/metrics`, health `8000/health` |
> | **Тесты** | 18 штук (`test_calculations.py`, `test_validators.py`) |
> | **Ориентировочное время** | 4–6 часов |

---

## 1. Цель работы

Освоить разработку MCP-сервисов (Model Context Protocol) на Python с использованием фреймворка
**FastMCP**: описание инструментов для агента, валидация входных данных, тестирование,
контейнеризация и локальный запуск (Docker Compose).

---

## 2. Теоретическая часть

### Что такое MCP-сервер

MCP-сервер — это сервис, предоставляющий набор **инструментов (tools)**, к которым может
обращаться агент. Каждый инструмент — это функция, зарегистрированная в фреймворке FastMCP.

FastMCP берёт на себя:

- запуск сервера (транспорт `streamable-http` или `sse`);
- регистрацию и описание инструментов;
- сериализацию / десериализацию аргументов и результатов;
- автоматическую генерацию спецификаций для клиента;
- поддержку метрик Prometheus и интеграцию с OpenTelemetry.

### Базовая структура

- **основной файл** (`server.py`) — создание экземпляра FastMCP, подключение инструментов, запуск;
- **единый экземпляр** (`mcp_instance.py`) — импортируется всеми модулями;
- **метрики** (`metrics.py`) — мониторинг через Prometheus;
- **бизнес-логика** (`calculations.py`, `validators.py`, `tools/`).

```python
from mcp_instance import mcp

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",  # транспорт
        host="0.0.0.0",               # адрес
        port=os.getenv("PORT", 8000)  # порт
    )
```

### Регистрация инструментов

Инструменты определяются как `async`-функции с декоратором `@mcp.tool`:

```python
@mcp.tool
async def loan_schedule_annuity(principal: float,
                                annual_rate_percent: float,
                                months: int,
                                ctx: Context = None) -> dict:
    """Полное и достаточное описание инструмента"""
    if ctx:
        await ctx.info("Начинаем расчет...")
        await ctx.report_progress(progress=0, total=100)
    # валидации и расчёты
    if ctx:
        await ctx.report_progress(progress=100, total=100)
    return {"summary": {...}, "schedule": [...]}
```

FastMCP автоматически создаёт описание инструмента (имя, аргументы, тип возврата) из аннотаций
типов и docstring, добавляет его в спецификацию сервера и обрабатывает вызовы с аргументами.

### Как правильно писать описания MCP-тулов

1. **Docstring обязателен.** Первые 1–2 строки — краткое назначение, далее формат входа и выхода.
2. **Описание аргументов** в секции `Args:` — тип, допустимый диапазон, смысл.
3. **Описание возвращаемых данных** в `Returns:` — структура словаря и ключи.
4. **Описание исключений** — при каких условиях поднимается `ValueError`.
5. **Примечания** в `Note:` — округления, коррекции, ограничения.

### Рекомендации по стилю

- Один `FastMCP` на весь сервис (через `mcp_instance.py`).
- Логику расчётов выносить в отдельные модули (в туле — только валидация и вызов).
- Docstring должен быть **самодостаточным**: агент должен понять инструмент только по описанию.
- Строгие аннотации типов (`float`, `int`, `bool`) → FastMCP валидирует вход автоматически.
- Использовать `Context` для логирования и прогресс-отчётов в длительных операциях.
- Добавлять метрики для отслеживания использования инструментов.

---

## 3. Задание

1. Изучить структуру проекта и назначение модулей: `server.py`, `mcp_instance.py`, `metrics.py`,
   `calculations.py`, `validators.py`, `config.py`, каталог `tools/`.
2. Разобрать реализацию четырёх базовых инструментов (раздел 4).
3. Запустить сервер локально и проверить работу инструментов через любой MCP-клиент
   (`tools/list`, затем `tools/call`).
4. Прогнать тесты и разобрать, что покрывают `test_calculations.py` и `test_validators.py`.
5. Выполнить **самостоятельное задание** (раздел 6).
6. Собрать Docker-образ, загрузить в Artifact Registry, развернуть MCP-сервер в AI Agents
   и подключить его к агенту.

---

## 4. Инструменты сервера

### 4.1 `loan_schedule_annuity` — аннуитетный кредит

Расчёт фиксированного ежемесячного платежа и помесячного графика.

- **Параметры:** `principal` (float), `annual_rate_percent` (float), `months` (int)
- **Возвращает:** график платежей с помесячной разбивкой и итоговой сводкой

Формула ежемесячного платежа:

```
M = P · i / (1 − (1 + i)^(−n)),   где i = r / 12
```

Для каждого месяца возвращаются: `payment`, `interest`, `principal_component`,
`remaining_principal`, `cumulative_interest`, `cumulative_principal`.

### 4.2 `loan_schedule_differential` — дифференцированный кредит

Платежи с постоянной частью тела и уменьшающимися процентами.

- тело кредита за месяц постоянно: `P / n`;
- проценты за месяц: `i · остаток`;
- итоговый платёж убывает от месяца к месяцу.

### 4.3 `deposit_schedule_compound` — вклад с капитализацией

График вклада с ежемесячной капитализацией и взносами.

- **Параметры:** `initial_amount`, `annual_rate_percent`, `months`, `monthly_contribution`,
  `contribution_at_beginning` (взнос в начале месяца `True` или в конце `False`).

### 4.4 `compare_loan_schedules` — сравнение кредитов

Сопоставление аннуитетной и дифференцированной схем с одинаковыми параметрами:
общая сумма выплат, переплата, разница в платежах, преимущества каждого типа и рекомендация.

### 4.5 `investment_calculator` — калькулятор инвестиций

Рост инвестиций с регулярными взносами и капитализацией; метрики ROI, прирост капитала,
итоговая сумма и общие взносы.

---

## 5. Этапы выполнения

### Этап 1. Подготовка окружения

```bash
cd lab1-mcp-finance-lab
uv sync
cp .env.example .env
```

В `.env` задаются: `PORT` (по умолчанию 8000), `LOG_LEVEL`, лимиты `MAX_PRINCIPAL`,
`MAX_CONTRIBUTION`, `MAX_MONTHS`, `MAX_RATE`, `MAX_BALANCE_CAP`, опционально `OTEL_ENDPOINT`
и `OTEL_SERVICE_NAME`.

### Этап 2. Запуск сервера

```bash
uv run python src/server.py
```

При старте выводится:

```
🌐 ЗАПУСК MCP СЕРВЕРА — MCP FINANCE
🚀 MCP Server: http://0.0.0.0:8000/mcp
📊 Метрики: http://0.0.0.0:8000/metrics
🏥 Health check: http://0.0.0.0:8000/health
```

Проверка:

```bash
curl http://localhost:8000/health   # OK
curl http://localhost:8000/metrics  # метрики Prometheus
```

### Этап 3. Проверка инструментов

Подключить любой MCP-клиент к `http://localhost:8000/sse`, вызвать `tools/list`,
затем `tools/call` для каждого инструмента. Убедиться, что расчёты корректны,
а при неверных параметрах возвращается код `-32602`.

### Этап 4. Тесты

```bash
PYTHONPATH=src uv run pytest test/ -v
```

Разобрать покрытие:

- `test_calculations.py` — корректность формул, графиков, коррекции последнего платежа;
- `test_validators.py` — границы диапазонов и сообщения об ошибках.

### Этап 5. Самостоятельное задание

См. раздел 6.

### Этап 6. Сборка Docker-образа

```bash
docker buildx build --platform linux/amd64 -t mcp-finance .
docker run --rm -p 8000:8000 -e PORT=8000 mcp-finance
```

> MCP-сервер в AI Agents не должен использовать файловую систему в рантайме —
> все манипуляции выполняются на этапе сборки образа.

### Этап 7. Публикация в Artifact Registry

Пройти аутентификацию по инструкции
локальный Docker-реестр (registry:2 на localhost:5000),
затем:

```bash
docker tag mcp-finance:latest localhost:5000/mcp-finance-repo:v1.0.0
docker push localhost:5000/mcp-finance-repo:v1.0.0
```

### Этап 8. Развёртывание в AI Agents

1. Создать реестр в сервисе Artifact Registry (если ещё не создан).
2. Создать репозиторий для хранения образа.
3. Загрузить образ (этап 7).
4. Запустить MCP-сервер локально из Docker-образа (docker compose --profile lab1).
5. Создать агента и выбрать созданный MCP-сервер в соответствующем поле.
6. Общаться с агентом в чате и убедиться, что инструменты вызываются.

---

## 6. Самостоятельное задание

Реализовать новый инструмент **`investment_calculator`** — расчёт доходности инвестиций
с ежемесячным пополнением.

- **Вход:** начальная сумма, ежемесячный взнос, ставка, срок.
- **Выход:** итоговая сумма и график роста.
- **Требования:** собственный валидатор (переиспользовать `validators.py`) и **не менее 3 тестов**.

**Подсказка:** за образец возьмите `tools/deposit_schedule_compound.py` — он реализует
похожую логику с капитализацией и ежемесячными взносами.

---

## 7. Ключевые инженерные решения

### Единый экземпляр FastMCP

`src/mcp_instance.py`:

```python
from fastmcp import FastMCP
mcp = FastMCP("mcp-finance")
```

Все модули импортируют **этот же объект**. Если создать экземпляр в каждом модуле отдельно,
декораторы `@mcp.tool` зарегистрируют инструменты в разных серверах, и клиент их не увидит.

### Метаданные инструмента в декораторе

```python
@mcp.tool(
    name="loan_schedule_annuity",
    description="""Аннуитетный кредит: расчёт фиксированного
        ежемесячного платежа и помесячного графика.""",
    annotations={"title": "График аннуитетного кредита",
                 "readOnlyHint": True,
                 "idempotentHint": True,
                 "openWorldHint": True},
    tags={"credit", "loan", "annuity", "schedule"},
)
async def loan_schedule_annuity(
    principal: float = Field(..., description="Сумма кредита (> 0)"),
    annual_rate_percent: float = Field(..., description="Годовая ставка, %"),
    months: int = Field(..., description="Срок в месяцах"),
    ctx: Context = None,
) -> ToolResult:
    ...
```

- `annotations` подсказывают агенту свойства инструмента (только чтение, идемпотентность).
- `tags` группируют инструменты.
- `pydantic.Field` с `description` — источник описаний параметров в JSON-схеме.

### Слой валидации

```python
# src/validators.py
def validate_positive_number(name, value, min_inclusive, max_inclusive):
    if not is_finite(value):
        raise ValueError(f"{name}: значение не является конечным числом.")
    if value < min_inclusive:
        raise ValueError(f"{name}: значение должно быть ≥ {min_inclusive}.")
    if value > max_inclusive:
        raise ValueError(f"{name}: значение слишком велико (>{max_inclusive}).")

def check_principal(x: float) -> None:
    validate_positive_number("principal", x, 1e-9, MAX_PRINCIPAL)
```

FastMCP проверяет **типы** по аннотациям. Слой валидаций проверяет **бизнес-ограничения**
(диапазоны, лимиты, конечность значений) и даёт агенту понятные сообщения об ошибках.

### Метрики, трейсинг и коды ошибок

- `TOOL_CALLS`, `CALCULATION_ERRORS`, `API_CALLS` — счётчики Prometheus с лейблами.
- `tracer.start_as_current_span(tool_name)` — OpenTelemetry-спан вокруг расчёта.
- `ValueError` → `McpError(ErrorData(code=-32602))` — неверные параметры.
- Прочие исключения → `McpError(ErrorData(code=-32603))` — внутренняя ошибка.

### Middleware в `server.py`

```python
mcp.add_middleware(FriendlyErrorHandlingMiddleware(...))   # понятные ошибки агенту
mcp.add_middleware(RateLimitingMiddleware(
    max_requests_per_second=50.0, burst_capacity=20))     # защита от перегрузки
mcp.add_middleware(TimingMiddleware())                     # тайминги
mcp.add_middleware(LoggingMiddleware(include_payloads=False,
                                     max_payload_length=500))
```

---

## 8. Структура проекта

```
lab1-mcp-finance-lab/
├── src/
│   ├── mcp_instance.py      # Единый экземпляр FastMCP
│   ├── metrics.py            # Prometheus метрики
│   ├── server.py             # Основной файл сервера, middleware, /metrics, /health
│   ├── calculations.py       # Алгоритмы расчётов
│   ├── validators.py         # Валидация входных данных
│   ├── utils.py              # Вспомогательные функции
│   ├── config.py             # Конфигурационные параметры
│   └── tools/                # Реализация инструментов (@mcp.tool)
├── test/                     # Тесты
├── Dockerfile
├── pyproject.toml
└── .env.example
```

---

## 14. Контрольные вопросы

1. Что такое MCP и зачем он нужен AI-агентам? Какова связь MCP и протокола A2A?
2. Как FastMCP превращает Python-функцию в инструмент? Какую роль играют type hints
   и docstring в генерации схемы?
3. Чем аннуитетный платёж отличается от дифференцированного? Приведите формулы и объясните,
   как это влияет на переплату.
4. Зачем нужен отдельный слой валидации входных данных, если FastMCP уже проверяет типы?
5. Какую роль играют middleware (rate limiting, timing, logging) и как они подключаются?

---

## 10. Критерии приёмки

- [ ] Сервер стартует на `:8000` и отвечает на `/health` и `/metrics`.
- [ ] Все 5 инструментов вызываются и возвращают `summary` и `schedule`.
- [ ] 18 исходных + не менее 3 новых теста проходят.
- [ ] Docker-образ собран под `linux/amd64` и загружен в Artifact Registry.
- [ ] MCP-сервер создан в AI Agents и подключён к агенту.

---

## 12. Как тестировать лабораторную

### 12.1. Запуск MCP-сервера

**Локально (без Docker):**

```powershell
cd lab1-mcp-finance-lab
uv sync
cp .env.example .env
uv run python src/server.py
```

**Через Docker Compose:**

```powershell
docker compose -f docker-compose.local.yaml --profile lab1 up -d --build
```

Сервер запустится на порту **8000**.

### 12.2. Проверка доступности

```powershell
# Health check
curl http://localhost:8000/health
# Ожидаемый ответ: OK

# Prometheus-метрики
curl http://localhost:8000/metrics

# Проверка через check.ps1 (из корня репозитория)
.\check.ps1
# Должно показать: [OK] Lab 1: MCP (Python)
```

### 12.3. Проверка инструментов через MCP-клиент

Запустить инспектор:

```powershell
npx @modelcontextprotocol/inspector
# Transport: HTTP, URL: http://localhost:8000/mcp
```

Или через `curl` (JSON-RPC):

```powershell
# 1. Инициализация сессии
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# 2. Список инструментов
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# 3. Вызов инструмента (аннуитетный кредит: 1 000 000 ₽, 15%, 60 мес.)
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"loan_schedule_annuity","arguments":{"principal":1000000,"annual_rate_percent":15,"months":60}}}'
```

Ожидаемый результат: `monthly_payment ≈ 23 790 ₽`.

### 12.4. Тесты

```powershell
cd lab1-mcp-finance-lab
PYTHONPATH=src uv run pytest test/ -v
```

- `test_calculations.py` — корректность формул, графиков, коррекция последнего платежа;
- `test_validators.py` — границы диапазонов и сообщения об ошибках.

### 12.6. GUI-интерфейс (опционально)

```powershell
# 1. Запустить MCP-сервер (лаб. 1)
cd lab1-mcp-finance-lab
uv sync
cp .env.example .env
uv run python src/server.py

# 2. В новом терминале запустить GUI
cd ..\gui
/c/Users/voyag/AppData/Local/Programs/Python/Python312/python.exe -m pip install -r requirements.txt
/c/Users/voyag/AppData/Local/Programs/Python/Python312/python.exe server.py
# Открыть http://localhost:8080
```

В GUI выбрать вкладку **Lab 1 — MCP Finance**, выбрать инструмент, задать параметры и нажать **Рассчитать**.

### 12.7. Сборка и публикация

```powershell
docker buildx build --platform linux/amd64 -t mcp-finance .
docker run --rm -p 8000:8000 -e PORT=8000 mcp-finance
```

---

## 13. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| Port 8000 занят | Другой процесс слушает порт | Задать другой `PORT` в `.env` |
| `ModuleNotFoundError` | Не настроен путь импорта | `PYTHONPATH=src` или `uv sync` |
| Агент не видит инструменты | MCP-сервер не выбран в UI | Выбрать созданный MCP-сервер в настройках агента |
| Неверные расчёты | Не учтено округление | Денежные величины округляются до 2 знаков; в последний месяц — коррекция, чтобы остаток стал `0.00` |
| Ошибка при импорте метрик | Не установлен `prometheus_client` | `uv sync` |