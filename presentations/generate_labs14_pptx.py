#!/usr/bin/env python3
"""
Генерация презентаций (.pptx) для лабораторных работ 1–4.
Формат совместим с WPS Office (используется python-pptx).

Запуск:
    pip install python-pptx
    python generate_labs14_pptx.py
"""

import os
import sys

# В консоли Windows кодировка по умолчанию cp1251 — print() с эмодзи падает.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Цветовая палитра ──────────────────────────────────────────────
BG_DARK      = RGBColor(0x1A, 0x1A, 0x2E)   # тёмно-синий фон
BG_MID       = RGBColor(0x16, 0x21, 0x3E)   # фон слайдов
ACCENT_BLUE  = RGBColor(0x00, 0xD2, 0xFF)   # голубой акцент
ACCENT_GREEN = RGBColor(0x00, 0xE6, 0x76)   # зелёный акцент
ACCENT_PURPLE= RGBColor(0xBB, 0x86, 0xFC)   # фиолетовый акцент
ACCENT_ORANGE= RGBColor(0xFF, 0x91, 0x00)   # оранжевый акцент
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xB0, 0xBE, 0xC5)
CODE_BG      = RGBColor(0x0D, 0x11, 0x17)   # фон кода
CARD_BG      = RGBColor(0x1E, 0x2A, 0x45)   # фон карточек

LAB_COLORS = {
    1: ACCENT_BLUE,
    2: ACCENT_GREEN,
    3: ACCENT_PURPLE,
    4: ACCENT_ORANGE,
}

# ── Вспомогательные функции ───────────────────────────────────────

def set_slide_bg(slide, color):
    """Устанавливает фон слайда."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape_bg(slide, left, top, width, height, color, alpha=None):
    """Добавляет прямоугольник-фон."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    if alpha is not None:
        shape.fill.fore_color.brightness = alpha
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=14,
                 color=WHITE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    """Добавляет текстовый блок."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_bullet_list(slide, left, top, width, height, items, font_size=13,
                    color=LIGHT_GRAY, bullet_color=None):
    """Добавляет маркированный список."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.space_after = Pt(4)
        p.level = 0
    return txBox


def add_code_block(slide, left, top, width, height, code_text, font_size=10):
    """Добавляет блок кода с тёмным фоном."""
    # Фон
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = CODE_BG
    shape.line.fill.background()

    # Текст
    txBox = slide.shapes.add_textbox(
        left + Inches(0.1), top + Inches(0.05),
        width - Inches(0.2), height - Inches(0.1)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    for line in code_text.strip().split("\n"):
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = line
        p.font.size = Pt(font_size)
        p.font.color.rgb = ACCENT_GREEN
        p.font.name = "Consolas"
        p.space_after = Pt(1)
    return txBox


def add_accent_bar(slide, left, top, width, height, color):
    """Добавляет цветную полоску-акцент."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_card(slide, left, top, width, height, title, body_lines, accent_color, font_size=12):
    """Добавляет карточку с заголовком и телом."""
    # Фон карточки
    card = add_shape_bg(slide, left, top, width, height, CARD_BG)

    # Акцентная полоска сверху
    add_accent_bar(slide, left, top, width, Inches(0.06), accent_color)

    # Заголовок
    add_text_box(slide, left + Inches(0.15), top + Inches(0.12),
                 width - Inches(0.3), Inches(0.3),
                 title, font_size=13, color=WHITE, bold=True)

    # Тело
    txBox = slide.shapes.add_textbox(
        left + Inches(0.15), top + Inches(0.4),
        width - Inches(0.3), height - Inches(0.5)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(body_lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(font_size)
        p.font.color.rgb = LIGHT_GRAY
        p.font.name = "Calibri"
        p.space_after = Pt(2)

    return card


def add_slide_number(slide, num, total):
    """Добавляет номер слайда в правый нижний угол."""
    add_text_box(slide, Inches(8.5), Inches(7.0), Inches(1.2), Inches(0.3),
                 f"{num}/{total}", font_size=10, color=LIGHT_GRAY,
                 alignment=PP_ALIGN.RIGHT)


def add_section_header(slide, section_num, section_title, accent_color):
    """Добавляет заголовок секции на слайд."""
    add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.08), accent_color)
    add_text_box(slide, Inches(0.6), Inches(0.3), Inches(8.5), Inches(0.5),
                 f"СЕКЦИЯ {section_num}", font_size=11, color=accent_color, bold=True)
    add_text_box(slide, Inches(0.6), Inches(0.7), Inches(8.5), Inches(0.6),
                 section_title, font_size=22, color=WHITE, bold=True)


# ── Контент презентаций ───────────────────────────────────────────

LABS_DATA = {
    1: {
        "title": "MCP-сервер финансовых расчётов",
        "subtitle": "Лабораторная работа 1",
        "tech": "Python 3.12 · FastMCP · Docker · uv",
        "sections": [
            {
                "title": "Цель работы",
                "items": [
                    "Освоить разработку MCP-сервисов на Python с FastMCP",
                    "Описание инструментов для AI-агента",
                    "Валидация входных данных, тестирование",
                    "Контейнеризация и развёртывание в Docker Compose",
                ],
            },
            {
                "title": "Что такое MCP-сервер",
                "items": [
                    "MCP — Model Context Protocol: протокол «агент ↔ инструменты»",
                    "Сервис предоставляет набор инструментов (tools)",
                    "FastMCP берёт на себя: транспорт, регистрацию, сериализацию",
                    "Поддержка метрик Prometheus и OpenTelemetry",
                ],
            },
            {
                "title": "Инструменты сервера",
                "items": [
                    "loan_schedule_annuity — аннуитетный кредит",
                    "loan_schedule_differential — дифференцированный кредит",
                    "deposit_schedule_compound — вклад с капитализацией",
                    "compare_loan_schedules — сравнение схем погашения",
                    "investment_calculator — калькулятор инвестиций",
                ],
            },
            {
                "title": "Запуск и проверка",
                "items": [
                    "Локально: uv run python src/server.py (порт 8000)",
                    "Docker: docker compose --profile lab1 up -d --build",
                    "Health: curl http://localhost:8000/health → OK",
                    "Метрики: curl http://localhost:8000/metrics",
                    "Тесты: PYTHONPATH=src uv run pytest test/ -v (18 тестов)",
                    "GUI: uv run python gui/server.py → http://localhost:8090",
                ],
            },
            {
                "title": "Запуск в Docker",
                "items": [
                    "Сборка образа: docker build -t lab1-mcp-finance .",
                    "Запуск: docker run --rm -p 8000:8000 lab1-mcp-finance",
                    "Через Compose (из корня репозитория):",
                    "docker compose -f docker-compose.local.yaml --profile lab1 up -d --build",
                    "Проверка: curl http://localhost:8000/health → OK",
                    "Остановка: docker compose ... --profile lab1 down",
                ],
                "code": """# Сборка и запуск
docker build -t lab1-mcp-finance .
docker run --rm -p 8000:8000 lab1-mcp-finance

# Или через Compose
docker compose -f docker-compose.local.yaml \\
  --profile lab1 up -d --build

# Проверка
curl http://localhost:8000/health   # OK
curl http://localhost:8000/metrics

# Остановка
docker compose -f docker-compose.local.yaml \\
  --profile lab1 down""",
            },
            {
                "title": "Развёртывание Ollama на хосте",
                "items": [
                    "Лаб. 1 — MCP-сервер: LLM не нужна, сервис самодостаточен",
                    "Ollama требуется агентам лаб. 2–4 (вызов инструментов)",
                    "1. Установить Ollama: https://ollama.com/download",
                    "2. Запустить сервис: ollama serve (слушает 127.0.0.1:11434)",
                    "3. Скачать модель: ollama pull llama3.2:3b",
                    "4. Проверить: ollama list / curl http://localhost:11434/api/tags",
                ],
                "code": """# 1. Установить Ollama (Windows/macOS/Linux)
#    https://ollama.com/download

# 2. Запустить сервис (в отдельном терминале)
ollama serve            # 127.0.0.1:11434

# 3. Скачать модель
ollama pull llama3.2:3b

# 4. Проверить
ollama list
curl http://localhost:11434/api/tags""",
            },
            {
                "title": "Развёртывание Ollama в Docker",
                "items": [
                    "Изоляция: своя Ollama и модели в отдельном volume",
                    "1. Поднять контейнер: docker compose ... up -d ollama",
                    "2. Скачать модель ВНУТРЬ контейнера (volume пустой)",
                    "3. Проверить: docker exec -it pis-ollama ollama list",
                    "Агенты в сети pis-net: http://pis-ollama:11434",
                    "⚠️ Порт 11434 конфликтует с хостовой Ollama — остановите её",
                ],
                "code": """# 1. Поднять Ollama в контейнере
docker compose -f docker-compose.local.yaml up -d ollama

# 2. Скачать модель внутрь контейнера
docker exec -it pis-ollama ollama pull llama3.2:3b

# 3. Проверить
docker exec -it pis-ollama ollama list
curl http://localhost:11434/api/tags

# Агенты в pis-net: LLM_API_BASE=http://pis-ollama:11434""",
            },
            {
                "title": "Структура проекта",
                "code": """lab1-mcp-finance-lab/
├── src/
│   ├── mcp_instance.py      # Единый экземпляр FastMCP
│   ├── metrics.py            # Prometheus метрики
│   ├── server.py             # Сервер, middleware, /metrics, /health
│   ├── calculations.py       # Алгоритмы расчётов
│   ├── validators.py         # Валидация входных данных
│   └── tools/                # Инструменты (@mcp.tool)
├── test/                     # Тесты (pytest)
├── gui/                      # Веб-интерфейс
├── Dockerfile
└── pyproject.toml""",
            },
            {
                "title": "GUI-интерфейс (единый для всех лаб)",
                "items": [
                    "Запустить MCP-сервер: uv run python src/server.py (порт 8000)",
                    "Запустить GUI: python gui/server.py (порт 8090)",
                    "Открыть http://localhost:8090",
                    "Вкладка Lab 1 — MCP Finance: выбрать инструмент, задать параметры, нажать Рассчитать",
                    "Результат отображается в блоке вывода под кнопкой",
                    "Поддерживаются 5 инструментов: аннуитетный, дифференцированный кредит, вклад, инвестиции, сравнение",
                ],
            },
            {
                "title": "Ключевые решения",
                "items": [
                    "Единый экземпляр FastMCP через mcp_instance.py",
                    "Слой валидации: бизнес-ограничения (диапазоны, лимиты)",
                    "Middleware: rate limiting, timing, logging, error handling",
                    "Метрики: TOOL_CALLS, CALCULATION_ERRORS, API_CALLS",
                    "Трейсинг: OpenTelemetry spans вокруг каждого расчёта",
                ],
            },
            {
                "title": "Критерии приёмки",
                "items": [
                    "✅ Сервер стартует на :8000, отвечает на /health и /metrics",
                    "✅ Все 5 инструментов вызываются и возвращают summary + schedule",
                    "✅ 18 исходных + ≥ 3 новых теста проходят",
                    "✅ Docker-образ собран под linux/amd64",
                    "✅ MCP-сервер развёрнут в AI Agents и подключён к агенту",
                ],
            },
        ],
    },
    2: {
        "title": "Агент на Google ADK",
        "subtitle": "Лабораторная работа 2",
        "tech": "Python 3.12 · Google ADK · A2A SDK · LiteLLM · Docker",
        "sections": [
            {
                "title": "Цель работы",
                "items": [
                    "Определить агента в Google ADK (Agent Development Kit)",
                    "Обёртка в A2A-сервис (Agent-to-Agent протокол)",
                    "Сборка Docker-образа и запуск в AI Agents",
                    "Интеграция с MCP-сервером из лаб. 1",
                ],
            },
            {
                "title": "Google ADK: ключевые абстракции",
                "items": [
                    "Agent — имя, описание, инструкция, модель, инструменты",
                    "Toolset — группа инструментов, включая MCP-подключение",
                    "Session Service — управление историей диалога",
                    "Runner — цикл исполнения задачи агента",
                ],
            },
            {
                "title": "A2A-протокол",
                "items": [
                    "Агент публикует AgentCard (имя, версия, URL, skills)",
                    "Обработка задач по HTTP/SSE с JSON-RPC",
                    "Поддержка streaming — ответы чанками",
                    "Task store — хранение состояния задач",
                ],
            },
            {
                "title": "Запуск и проверка",
                "items": [
                    "Локально: LLM_API_KEY=dummy uv run python src/start_a2a.py",
                    "Docker: docker compose --profile lab2 up -d --build",
                    "Порт хоста: 8002 (внутренний: 10000)",
                    "Agent Card: curl http://localhost:8002/.well-known/agent-card.json",
                    "Проверка: .\\check.ps1 → [OK] Lab 2: ADK A2A",
                ],
            },
            {
                "title": "Запуск в Docker",
                "items": [
                    "Сборка образа: docker build -t lab2-adk-agent .",
                    "Запуск: docker run -p 8002:10000 с переменными окружения",
                    "MCP и Ollama доступны через host.docker.internal",
                    "Через Compose (из корня репозитория):",
                    "docker compose -f docker-compose.local.yaml --profile lab2 up -d --build",
                    "Порт хоста 8002 → внутренний 10000",
                ],
                "code": """# Сборка
docker build -t lab2-adk-agent .

# Запуск контейнера
docker run --rm -p 8002:10000 \\
  -e MCP_URL=http://host.docker.internal:8000/mcp \\
  -e LLM_API_BASE=http://host.docker.internal:11434 \\
  -e LLM_MODEL=ollama_chat/llama3.2:3b \\
  -e LLM_API_KEY=dummy \\
  --add-host=host.docker.internal:host-gateway \\
  lab2-adk-agent

# Или через Compose
docker compose -f docker-compose.local.yaml \\
  --profile lab2 up -d --build""",
            },
            {
                "title": "Развёртывание Ollama на хосте",
                "items": [
                    "1. Установить Ollama: https://ollama.com/download",
                    "2. Запустить сервис: ollama serve (слушает 127.0.0.1:11434)",
                    "3. Скачать модель: ollama pull llama3.2:3b",
                    "4. Проверить: ollama list / curl http://localhost:11434/api/tags",
                    "Агент в контейнере: LLM_API_BASE=http://host.docker.internal:11434",
                    "Формат модели (LiteLLM): ollama_chat/llama3.2:3b",
                ],
                "code": """# 1. Установить Ollama (Windows/macOS/Linux)
#    https://ollama.com/download

# 2. Запустить сервис (в отдельном терминале)
ollama serve            # 127.0.0.1:11434

# 3. Скачать модель
ollama pull llama3.2:3b

# 4. Проверить
ollama list
curl http://localhost:11434/api/tags

# Агент (лаб. 2): LLM_API_BASE=http://host.docker.internal:11434
#                 LLM_MODEL=ollama_chat/llama3.2:3b""",
            },
            {
                "title": "Развёртывание Ollama в Docker",
                "items": [
                    "Изоляция: своя Ollama и модели в отдельном volume",
                    "1. Поднять контейнер: docker compose ... up -d ollama",
                    "2. Скачать модель ВНУТРЬ контейнера (volume пустой)",
                    "3. Проверить: docker exec -it pis-ollama ollama list",
                    "Агенты в сети pis-net: http://pis-ollama:11434",
                    "⚠️ Порт 11434 конфликтует с хостовой Ollama — остановите её",
                ],
                "code": """# 1. Поднять Ollama в контейнере
docker compose -f docker-compose.local.yaml up -d ollama

# 2. Скачать модель внутрь контейнера
docker exec -it pis-ollama ollama pull llama3.2:3b

# 3. Проверить
docker exec -it pis-ollama ollama list
curl http://localhost:11434/api/tags

# Агент (лаб. 2): LLM_API_BASE=http://pis-ollama:11434
#                 LLM_MODEL=ollama_chat/llama3.2:3b""",
            },
            {
                "title": "Сквозная проверка: агент + MCP",
                "code": """# 1. MCP-сервер (лаб. 1)
docker compose --profile lab1 up -d --build

# 2. ADK-агент (лаб. 2)
docker compose --profile lab2 up -d --build

# 3. Отправить запрос
curl -X POST http://localhost:8002/ \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"message/send",
    "params":{"message":{"role":"user","kind":"message",
    "messageId":"msg-1","parts":[{"kind":"text",
    "text":"Сравни аннуитетный и дифференцированный кредиты
    на 500 000 ₽ под 12% на 3 года"}]}}}'

# Ожидаемо: state=completed, агент вызывает
# compare_loan_schedules и возвращает сравнение""",
            },
            {
                "title": "GUI-интерфейс (единый для всех лаб)",
                "items": [
                    "Запустить MCP-сервер (лаб. 1) и ADK-агент (лаб. 2)",
                    "Запустить GUI: python gui/server.py → http://localhost:8090",
                    "Вкладка Lab 2 — ADK Agent: чат с агентом",
                    "Ввести сообщение → агент вызывает MCP-инструменты → потоковый ответ",
                    "Agent Card загружается автоматически при открытии вкладки",
                ],
            },
            {
                "title": "Ключевые решения",
                "items": [
                    "Декларативное определение: AgentCard из переменных окружения",
                    "MCP_URL разбивается по запятой → McpToolset для каждого",
                    "AgentCapabilities(streaming=True) — обязательно для streaming",
                    "CORS middleware — для доступа из браузера (лаб. 10)",
                    "Один образ переиспользуется для разных агентов",
                ],
            },
            {
                "title": "Критерии приёмки",
                "items": [
                    "✅ Агент запускается локально через start_a2a.py",
                    "✅ Ответ приходит по A2A, поддерживается streaming",
                    "✅ Dockerfile: все зависимости на этапе сборки",
                    "✅ Образ опубликован в Artifact Registry",
                    "✅ Агент создан в UI AI Agents и работает в чате",
                    "✅ Системный промпт переработан под фин. консультанта",
                ],
            },
        ],
    },
    3: {
        "title": "Агент на LangChain",
        "subtitle": "Лабораторная работа 3",
        "tech": "Python 3.12 · LangChain ≥ 0.3 · A2A SDK · LiteLLM",
        "sections": [
            {
                "title": "Цель работы",
                "items": [
                    "Создать агента на базе LangChain — одного из самых популярных фреймворков",
                    "Интеграция MCP-инструментов как LangChain Tools",
                    "Развёртывание через A2A-протокол в AI Agents",
                    "Streaming-ответы и OpenInference-телеметрия",
                ],
            },
            {
                "title": "AgentExecutor и цикл ReAct",
                "items": [
                    "ReAct = Reason + Act: модель рассуждает → выбирает инструмент → наблюдает результат",
                    "create_openai_tools_agent связывает модель, инструменты и промпт",
                    "AgentExecutor выполняет цикл с max_iterations (защита от зацикливания)",
                    "handle_parsing_errors=True — не падает при неверном формате ответа",
                ],
            },
            {
                "title": "MCP → LangChain Tool",
                "code": """def create_mcp_tool(mcp_url, tool_name, tool_desc):
    def mcp_tool_func(input_text):
        async def async_call():
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{mcp_url}/tools/{tool_name}/invoke",
                    json={"input": input_text})
                return str(resp.json().get("content", resp.json()))
        return asyncio.run(async_call())

    return Tool(name=tool_name,
                description=tool_desc,
                func=mcp_tool_func)""",
            },
            {
                "title": "Запуск и проверка",
                "items": [
                    "Локально: MCP_URL=http://localhost:8000/sse PORT=10003 LLM_API_KEY=dummy uv run python src/start_a2a.py",
                    "Docker: docker compose --profile lab3 up -d --build",
                    "Порт хоста: 8003 (внутренний: 10000)",
                    "Agent Card: curl http://localhost:8003/.well-known/agent-card.json",
                    "Телеметрия: ENABLE_PHOENIX=true → Phoenix UI для трейсов",
                ],
            },
            {
                "title": "Запуск в Docker",
                "items": [
                    "Сборка образа: docker build -t lab3-langchain-agent .",
                    "Запуск: docker run -p 8003:10000 с переменными окружения",
                    "LLM_API_BASE указывается С суффиксом /v1 (ChatOpenAI)",
                    "Через Compose (из корня репозитория):",
                    "docker compose -f docker-compose.local.yaml --profile lab3 up -d --build",
                    "Порт хоста 8003 → внутренний 10000",
                ],
                "code": """# Сборка
docker build -t lab3-langchain-agent .

# Запуск контейнера
docker run --rm -p 8003:10000 \\
  -e MCP_URL=http://host.docker.internal:8000/mcp \\
  -e LLM_API_BASE=http://host.docker.internal:11434/v1 \\
  -e LLM_MODEL=llama3.2:3b \\
  -e LLM_API_KEY=dummy \\
  --add-host=host.docker.internal:host-gateway \\
  lab3-langchain-agent

# Или через Compose
docker compose -f docker-compose.local.yaml \\
  --profile lab3 up -d --build""",
            },
            {
                "title": "Развёртывание Ollama на хосте",
                "items": [
                    "1. Установить Ollama: https://ollama.com/download",
                    "2. Запустить сервис: ollama serve (слушает 127.0.0.1:11434)",
                    "3. Скачать модель: ollama pull llama3.2:3b",
                    "4. Проверить: ollama list / curl http://localhost:11434/api/tags",
                    "Агент в контейнере: LLM_API_BASE=http://host.docker.internal:11434/v1",
                    "Формат модели (ChatOpenAI): llama3.2:3b — БЕЗ префикса",
                ],
                "code": """# 1. Установить Ollama (Windows/macOS/Linux)
#    https://ollama.com/download

# 2. Запустить сервис (в отдельном терминале)
ollama serve            # 127.0.0.1:11434

# 3. Скачать модель
ollama pull llama3.2:3b

# 4. Проверить
ollama list
curl http://localhost:11434/api/tags

# Агент (лаб. 3): LLM_API_BASE=http://host.docker.internal:11434/v1
#                 LLM_MODEL=llama3.2:3b""",
            },
            {
                "title": "Развёртывание Ollama в Docker",
                "items": [
                    "Изоляция: своя Ollama и модели в отдельном volume",
                    "1. Поднять контейнер: docker compose ... up -d ollama",
                    "2. Скачать модель ВНУТРЬ контейнера (volume пустой)",
                    "3. Проверить: docker exec -it pis-ollama ollama list",
                    "Агенты в сети pis-net: http://pis-ollama:11434/v1",
                    "⚠️ Порт 11434 конфликтует с хостовой Ollama — остановите её",
                ],
                "code": """# 1. Поднять Ollama в контейнере
docker compose -f docker-compose.local.yaml up -d ollama

# 2. Скачать модель внутрь контейнера
docker exec -it pis-ollama ollama pull llama3.2:3b

# 3. Проверить
docker exec -it pis-ollama ollama list
curl http://localhost:11434/api/tags

# Агент (лаб. 3): LLM_API_BASE=http://pis-ollama:11434/v1
#                 LLM_MODEL=llama3.2:3b""",
            },
            {
                "title": "GUI-интерфейс (единый для всех лаб)",
                "items": [
                    "Запустить MCP-сервер (лаб. 1) и LangChain-агент (лаб. 3)",
                    "Запустить GUI: python gui/server.py → http://localhost:8090",
                    "Вкладка Lab 3 — LangChain: чат с агентом",
                    "Ввести сообщение → агент вызывает MCP-инструменты → потоковый ответ",
                    "Agent Card загружается автоматически при открытии вкладки",
                ],
            },
            {
                "title": "Отличия от Google ADK (лаб. 2)",
                "items": [
                    "Фреймворк: LangChain вместо Google ADK",
                    "Инструменты: явное преобразование MCP → Tool",
                    "Streaming: astream вместо run_async",
                    "История: хранение в памяти вместо SessionService",
                    "Формат модели: llama3.2:3b БЕЗ префикса (ChatOpenAI)",
                ],
            },
            {
                "title": "Критерии приёмки",
                "items": [
                    "✅ AgentExecutor построен, инструменты из MCP_URL",
                    "✅ Агент вызывает MCP-инструменты и отвечает корректно",
                    "✅ Streaming через A2A работает",
                    "✅ Трейсы видны в Phoenix",
                    "✅ Второй инструмент добавлен, маршрутизация продемонстрирована",
                    "✅ Образ развёрнут в AI Agents",
                ],
            },
        ],
    },
    4: {
        "title": "Агент на SmolAgents (Code Agent)",
        "subtitle": "Лабораторная работа 4",
        "tech": "Python 3.12 · SmolAgents · A2A SDK · LiteLLM",
        "sections": [
            {
                "title": "Цель работы",
                "items": [
                    "Создать лёгковесного Code Agent на SmolAgents (Hugging Face)",
                    "Подключить к A2A-протоколу",
                    "Сравнить с LangChain (лаб. 3): число шагов, вызовов LLM",
                    "Оценить эффективность и простоту API",
                ],
            },
            {
                "title": "Code Agent vs Tool Calling Agent",
                "items": [
                    "Tool Calling: выбирает инструмент → передаёт аргументы → много шагов",
                    "Code Agent: пишет Python-код → исполняет → мало шагов",
                    "Code Agent сокращает вызовы LLM на ~30 %",
                    "Гибкость: практически любая вычислительная задача",
                    "Расход токенов: ниже за счёт объединения шагов",
                ],
            },
            {
                "title": "Code Agent: определение",
                "code": """from smolagents import CodeAgent, Tool

def create_smolagents_agent(mcp_urls=None):
    def llm_call(messages, **kwargs):
        response = completion(
            model=os.getenv("LLM_MODEL"),
            messages=messages,
            api_base=os.getenv("LLM_API_BASE"),
            api_key=os.getenv("LLM_API_KEY"))
        return response.choices[0].message.content

    tools = get_mcp_tools(mcp_urls)
    agent = CodeAgent(
        tools=tools,
        llm=llm_call,
        system_prompt=os.getenv("AGENT_SYSTEM_PROMPT"),
        max_iterations=15)
    return agent""",
            },
            {
                "title": "Запуск и проверка",
                "items": [
                    "Локально: LLM_API_KEY=dummy uv run python src/start_a2a.py",
                    "Docker: docker compose --profile lab4 up -d --build",
                    "Порт хоста: 8004 (внутренний: 10000)",
                    "Agent Card: curl http://localhost:8004/.well-known/agent-card.json",
                    "Задачи: «посчитай 17-е простое число», «факториал 10»",
                    "⚠️ Intel Mac: uv sync может упасть (torch) → используйте Docker",
                ],
            },
            {
                "title": "Запуск в Docker",
                "items": [
                    "Сборка образа: docker build -t lab4-smolagents-agent .",
                    "Запуск: docker run -p 8004:10000 с переменными окружения",
                    "LLM_API_BASE указывается БЕЗ суффикса /v1 (LiteLLM)",
                    "Через Compose (из корня репозитория):",
                    "docker compose -f docker-compose.local.yaml --profile lab4 up -d --build",
                    "Порт хоста 8004 → внутренний 10000",
                ],
                "code": """# Сборка
docker build -t lab4-smolagents-agent .

# Запуск контейнера
docker run --rm -p 8004:10000 \\
  -e MCP_URL=http://host.docker.internal:8000/mcp \\
  -e LLM_API_BASE=http://host.docker.internal:11434 \\
  -e LLM_MODEL=ollama_chat/llama3.2:3b \\
  -e LLM_API_KEY=dummy \\
  --add-host=host.docker.internal:host-gateway \\
  lab4-smolagents-agent

# Или через Compose
docker compose -f docker-compose.local.yaml \\
  --profile lab4 up -d --build""",
            },
            {
                "title": "Развёртывание Ollama на хосте",
                "items": [
                    "1. Установить Ollama: https://ollama.com/download",
                    "2. Запустить сервис: ollama serve (слушает 127.0.0.1:11434)",
                    "3. Скачать модель: ollama pull llama3.2:3b",
                    "4. Проверить: ollama list / curl http://localhost:11434/api/tags",
                    "Агент в контейнере: LLM_API_BASE=http://host.docker.internal:11434",
                    "Формат модели (LiteLLM): ollama_chat/llama3.2:3b",
                ],
                "code": """# 1. Установить Ollama (Windows/macOS/Linux)
#    https://ollama.com/download

# 2. Запустить сервис (в отдельном терминале)
ollama serve            # 127.0.0.1:11434

# 3. Скачать модель
ollama pull llama3.2:3b

# 4. Проверить
ollama list
curl http://localhost:11434/api/tags

# Агент (лаб. 4): LLM_API_BASE=http://host.docker.internal:11434
#                 LLM_MODEL=ollama_chat/llama3.2:3b""",
            },
            {
                "title": "Развёртывание Ollama в Docker",
                "items": [
                    "Изоляция: своя Ollama и модели в отдельном volume",
                    "1. Поднять контейнер: docker compose ... up -d ollama",
                    "2. Скачать модель ВНУТРЬ контейнера (volume пустой)",
                    "3. Проверить: docker exec -it pis-ollama ollama list",
                    "Агенты в сети pis-net: http://pis-ollama:11434",
                    "⚠️ Порт 11434 конфликтует с хостовой Ollama — остановите её",
                ],
                "code": """# 1. Поднять Ollama в контейнере
docker compose -f docker-compose.local.yaml up -d ollama

# 2. Скачать модель внутрь контейнера
docker exec -it pis-ollama ollama pull llama3.2:3b

# 3. Проверить
docker exec -it pis-ollama ollama list
curl http://localhost:11434/api/tags

# Агент (лаб. 4): LLM_API_BASE=http://pis-ollama:11434
#                 LLM_MODEL=ollama_chat/llama3.2:3b""",
            },
            {
                "title": "GUI-интерфейс (единый для всех лаб)",
                "items": [
                    "Запустить MCP-сервер (лаб. 1) и Smolagents-агент (лаб. 4)",
                    "Запустить GUI: python gui/server.py → http://localhost:8090",
                    "Вкладка Lab 4 — SmolAgents: чат с агентом",
                    "Ввести сообщение → агент пишет и выполняет Python-код → возвращает результат",
                    "Agent Card загружается автоматически при открытии вкладки",
                ],
            },
            {
                "title": "Сравнение: LangChain vs SmolAgents",
                "items": [
                    "LangChain: AgentExecutor, ReAct-цикл, verbose=True",
                    "SmolAgents: CodeAgent, генерация и исполнение кода",
                    "SmolAgents: меньше шагов, меньше вызовов LLM (~30 %)",
                    "SmolAgents: проще API, меньше зависимостей",
                    "LangChain: более зрелый фреймворк, больше интеграций",
                ],
            },
            {
                "title": "Критерии приёмки",
                "items": [
                    "✅ CodeAgent создан, модель через LiteLLM",
                    "✅ Агент решает задачи на генерацию и исполнение кода",
                    "✅ Число шагов/вызовов LLM сравнено с лаб. 3",
                    "✅ Собственный @tool добавлен и вызывается",
                    "✅ Образ развёрнут в AI Agents",
                ],
            },
        ],
    },
}


# ── Генерация презентаций ─────────────────────────────────────────

def generate_presentation(lab_num, data):
    """Генерирует презентацию для одной лабораторной."""
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    total = len(data["sections"]) + 2  # титульный + секции
    accent = LAB_COLORS[lab_num]

    # ── Слайд 1: Титульный ──
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    set_slide_bg(slide, BG_DARK)

    # Декоративная полоска сверху
    add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.12), accent)

    # Номер лабы
    add_text_box(slide, Inches(0.8), Inches(1.8), Inches(8.5), Inches(0.5),
                 f"ЛАБОРАТОРНАЯ РАБОТА {lab_num}", font_size=16,
                 color=accent, bold=True)

    # Заголовок
    add_text_box(slide, Inches(0.8), Inches(2.4), Inches(8.5), Inches(1.2),
                 data["title"], font_size=36, color=WHITE, bold=True)

    # Подзаголовок
    add_text_box(slide, Inches(0.8), Inches(3.8), Inches(8.5), Inches(0.5),
                 data["subtitle"], font_size=18, color=LIGHT_GRAY)

    # Технологии
    add_text_box(slide, Inches(0.8), Inches(4.5), Inches(8.5), Inches(0.5),
                 data["tech"], font_size=14, color=accent)

    # Нижний акцент
    add_accent_bar(slide, Inches(0), Inches(7.3), Inches(10), Inches(0.08), accent)

    # ── Слайды секций ──
    for idx, section in enumerate(data["sections"]):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        set_slide_bg(slide, BG_MID)

        section_num = idx + 1
        add_section_header(slide, section_num, section["title"], accent)

        y = Inches(1.5)
        height_left = Inches(5.5)

        if "items" in section:
            # Левая колонка — текст
            add_bullet_list(slide, Inches(0.6), y, Inches(5.5), height_left,
                            section["items"], font_size=14, color=LIGHT_GRAY)

        if "code" in section:
            # Правая колонка — код
            code_lines = section["code"].strip().split("\n")
            code_height = max(Inches(1.5), Inches(0.35 * len(code_lines)))
            add_code_block(slide, Inches(6.2), y, Inches(3.5), code_height,
                           section["code"], font_size=9)

        add_slide_number(slide, section_num + 1, total)

    # ── Последний слайд: Спасибо ──
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, BG_DARK)
    add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.12), accent)

    add_text_box(slide, Inches(0.8), Inches(2.5), Inches(8.5), Inches(1.0),
                 "СПАСИБО ЗА ВНИМАНИЕ!", font_size=32,
                 color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(0.8), Inches(3.8), Inches(8.5), Inches(0.5),
                 f"Лабораторная работа {lab_num}: {data['title']}",
                 font_size=16, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(0.8), Inches(4.5), Inches(8.5), Inches(0.5),
                 "Вопросы?", font_size=20, color=accent, bold=True,
                 alignment=PP_ALIGN.CENTER)

    add_accent_bar(slide, Inches(0), Inches(7.3), Inches(10), Inches(0.08), accent)

    # Сохранение
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{lab_num:02d}-lab-slides.pptx")
    prs.save(filename)
    print(f"✅ Сохранено: {filename}")


def main():
    for lab_num, data in LABS_DATA.items():
        generate_presentation(lab_num, data)
    print("\n🎉 Все презентации сгенерированы!")


if __name__ == "__main__":
    main()
