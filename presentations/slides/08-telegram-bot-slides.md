# Лабораторная работа 8. Telegram-бот для A2A-агента
## Слайды с пояснениями

---

## Слайд 1. Титульный

**Telegram-бот для A2A-агента**

- Каталог: `lab8-telegram-bot-for-agents/`
- Точка входа: `bot.py`
- Технологии: Python 3.10+, aiogram 3.x, a2a SDK, uv
- Транспорт: long polling
- Время: 3–5 часов

> **Пояснение:** Telegram — самый доступный мессенджер для быстрого прототипирования. Бот создаётся за минуты через @BotFather. В отличие от Mattermost (лаб. 7), здесь long polling вместо WebSocket, есть FSM и поддержка голосовых сообщений.

---

## Слайд 2. Цель работы

**Создать Telegram-бота, интегрированного с A2A-агентом:**

- Обработка текстовых и голосовых сообщений
- FSM (машина состояний) для многошаговых диалогов
- Retry-логика и graceful shutdown

> **Пояснение:** Бот принимает сообщение от пользователя, отправляет его A2A-агенту и возвращает ответ. Дополнительно: распознавание голоса, многошаговые диалоги через FSM, устойчивость к сбоям через retry.

---

## Слайд 3. Получение токена бота

1. Открыть **@BotFather** в Telegram.
2. Отправить команду `/newbot`.
3. Указать имя бота и его username (должен заканчиваться на `bot`).
4. Скопировать выданный **токен**.

> **Пояснение:** @BotFather — официальный сервис Telegram для управления ботами. Он выдаёт токен — «пароль» бота. Username обязан заканчиваться на `bot` (например, `my_a2a_bot`). Токен выглядит как `123456789:AAH...`.

---

## Слайд 4. Настройка `.env`

```bash
cd lab8-telegram-bot-for-agents
cp .env.example .env
```

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# A2A Agent Configuration
A2A_BASE_URL=http://localhost:10000 (локальный A2A-агент)
A2A_TOKEN=your_a2a_agent_token

# Logging
LOG_LEVEL=INFO
```

> **Пояснение:** `TELEGRAM_BOT_TOKEN` — доступ к Telegram. `A2A_BASE_URL` и `A2A_TOKEN` — доступ к агенту из лаб. 2–6. `LOG_LEVEL` — подробность логов. Все секреты — только в `.env`, никогда в коде.

---

## Слайд 5. Запуск бота

```bash
uv pip install -r requirements.txt
uv run python bot.py
```

**Для разработки:** `LOG_LEVEL=DEBUG uv run python bot.py`

> **Пояснение:** `requirements.txt` — для установки зависимостей, `pyproject.toml` — для описания проекта. `LOG_LEVEL=DEBUG` показывает больше информации в логах — полезно при отладке.

---

## Слайд 6. Проверка работы

Бот должен вывести в логах:

```
INFO - A2A клиент инициализирован
INFO - Запуск Telegram бота...
```

**Далее проверить в Telegram:**
- `/start` — бот приветствует и показывает доступные команды;
- `Привет!` — бот отвечает через A2A-агента;
- `/reset` — сброс контекста диалога.

> **Пояснение:** `/start` — обязательная команда Telegram-бота, точка входа. `/reset` очищает историю диалога. Обычное сообщение уходит агенту. Если бот молчит — смотрите логи.

---

## Слайд 7. Жизненный цикл бота

```python
# bot.py
async def main():
    config = get_config()
    logging.basicConfig(level=config.LOG_LEVEL)

    a2a_client = A2AClientWrapper()
    await a2a_client.initialize()

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(main_router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await a2a_client.close()
        await bot.session.close()
```

> **Пояснение:** aiogram 3 использует Dispatcher и Router. `delete_webhook(drop_pending_updates=True)` очищает старые апдейты при старте. Блок `finally` гарантирует освобождение ресурсов даже при ошибке — это и есть graceful shutdown.

---

## Слайд 8. FSM — машина состояний

```python
# handlers.py
class DialogStates(StatesGroup):
    waiting_for_message = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: StateMemory):
    await state.set_state(DialogStates.waiting_for_message)
    await message.answer("Привет! Напишите сообщение для агента.")

@router.message(F.text, DialogStates.waiting_for_message)
async def handle_text(message: Message, a2a_client: A2AClientWrapper):
    async with message.chat.action_typing():
        response = await a2a_client.send_message(message.text)
    await message.answer(response)
```

> **Пояснение:** FSM (Finite State Machine) — «конечный автомат», хранит состояние диалога. `StatesGroup` — группа состояний, `State` — конкретное состояние. `set_state` переключает состояние, `F.text` — фильтр «это текстовое сообщение». Так строится многошаговый диалог.

---

## Слайд 9. Retry-логика

```python
# a2a_client.py
async def send_message(self, text: str,
                       max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return await self._send_once(text)
        except (TimeoutError, ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            delay = 2 ** attempt          # 1, 2, 4 секунды
            logger.warning(f"Повтор {attempt + 1} через {delay}с: {e}")
            await asyncio.sleep(delay)
```

> **Пояснение:** Retry — повторная попытка при сбое. Сетевые запросы к агенту могут отваливаться. Экспоненциальная задержка (`2 ** attempt`) — «умный» retry: чем больше попыток, тем дольше ждём, чтобы не «задавить» сервер.

---

## Слайд 10. Обработка голосовых сообщений

```python
# handlers.py
@router.message(F.voice, DialogStates.waiting_for_message)
async def handle_voice(message: Message, bot: Bot,
                       a2a_client: A2AClientWrapper):
    file = await bot.get_file(message.voice.file_id)
    audio = await bot.download_file(file.file_path)
    text = await transcribe(audio)        # распознавание речи
    async with message.chat.action_typing():
        response = await a2a_client.send_message(text)
    await message.answer(response)
```

> **Пояснение:** Голосовое сообщение — это аудиофайл. Бот скачивает его по `file_id`, распознаёт речь в текст (STT — speech-to-text) и отправляет текст агенту. Ответ возвращается как текст. Это расширяет каналы ввода.

---

## Слайд 11. Структура проекта

```
lab8-telegram-bot-for-agents/
├── bot.py             # Точка входа, запуск polling
├── handlers.py        # Хендлеры команд и сообщений
├── a2a_client.py      # A2A-клиент с retry
├── config.py          # Загрузка конфигурации из env
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

> **Пояснение:** `bot.py` — точка входа и жизненный цикл, `handlers.py` — обработчики команд и сообщений, `a2a_client.py` — клиент к агенту с retry, `config.py` — настройки. Минимальная, но полная структура.

---

## Слайд 12. Сравнение: Mattermost vs Telegram

| Критерий | Mattermost (лаб. 7) | Telegram (лаб. 8) |
|---|---|---|
| Транспорт | WebSocket | Long polling |
| Команды | `/a2a help`, `/a2a status` | `/start`, `/reset` |
| FSM | — | `StatesGroup` / `State` |
| Голосовые | — | `F.voice` + STT |
| Телеметрия | OpenTelemetry/OpenInference | Логи |
| Аудитория | Корпоративная | Публичная |
| Создание бота | Через админ-панель | Через @BotFather |

> **Пояснение:** Mattermost — корпоративный канал: WebSocket, команды, телеметрия. Telegram — публичный: long polling, FSM, голосовые. Выбор зависит от аудитории и требований к надёжности.

---

## Слайд 13. Самостоятельное задание

1. **Поддержка изображений** — принимать фото (`F.photo`), извлекать текст (OCR) и отправлять агенту.
2. **Кнопки и inline-меню** — `InlineKeyboardMarkup` для быстрых действий.
3. **Лимит на длину ответа** — Telegram ограничивает сообщение 4096 символами; разбивать длинные ответы агента на части.

```python
@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    file = await bot.get_file(message.photo[-1].file_id)
    image = await bot.download_file(file.file_path)
    text = await ocr(image)               # распознавание текста
    ...
```

> **Пояснение:** Изображения обрабатываются как голосовые: скачиваем по `file_id`, распознаём (OCR), отправляем агенту. Inline-кнопки улучшают UX. Разбиение длинных ответов — обязательное требование Telegram.

---

## Слайд 14. Критерии приёмки

- [ ] Бот отвечает на `/start`, `/reset` и текстовые сообщения.
- [ ] Голосовые сообщения распознаются и обрабатываются.
- [ ] FSM корректно ведёт многошаговый диалог.
- [ ] Retry срабатывает при недоступности агента.
- [ ] Ресурсы корректно освобождаются при остановке.
- [ ] Приложены скриншоты переписки с ботом.

> **Пояснение:** Чек-лист для защиты. Преподаватель проверит: команды работают, голос распознаётся, FSM ведёт диалог, retry срабатывает, ресурсы освобождаются.

---

## Слайд 15. Типичные ошибки

| Проблема | Причина | Решение |
|---|---|---|
| Бот не запускается | Неверный `TELEGRAM_BOT_TOKEN` | Проверить токен в @BotFather |
| Конфликт polling | Бот запущен в двух местах | Остановить второй экземпляр |
| Бот молчит на сообщения | Нет хендлера для состояния | Проверить FSM и фильтры `F.text` |
| Ошибка 4096 символов | Ответ агента слишком длинный | Разбивать ответ на части |
| Ошибка подключения к агенту | Неверные `A2A_BASE_URL` / `A2A_TOKEN` | Проверить URL и доступность агента |

> **Пояснение:** Частая ошибка — «конфликт polling»: Telegram разрешает только одно активное соединение на бота. Если запустить бота дважды — второй не заработает. Вторая — длинные ответы: Telegram режет сообщения свыше 4096 символов.

---

## Слайд 16. Контрольные вопросы

1. Чем long polling отличается от WebSocket и webhooks?
2. Что такое FSM и зачем она нужна в диалогах с агентом?
3. Как работает retry с экспоненциальной задержкой?
4. Как обработать голосовое сообщение от получения до ответа?
5. Почему важно освобождать ресурсы в блоке `finally`?

> **Пояснение:** Long polling — «долгий опрос»: клиент ждёт ответа от сервера. FSM — «конечный автомат» для диалогов. Retry — повтор при сбое. `finally` гарантирует очистку ресурсов даже при ошибке.

---

## Слайд 17. Итоги

**Что мы сделали:**
- Создали Telegram-бота для общения с A2A-агентом
- Настроили long polling и FSM
- Добавили retry и обработку голосовых сообщений
- Сравнили два канала доставки (Mattermost и Telegram)

**Что дальше (лаб. 9):**
- Соберём мультиагентную систему
- Научим агентов общаться друг с другом
- Освоим маршрутизацию и агрегацию ответов

> **Пояснение:** Лабораторная 8 — «публичный» канал: long polling, FSM, голос. Мы завершили цикл интеграции агента в мессенджеры. В лаб. 9 переходим к мультиагентным системам — взаимодействию нескольких агентов между собой.
