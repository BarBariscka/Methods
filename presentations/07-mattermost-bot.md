# Лабораторная работа 7. Mattermost-бот для A2A-агента

> | | |
> |---|---|
> | **Каталог** | `lab7-mattermost-bot-for-agents/` |
> | **Точка входа** | `bot.py` |
> | **Технологии** | Python 3.10+, mattermostdriver, a2a SDK, OpenTelemetry / OpenInference, uv |
> | **Транспорт** | WebSocket |
> | **Ориентировочное время** | 3–5 часов |

---

## 1. Цель работы

Разработать бота для корпоративного мессенджера **Mattermost**, интегрированного с A2A-агентом,
с поддержкой streaming-ответов, команд и полной телеметрией через OpenInference.

---

## 2. Теоретическая часть

### Как бот получает события

| Механизм | Как работает | Плюсы | Минусы |
|---|---|---|---|
| **WebSocket** | Постоянное соединение с сервером Mattermost, события приходят сразу | Минимальная задержка, меньше нагрузки | Нужна стабильная сеть, reconnect-логика |
| **Webhooks** | Mattermost отправляет HTTP-запросы на заданный URL | Просто, не требует держать соединение | Нужен публичный адрес, лимиты |
| **Polling** | Бот периодически опрашивает API | Максимально просто | Задержка и лишние запросы |

В этой лабораторной работе используется **WebSocket** через `driver.init_websocket(handler)`.

### Команды бота

- `/a2a help` — справка с доступными skills агента (берётся из `AgentCard`);
- `/a2a status` — статус подключения к A2A-агенту;
- все остальные сообщения передаются напрямую агенту.

### Переменные окружения

| Переменная | Описание | Обязательно |
|---|---|---|
| `MATTERMOST_URL` | URL сервера Mattermost | Да |
| `MATTERMOST_TOKEN` | Токен бота | Да |
| `MATTERMOST_BOT_USERNAME` | Имя пользователя бота (определяется автоматически) | Нет |
| `A2A_BASE_URL` | Базовый URL A2A-агента | Да |
| `A2A_TOKEN` | Токен для доступа к A2A-агенту | Да |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint для экспорта телеметрии | Да |
| `OTEL_SERVICE_NAME` | Имя сервиса (по умолчанию `mattermost-a2a-bot`) | Нет |
| `LOG_LEVEL` | Уровень логирования (по умолчанию `INFO`) | Нет |

---

## 3. Задание

1. Изучить модули: `bot.py`, `a2a_client.py`, `mattermost_handler.py`, `commands.py`,
   `telemetry.py`, `config.py`.
2. Развернуть (или получить доступ к) тестовому Mattermost, создать бота
   в **System Console → Integrations → Bot Accounts** и получить Access Token.
3. Запустить бота.
4. Проверить: ответы на `@bot_name` в канале, прямые сообщения, команды `/a2a help`
   и `/a2a status`, streaming-ответы.
5. **Самостоятельное задание** (раздел 7).
6. Собрать образ (опционально), запустить в Docker.

---

## 4. Этапы выполнения

### Этап 1. Подготовка окружения

```bash
# Linux / Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

cd lab7-mattermost-bot-for-agents
uv pip install -r requirements.txt
```

> `requirements.txt` используется для установки зависимостей,
> `pyproject.toml` — для описания проекта.

### Этап 2. Получение токена Mattermost

1. Войти в Mattermost как администратор.
2. Перейти в **System Console → Integrations → Bot Accounts**.
3. Создать нового бота или использовать существующего.
4. Скопировать **Access Token**.

Альтернативный способ через API:

```bash
# Создать пользователя-бота
curl -X POST https://your-mattermost-server.com/api/v4/users \
  -H "Authorization: Bearer YOUR_PERSONAL_ACCESS_TOKEN" \
  -d '{
    "email": "bot@example.com",
    "username": "a2a-bot",
    "password": "secure_password",
    "nickname": "A2A Bot"
  }'

# Получить токен
curl -X POST https://your-mattermost-server.com/api/v4/users/login \
  -d '{"login_id": "a2a-bot", "password": "secure_password"}'
```

### Этап 3. Настройка `.env`

```bash
cp .env.example .env
```

```bash
# Mattermost Configuration
MATTERMOST_URL=https://your-mattermost-server.com
MATTERMOST_TOKEN=your_mattermost_bot_token
MATTERMOST_BOT_USERNAME=a2a-bot

# A2A Agent Configuration
A2A_BASE_URL=http://localhost:10000 (локальный A2A-агент)
A2A_TOKEN=your_a2a_agent_token

# OpenTelemetry/OpenInference Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=mattermost-a2a-bot

# Logging
LOG_LEVEL=INFO
```

> Если телеметрия не нужна, можно указать фиктивный endpoint — бот продолжит работать,
> но трейсы отправляться не будут.

### Этап 4. Запуск бота

```bash
uv run python bot.py
```

Для разработки: `LOG_LEVEL=DEBUG uv run python bot.py`.

### Этап 5. Проверка работы

Бот должен вывести в логах:

```
INFO - Телеметрия настроена
INFO - A2A клиент инициализирован
INFO - Подключение к Mattermost установлено
INFO - WebSocket соединение установлено, бот готов к работе
```

Далее проверить в Mattermost:

- `/a2a status` — бот отвечает статусом подключения;
- `/a2a help` — бот показывает справку с доступными skills агента;
- `@bot_name Привет!` — бот отвечает через A2A-агента.

### Этап 6. Запуск в Docker (опционально)

```dockerfile
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY requirements.txt ./
COPY . .
RUN uv pip install --system -r requirements.txt

CMD ["uv", "run", "python", "bot.py"]
```

```bash
docker build -t mattermost-bot .
docker run --rm --env-file .env mattermost-bot
```

### Этап 7. Самостоятельное задание

См. раздел 7.

---

## 5. Использование

**Упоминания бота** — в любом канале:

```
@bot_name Рассчитай аннуитетный кредит на 1 000 000 под 12% на 5 лет
```

**Прямые сообщения** — отправить боту личное сообщение в Mattermost.

**Команды:**

- `/a2a help` — показать справку с доступными skills агента;
- `/a2a status` — проверить статус подключения к A2A-агенту;
- остальные команды передаются напрямую в A2A-агент.

---

## 6. Ключевые инженерные решения

### Жизненный цикл бота

```python
# bot.py
class MattermostA2ABot:
    async def initialize(self) -> None:
        setup_telemetry()                       # 1. телеметрия
        self.a2a_client = A2AClientWrapper()
        await self.a2a_client.initialize()      # 2. A2A-клиент
        self.command_handler = CommandHandler(self.a2a_client)
        self.driver = Driver({
            "url": config.MATTERMOST_URL,
            "token": config.MATTERMOST_TOKEN,
            "scheme": "https" if config.MATTERMOST_URL
                            .startswith("https") else "http",
            "port": 443 if config.MATTERMOST_URL
                         .startswith("https") else 80,
        })
        self.driver.login()                     # 3. подключение к Mattermost
        self.mattermost_handler = MattermostHandler(
            driver=self.driver,
            a2a_client=self.a2a_client,
            command_handler=self.command_handler)
        await self.mattermost_handler.initialize()

    async def start(self) -> None:
        self._running = True
        event_handler = self.mattermost_handler.create_event_handler()
        self.driver.init_websocket(event_handler)   # WebSocket
        while self._running:
            await asyncio.sleep(1)
```

Инициализация строго по шагам: любой сбой останавливает старт с понятной ошибкой в логе.

### Обработка команд с трейсами

```python
# commands.py
class CommandHandler:
    async def handle_command(self, command: str,
                             args: list[str]) -> Optional[str]:
        tracer = get_tracer()
        with tracer.start_as_current_span(
                "commands.handle_command") as span:
            set_span_attribute(span, "command.name", command)
            set_span_attribute(span, "command.args_count", len(args))

            if command == "status":
                return "Статус подключения A2A-агента: ..."
            if command == "help":
                return "Доступные skills: ..."
            return None   # не наша команда — передать агенту
```

### Graceful shutdown

```python
def setup_signal_handlers(self) -> None:
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}, останавливаем бота...")
        asyncio.create_task(self.stop())
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
```

### Телеметрия

Бот автоматически отправляет телеметрию через OpenInference:

- traces для всех запросов;
- spans с метаданными (`message_id`, `channel_id`, `user_id`, `response_time`);
- метрики производительности;
- информация о skills агента.

---

## 7. Самостоятельное задание

Добавить две новые команды:

1. **`/a2a agents`** — возвращает список доступных агентов через A2A **Agent Card**.
   Точка входа: метод получения `AgentCard` в `A2AClientWrapper` (`agent_connector.py`).

2. **`/a2a switch <url>`** — переключение на другого агента **без перезапуска бота**.
   Требуется: изменить `self.a2a_client`, переинициализировать клиент, сохранить контекст
   сессии (или начать новую сессию для нового агента).

Пример регистрации команды в `commands.py`:

```python
if command == "agents":
    agents = await self.a2a_client.list_agents()
    return "\n".join(f"• {a}" for a in agents)

if command == "switch":
    if not args:
        return "Использование: /a2a switch <url>"
    ok = await self.a2a_client.switch_agent(args[0])
    return ("Агент переключён" if ok
            else "Не удалось подключиться к агенту")
```

---

## 8. Структура проекта

```
lab7-mattermost-bot-for-agents/
├── bot.py                 # Основной файл бота
├── a2a_client.py          # Обёртка A2A-клиента с телеметрией
├── mattermost_handler.py  # Обработчики событий Mattermost
├── commands.py            # Обработка команд бота
├── telemetry.py           # Настройка OpenInference-телеметрии
├── config.py              # Загрузка конфигурации из env
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 9. Контрольные вопросы

1. Как бот получает события из Mattermost: WebSocket или webhooks, и в чём разница?
2. Как реализован streaming из A2A в чат Mattermost и как он отображается пользователю?
3. Какие метрики и спаны собирает OpenTelemetry и зачем они нужны?
4. Как обеспечить безопасность токенов бота и его доступов?
5. Зачем боту graceful shutdown и какие ресурсы нужно освобождать при остановке?

---

## 10. Критерии приёмки

- [ ] Бот подключается к Mattermost, WebSocket-соединение установлено.
- [ ] Отвечает на упоминания в канале и на прямые сообщения.
- [ ] Команды `/a2a help` и `/a2a status` работают.
- [ ] Streaming-ответы отображаются в чате.
- [ ] Добавлены команды `/a2a agents` и `/a2a switch <url>` (самостоятельное задание).
- [ ] Приложены скриншоты работы в Mattermost.

---

## 11. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| Бот молчит | Неверный токен или нет прав в канале | Проверить логи, токен, добавить бота в канал |
| Ошибка подключения к агенту | Неверные `A2A_BASE_URL` / `A2A_TOKEN` | Проверить URL, доступность агента, сетевые настройки |
| Ошибки телеметрии | Неверный OTLP endpoint | HTTP — порт 4318, gRPC — порт 4317 |
| Бот не показывает skills в help | В `agent_card` нет информации о skills | Проверить структуру ответа A2A-агента, логи |
| Ошибки при остановке | Нет обработки сигналов | Проверить `setup_signal_handlers` |