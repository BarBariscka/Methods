# Лабораторная работа 8. Telegram-бот для A2A-агента

> | | |
> |---|---|
> | **Каталог** | `lab8-telegram-bot-for-agents/` |
> | **Точка входа** | `main.py` |
> | **Технологии** | Python 3.13, aiogram 3, a2a SDK, httpx, pydantic-settings, OpenTelemetry, Poetry |
> | **Токен** | Получить у @BotFather командой `/newbot` |
> | **Ориентировочное время** | 3–5 часов |

---

## 1. Цель работы

Разработать бота на базе `aiogram 3` для взаимодействия с A2A-агентами по URL:
быстрое подключение к агентной системе, переподключение и механизм повторных попыток
при ошибках.

---

## 2. Теоретическая часть

### Возможности бота

1. **Старт и меню** — разделы «Начать работу», «Помощь», «Подключиться по URL».
2. **Подключение к агенту по URL** — вводите URL, и бот подключится к вашему агенту.
3. **Общение с агентом** — пересылайте текстовые запросы и получайте ответы.
4. **Обработка голосовых сообщений** — поддержка транскрипции.
5. **Повтор запроса (Retry)** — при ошибке можно быстро повторить запрос.
6. **История ошибок** — краткая сводка последних ошибок для отладки.

### FSM и состояния диалога в aiogram 3

Finite State Machine позволяет боту помнить **режим** пользователя:

```
Новый пользователь → состояние «ожидает подключения»
     ↓ /start → главное меню
     ↓ «Подключиться по URL» → состояние «ожидает ввода URL»
     ↓ ввод URL → валидация → состояние «подключён»
     ↓ текстовое сообщение → отправка агенту
     ↓ голосовое сообщение → транскрипция → отправка агенту
```

Без FSM бот не поймёт, что означает очередной текст: это URL агента или вопрос к агенту.

### Стратегии повторных попыток (retry)

| Стратегия | Формула задержки | Когда применять |
|---|---|---|
| Фиксированная | `const` | Простые ошибки сети |
| **Экспоненциальная** | `base · 2^attempt` | Временная недоступность сервиса |
| Jitter | `random(base, base·2^attempt)` | Сотни клиентов перезапрашивают одновременно |

В проекте используется экспоненциальная задержка: `2.0 * (2 ** attempt)` для ошибок задачи A2A
и `1.0 * (2 ** attempt)` для сетевых исключений, при **максимум 3 попытках**.

---

## 3. Задание

1. Изучить структуру `src/`: `config` (pydantic-settings), `handlers` (обработчики),
   `keyboards` (клавиатуры меню), `services` (интеграция с агентом, request manager),
   `utils` (команды, сессии, голос).
2. Создать бота через @BotFather и настроить `.env` по образцу `.env.example`.
3. Запустить бота.
4. Проверить сценарии: старт и меню, подключение по URL, текстовый диалог с агентом,
   голосовое сообщение (транскрипция), retry при ошибке, история ошибок.
5. **Самостоятельное задание** (раздел 7).

---

## 4. Этапы выполнения

### Этап 1. Подготовка окружения

```bash
# Linux / Mac
curl -sSL https://install.python-poetry.org | python3-

# Windows
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Или
pip install poetry
```

```bash
cd lab8-telegram-bot-for-agents
poetry install --only main    # или poetry install с dev-зависимостями
```

### Этап 2. Создание бота

1. Открыть Telegram и найти [@BotFather](https://t.me/botfather).
2. Отправить команду `/newbot`.
3. Следовать инструкциям для создания бота.
4. Скопировать полученный токен.

### Этап 3. Настройка `.env`

```bash
cp .env.example .env
```

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_BOT_USERNAME=your_bot_username

# A2A Agent Configuration
PUBLIC_URL=http://localhost:10000 (локальный A2A-агент)

# Optional: Message handling
HANDLE_MESSAGE_EDITS=true
HANDLE_MESSAGE_DELETES=false
EDIT_RESPONSE_TIMEOUT=30
```

### Этап 4. Запуск бота

```bash
poetry run python main.py
```

В логах должно быть:

```
Bot started
Bot started with request manager
```

### Этап 5. Проверка работы

1. Отправить боту `/start` — бот отвечает приветственным сообщением с меню.
2. Нажать «🚀 Начать работу» → «🔌 Подключиться к чату» — бот подключается к агенту
   и показывает статус.
3. Отправить текстовое сообщение — бот пересылает его агенту и возвращает ответ.

### Этап 6. Проверка дополнительных сценариев

- **Голосовое сообщение** — бот транскрибирует его и отправляет агенту.
- **Retry** — при ошибке появляется кнопка «🔄 Retry», нажатие повторяет запрос.
- **История ошибок** — бот показывает сводку последних ошибок для отладки.

### Этап 7. Самостоятельное задание

См. раздел 7.

### Этап 8. Запуск в Docker (опционально)

В проекте есть готовый многоэтапный `Dockerfile` с Poetry:

```bash
docker build -t tg-bot:latest .
docker run --rm --env-file .env tg-bot:latest
```

Или через docker-compose:

```yaml
version: '3.8'
services:
  telegram-bot:
    build: .
    container_name: telegram-a2a-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
```

```bash
docker-compose up -d
docker-compose logs -f
```

---

## 5. Переменные окружения

| Переменная | Описание | Обязательно |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота от BotFather | Да |
| `TELEGRAM_BOT_USERNAME` | Юзернейм бота (без `@`) | Да |
| `PUBLIC_URL` | URL A2A-агента | Да |
| `HANDLE_MESSAGE_EDITS` | Обрабатывать изменённые сообщения (по умолчанию `true`) | Нет |
| `HANDLE_MESSAGE_DELETES` | Игнорировать удалённые сообщения (по умолчанию `false`) | Нет |
| `EDIT_RESPONSE_TIMEOUT` | Таймаут для отмены старого запроса, секунды (по умолчанию `30`) | Нет |

Дополнительно можно настроить переменные OpenTelemetry (`OTEL_EXPORTER_OTLP_ENDPOINT` и др.),
если требуется экспорт трейсов.

---

## 6. Ключевые инженерные решения

### AgentConnector: обмен с агентом и retry

```python
# src/services/agent_connector.py
class AgentConnector:
    def __init__(self, agent_url: str):
        if not agent_url.endswith('/'):
            agent_url += '/'
        self.agent_url = agent_url
        self.session = httpx.AsyncClient(
            base_url=agent_url,
            timeout=httpx.Timeout(180.0, connect=30.0))
        self.tracer = trace.get_tracer(__name__)
        self.request_id = 0

    async def send_message(self, text_msg: str,
                           max_retries: int = 3) -> str:
        with self.tracer.start_as_current_span(
            "agent_connector_send_message",
            attributes={"agent.url": self.agent_url,
                        "input.message": text_msg,
                        "max_retries": max_retries}) as span:
            for attempt in range(max_retries):
                try:
                    result = await self._send_single_message(
                        text_msg, span, attempt + 1)

                    # Проверяем, не содержит ли ответ признак провала задачи A2A
                    if self._is_a2a_task_failure(result):
                        if attempt < max_retries - 1:
                            retry_delay = 2.0 * (2 ** attempt)  # backoff
                            logger.warning(
                                f"a2a task failed, retrying in "
                                f"{retry_delay}s "
                                f"(attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            continue
                        return result
                    return result

                except Exception as e:
                    error_id = str(uuid.uuid4())
                    if attempt < max_retries - 1:
                        retry_delay = 1.0 * (2 ** attempt)
                        await asyncio.sleep(retry_delay)
                    else:
                        span.record_exception(e)
                        span.set_status(trace.Status(
                            trace.StatusCode.ERROR, str(e)))
                        return (f"🚨 Задача не выполнена за "
                                f"{max_retries} попыток (ID: {error_id})\n"
                                f"• Ошибка: {str(e)}")
```

### Распознавание провала задачи A2A

```python
    def _is_a2a_task_failure(self, response_text: str) -> bool:
        """Проверяет, что ответ указывает на провал, который стоит повторить."""
        try:
            if response_text.strip().startswith('{'):
                response_data = json.loads(response_text)
                if isinstance(response_data, dict):
                    # структура проваленной задачи a2a
                    if (response_data.get('kind') == 'task' and
                        response_data.get('status', {}).get('state')
                        == 'failed'):
                        return True
                    # распространённые повторяемые коды ошибок
                    if ('error' in response_data and
                        response_data.get('error', {}).get('code')
                        in [-32000, -32603]):
                        return True

            # текстовые маркеры повторяемых ошибок
            retryable_patterns = ['Task failed', 'failed', 'timeout',
                                  'connection', 'network']
            ...
```

Важно: не вся ошибка повторяема. Ошибка валидации запроса (`-32602`) повторять бессмысленно —
пользователь должен изменить ввод. Повторяются только сетевые сбои и временная
недоступность сервиса.

### RequestManager

Управляет конкурентными запросами: если пользователь отредактировал сообщение, предыдущий
запрос отменяется по таймауту `EDIT_RESPONSE_TIMEOUT` — иначе пользователь получит
два недетерминированных ответа на один вопрос.

### Структура проекта

```
lab8-telegram-bot-for-agents/
├── main.py                 # Точка входа бота
├── Dockerfile              # Docker-образ (многоэтапная сборка с Poetry)
├── docker-compose.yaml
├── pyproject.toml
├── poetry.lock
├── .env.example
└── src/
    ├── config/
    │   └── config.py       # Конфигурация через pydantic-settings
    ├── handlers/
    │   └── common.py       # Обработчики команд и сообщений
    ├── keyboards/
    │   └── __init__.py     # Клавиатуры для меню
    ├── models/
    │   └── __init__.py
    ├── services/
    │   ├── agent_connector.py  # Интеграция с A2A-агентом
    │   └── request_manager.py  # Управление запросами
    └── utils/
        ├── commands.py     # Команды бота
        ├── session.py      # Управление сессиями
        └── voice_processor.py  # Обработка голосовых сообщений
```

---

## 7. Самостоятельное задание

1. Добавить команду **`/history`**, возвращающую последние **N** сообщений сессии.
2. Реализовать **сохранение истории сессии между перезапусками**, например в SQLite.

Минимальная схема таблицы:

```sql
CREATE TABLE messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    role        TEXT    NOT NULL,   -- 'user' | 'agent'
    content     TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session ON messages(session_id, created_at);
```

Обработчик команды:

```python
@router.message(Command("history"))
async def cmd_history(message: Message,
                      history: HistoryRepo,
                      count: int = 10) -> None:
    session_id = str(message.chat.id)
    rows = await history.last(session_id, limit=count)
    if not rows:
        await message.answer("История пуста.")
        return
    lines = [f"{'👤 Вы' if r.role == 'user' else '🤖 Агент'}: {r.content}"
             for r in rows]
    await message.answer("\n\n".join(lines))
```

**Критерии проверки:** после перезапуска бота команда `/history` возвращает сообщения
предыдущей сессии.

---

## 8. Контрольные вопросы

1. Как устроены FSM и состояния диалога в aiogram 3 и зачем они нужны боту с подключением?
2. Как реализовано переподключение к агенту по URL и как обрабатывается неверный URL?
3. Как выполняется транскрипция голосовых сообщений и что происходит при её ошибке?
4. Какие стратегии retry применяются и почему используется экспоненциальная задержка?
5. Как отличить повторяемую ошибку от неповторяемой? Почему нельзя повторять все ошибки?

---

## 9. Критерии приёмки

- [ ] Бот запускается, `/start` открывает главное меню.
- [ ] Подключение по URL работает, отображается статус подключения.
- [ ] Текстовый диалог с агентом возвращает ответы.
- [ ] Голосовое сообщение транскрибируется и обрабатывается агентом.
- [ ] При ошибке появляется кнопка Retry, ведётся история ошибок.
- [ ] Добавлена команда `/history` и сохранение истории сессии (самостоятельное задание).

---

## 10. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| Бот не запускается | Не заданы `TELEGRAM_BOT_TOKEN` / `TELEGRAM_BOT_USERNAME` | Проверить `.env`, корректность токена, логи |
| Нет ответа от агента | Неверный `PUBLIC_URL` или сетевая недоступность | Проверить URL, доступность агента, логи подключения |
| Ошибки зависимостей | Рассинхроновка lock-файла | `poetry lock --no-update && poetry install` |
| Проблемы с SSL/сертификатами | Самоподписанный сертификат агента | В образ добавлены `ca-certificates`; проверить доверие сертификату |
| Голос не обрабатывается | Недоступен сервис транскрипции | Проверить зависимости аудио и сервисы транскрипции (Whisper, Google Speech) |
| Бот отвечает на всё подряд | Не настроен FSM | Проверить состояния диалога в `handlers/common.py` |