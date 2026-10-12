"""GUI-сервер для лабораторных работ 1–4.

Подключается к MCP-серверу (лаб. 1) и A2A-агентам (лабы 2–4),
предоставляет REST API и раздает статический фронтенд.
"""
import os
import sys
import json
import asyncio
import httpx
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# UTF-8 reconfigure для Windows
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

app = FastAPI(title="AI Agents Lab GUI", version="1.0.0")

# ── Конфигурация сервисов ────────────────────────────────────────
SERVICES = {
    "lab1_mcp": {
        "name": "MCP-сервер (лаб. 1)",
        "base_url": os.getenv("MCP_URL", "http://localhost:8000"),
        "type": "mcp",
    },
    "lab2_adk": {
        "name": "ADK-агент (лаб. 2)",
        "base_url": os.getenv("LAB2_URL", "http://localhost:8002"),
        "type": "a2a",
    },
    "lab3_langchain": {
        "name": "LangChain-агент (лаб. 3)",
        "base_url": os.getenv("LAB3_URL", "http://localhost:8003"),
        "type": "a2a",
    },
    "lab4_smolagents": {
        "name": "SmolAgents (лаб. 4)",
        "base_url": os.getenv("LAB4_URL", "http://localhost:8004"),
        "type": "a2a",
    },
}

# ── Модели ───────────────────────────────────────────────────────
class HealthCheck(BaseModel):
    status: str
    service: str
    url: str
    details: Optional[Dict[str, Any]] = None

class MCPToolCall(BaseModel):
    tool_name: str
    principal: float = 1000000
    annual_rate_percent: float = 15
    months: int = 60
    monthly_contribution: float = 100
    contribution_at_beginning: bool = False

class A2AMessage(BaseModel):
    service: str
    message: str = Field(..., min_length=1, max_length=2000)

class A2AResponse(BaseModel):
    service: str
    text: str
    state: str
    steps: Optional[int] = None

# ── Статика ──────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

# Создаём index.html
INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agents Lab GUI</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI Agents — Лабораторные 1–4</h1>
            <p class="subtitle">GUI для тестирования MCP-сервера и A2A-агентов</p>
        </header>

        <!-- Статус сервисов -->
        <section id="services" class="card">
            <h2>📡 Статус сервисов</h2>
            <div id="service-list" class="service-grid"></div>
        </section>

        <!-- MCP-инструменты -->
        <section id="mcp-section" class="card">
            <h2>💰 MCP-сервер (Лаба 1)</h2>
            <div class="tabs">
                <button class="tab active" data-tab="annuity">Аннуитетный кредит</button>
                <button class="tab" data-tab="differential">Дифференцированный</button>
                <button class="tab" data-tab="deposit">Вклад</button>
                <button class="tab" data-tab="compare">Сравнение</button>
                <button class="tab" data-tab="investment">Инвестиции</button>
            </div>

            <!-- Аннуитетный кредит -->
            <div class="tab-content active" id="tab-annuity">
                <form id="form-annuity">
                    <div class="form-row">
                        <label>Сумма кредита (₽): <input type="number" id="annuity-principal" value="1000000" min="1"></label>
                        <label>Ставка (%): <input type="number" id="annuity-rate" value="15" step="0.1" min="0.1"></label>
                        <label>Срок (мес): <input type="number" id="annuity-months" value="60" min="1"></label>
                    </div>
                    <button type="submit" class="btn btn-primary">Рассчитать</button>
                </form>
                <pre id="result-annuity" class="result"></pre>
            </div>

            <!-- Дифференцированный кредит -->
            <div class="tab-content" id="tab-differential">
                <form id="form-differential">
                    <div class="form-row">
                        <label>Сумма кредита (₽): <input type="number" id="diff-principal" value="1000000" min="1"></label>
                        <label>Ставка (%): <input type="number" id="diff-rate" value="15" step="0.1" min="0.1"></label>
                        <label>Срок (мес): <input type="number" id="diff-months" value="60" min="1"></label>
                    </div>
                    <button type="submit" class="btn btn-primary">Рассчитать</button>
                </form>
                <pre id="result-differential" class="result"></pre>
            </div>

            <!-- Вклад -->
            <div class="tab-content" id="tab-deposit">
                <form id="form-deposit">
                    <div class="form-row">
                        <label>Начальная сумма (₽): <input type="number" id="dep-initial" value="500000" min="0"></label>
                        <label>Ставка (%): <input type="number" id="dep-rate" value="12" step="0.1" min="0"></label>
                        <label>Срок (мес): <input type="number" id="dep-months" value="24" min="1"></label>
                        <label>Взнос/мес (₽): <input type="number" id="dep-contrib" value="10000" min="0"></label>
                    </div>
                    <label><input type="checkbox" id="dep-beginning" checked> Взнос в начале месяца</label>
                    <button type="submit" class="btn btn-primary">Рассчитать</button>
                </form>
                <pre id="result-deposit" class="result"></pre>
            </div>

            <!-- Сравнение -->
            <div class="tab-content" id="tab-compare">
                <form id="form-compare">
                    <div class="form-row">
                        <label>Сумма кредита (₽): <input type="number" id="cmp-principal" value="500000" min="1"></label>
                        <label>Ставка (%): <input type="number" id="cmp-rate" value="12" step="0.1" min="0.1"></label>
                        <label>Срок (мес): <input type="number" id="cmp-months" value="36" min="1"></label>
                    </div>
                    <button type="submit" class="btn btn-primary">Сравнить</button>
                </form>
                <pre id="result-compare" class="result"></pre>
            </div>

            <!-- Инвестиции -->
            <div class="tab-content" id="tab-investment">
                <form id="form-investment">
                    <div class="form-row">
                        <label>Начальная сумма (₽): <input type="number" id="inv-initial" value="100000" min="0"></label>
                        <label>Доходность (%): <input type="number" id="inv-rate" value="10" step="0.1" min="0"></label>
                        <label>Срок (мес): <input type="number" id="inv-months" value="36" min="1"></label>
                        <label>Взнос/мес (₽): <input type="number" id="inv-contrib" value="5000" min="0"></label>
                    </div>
                    <label><input type="checkbox" id="inv-beginning" checked> Взнос в начале месяца</label>
                    <button type="submit" class="btn btn-primary">Рассчитать</button>
                </form>
                <pre id="result-investment" class="result"></pre>
            </div>
        </section>

        <!-- A2A-агенты -->
        <section id="agents-section" class="card">
            <h2>🤖 A2A-агенты (Лабы 2–4)</h2>
            <div class="agent-selector">
                <label>Агент:
                    <select id="agent-select">
                        <option value="lab2_adk">ADK-агент (лаб. 2)</option>
                        <option value="lab3_langchain">LangChain-агент (лаб. 3)</option>
                        <option value="lab4_smolagents">SmolAgents (лаб. 4)</option>
                    </select>
                </label>
            </div>
            <form id="form-a2a">
                <textarea id="a2a-message" placeholder="Введите запрос агенту...&#10;&#10;Пример: Рассчитай аннуитетный кредит на 1 000 000 ₽ под 15% на 5 лет" rows="4"></textarea>
                <button type="submit" class="btn btn-success">Отправить агенту</button>
            </form>
            <div id="a2a-result" class="result"></div>
        </section>

        <footer>
            <p>AI Agents Lab GUI v1.0 | MCP + A2A + Docker</p>
        </footer>
    </div>

    <script src="/app.js"></script>
</body>
</html>"""

STYLE_CSS = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

header {
    text-align: center;
    padding: 30px 0;
}

header h1 {
    font-size: 2.5em;
    background: linear-gradient(90deg, #00d2ff, #3a7bd5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    color: #888;
    margin-top: 10px;
    font-size: 1.1em;
}

.card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
}

.card h2 {
    margin-bottom: 16px;
    color: #fff;
    font-size: 1.4em;
}

/* Service grid */
.service-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
}

.service-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.3s;
}

.service-item:hover {
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-2px);
}

.service-status {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}

.service-status.online {
    background: #00e676;
    box-shadow: 0 0 8px #00e676;
}

.service-status.offline {
    background: #ff5252;
    box-shadow: 0 0 8px #ff5252;
}

.service-name {
    font-weight: 600;
    color: #fff;
}

.service-url {
    font-size: 0.85em;
    color: #888;
}

/* Tabs */
.tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.tab {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ccc;
    padding: 10px 18px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.95em;
    transition: all 0.2s;
}

.tab:hover {
    background: rgba(255, 255, 255, 0.1);
}

.tab.active {
    background: linear-gradient(135deg, #00d2ff, #3a7bd5);
    color: #fff;
    border-color: transparent;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* Forms */
form {
    margin-bottom: 16px;
}

.form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
}

label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.9em;
    color: #aaa;
}

label input[type="number"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 10px 14px;
    color: #fff;
    font-size: 1em;
    outline: none;
    transition: border-color 0.2s;
}

label input[type="number"]:focus {
    border-color: #00d2ff;
}

label input[type="checkbox"] {
    width: auto;
    margin-right: 8px;
}

/* Buttons */
.btn {
    padding: 12px 28px;
    border: none;
    border-radius: 10px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    color: #fff;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: linear-gradient(135deg, #00d2ff, #3a7bd5);
}

.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
}

.btn-success {
    background: linear-gradient(135deg, #00e676, #00c853);
}

.btn-success:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 230, 118, 0.3);
}

/* Results */
.result {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 0.9em;
    color: #a5d6a7;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 500px;
    overflow-y: auto;
    min-height: 60px;
}

.result:empty::before {
    content: "Здесь появится результат...";
    color: #555;
}

/* Agent selector */
.agent-selector {
    margin-bottom: 16px;
}

.agent-selector select {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 10px 14px;
    color: #fff;
    font-size: 1em;
    outline: none;
    cursor: pointer;
}

#form-a2a textarea {
    width: 100%;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 14px;
    color: #fff;
    font-size: 1em;
    font-family: inherit;
    resize: vertical;
    outline: none;
    margin-bottom: 12px;
}

#form-a2a textarea:focus {
    border-color: #00e676;
}

/* Footer */
footer {
    text-align: center;
    padding: 20px;
    color: #555;
    font-size: 0.9em;
}

/* Loading spinner */
.loading::after {
    content: " ⏳";
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Responsive */
@media (max-width: 768px) {
    header h1 { font-size: 1.8em; }
    .form-row { grid-template-columns: 1fr; }
    .tabs { flex-direction: column; }
}"""

APP_JS = """// ── Утилиты ──────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

async function api(path, method = "GET", body = null) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
    }
    return res.json();
}

// ── Статус сервисов ──────────────────────────────────────────────
async function loadServices() {
    const list = $("#service-list");
    try {
        const services = await api("/api/health");
        list.innerHTML = services.map(s => `
            <div class="service-item">
                <div class="service-status ${s.status === 'ok' ? 'online' : 'offline'}"></div>
                <div>
                    <div class="service-name">${s.name}</div>
                    <div class="service-url">${s.url}</div>
                </div>
            </div>
        `).join("");
    } catch (e) {
        list.innerHTML = `<p style="color:#ff5252">Ошибка загрузки: ${e.message}</p>`;
    }
}

// ── Табы ─────────────────────────────────────────────────────────
$$(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
        $$(".tab").forEach(t => t.classList.remove("active"));
        $$(".tab-content").forEach(c => c.classList.remove("active"));
        tab.classList.add("active");
        $(`#tab-${tab.dataset.tab}`).classList.add("active");
    });
});

// ── MCP: Аннуитетный кредит ──────────────────────────────────────
$("#form-annuity").addEventListener("submit", async (e) => {
    e.preventDefault();
    const res = $("#result-annuity");
    res.textContent = "Вычисляю...";
    res.classList.add("loading");
    try {
        const data = await api("/api/mcp/loan_schedule_annuity", "POST", {
            principal: +$("#annuity-principal").value,
            annual_rate_percent: +$("#annuity-rate").value,
            months: +$("#annuity-months").value,
        });
        res.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        res.textContent = `Ошибка: ${e.message}`;
    } finally {
        res.classList.remove("loading");
    }
});

// ── MCP: Дифференцированный кредит ───────────────────────────────
$("#form-differential").addEventListener("submit", async (e) => {
    e.preventDefault();
    const res = $("#result-differential");
    res.textContent = "Вычисляю...";
    res.classList.add("loading");
    try {
        const data = await api("/api/mcp/loan_schedule_differential", "POST", {
            principal: +$("#diff-principal").value,
            annual_rate_percent: +$("#diff-rate").value,
            months: +$("#diff-months").value,
        });
        res.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        res.textContent = `Ошибка: ${e.message}`;
    } finally {
        res.classList.remove("loading");
    }
});

// ── MCP: Вклад ───────────────────────────────────────────────────
$("#form-deposit").addEventListener("submit", async (e) => {
    e.preventDefault();
    const res = $("#result-deposit");
    res.textContent = "Вычисляю...";
    res.classList.add("loading");
    try {
        const data = await api("/api/mcp/deposit_schedule_compound", "POST", {
            initial_amount: +$("#dep-initial").value,
            annual_rate_percent: +$("#dep-rate").value,
            months: +$("#dep-months").value,
            monthly_contribution: +$("#dep-contrib").value,
            contribution_at_beginning: $("#dep-beginning").checked,
        });
        res.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        res.textContent = `Ошибка: ${e.message}`;
    } finally {
        res.classList.remove("loading");
    }
});

// ── MCP: Сравнение ───────────────────────────────────────────────
$("#form-compare").addEventListener("submit", async (e) => {
    e.preventDefault();
    const res = $("#result-compare");
    res.textContent = "Вычисляю...";
    res.classList.add("loading");
    try {
        const data = await api("/api/mcp/compare_loan_schedules", "POST", {
            principal: +$("#cmp-principal").value,
            annual_rate_percent: +$("#cmp-rate").value,
            months: +$("#cmp-months").value,
        });
        res.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        res.textContent = `Ошибка: ${e.message}`;
    } finally {
        res.classList.remove("loading");
    }
});

// ── MCP: Инвестиции ──────────────────────────────────────────────
$("#form-investment").addEventListener("submit", async (e) => {
    e.preventDefault();
    const res = $("#result-investment");
    res.textContent = "Вычисляю...";
    res.classList.add("loading");
    try {
        const data = await api("/api/mcp/investment_calculator", "POST", {
            initial_amount: +$("#inv-initial").value,
            annual_rate_percent: +$("#inv-rate").value,
            months: +$("#inv-months").value,
            monthly_contribution: +$("#inv-contrib").value,
            contribution_at_beginning: $("#inv-beginning").checked,
        });
        res.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        res.textContent = `Ошибка: ${e.message}`;
    } finally {
        res.classList.remove("loading");
    }
});

// ── A2A: Агенты ──────────────────────────────────────────────────
$("#form-a2a").addEventListener("submit", async (e) => {
    e.preventDefault();
    const service = $("#agent-select").value;
    const message = $("#a2a-message").value.trim();
    if (!message) return;

    const res = $("#a2a-result");
    res.textContent = "Агент думает...";
    res.classList.add("loading");
    try {
        const data = await api("/api/a2a/message", "POST", { service, message });
        res.textContent = data.text || JSON.stringify(data, null, 2);
    } catch (e) {
        res.textContent = `Ошибка: ${e.message}`;
    } finally {
        res.classList.remove("loading");
    }
});

// ── Инициализация ────────────────────────────────────────────────
loadServices();
setInterval(loadServices, 30000); // Обновлять статус каждые 30 сек"""

# Записываем файлы
Path(STATIC_DIR / "index.html").write_text(INDEX_HTML, encoding="utf-8")
Path(STATIC_DIR / "style.css").write_text(STYLE_CSS, encoding="utf-8")
Path(STATIC_DIR / "app.js").write_text(APP_JS, encoding="utf-8")

# ── API: Health ──────────────────────────────────────────────────
def _client(timeout: float = 5.0) -> httpx.AsyncClient:
    """httpx-клиент без системного прокси (иначе localhost-запросы идут через прокси и виснут)."""
    return httpx.AsyncClient(timeout=timeout, trust_env=False)


@app.get("/api/health")
async def health_check():
    async def check_one(client, svc):
        try:
            if svc["type"] == "mcp":
                r = await client.get(f"{svc['base_url']}/health")
                status = "ok" if r.status_code == 200 else "error"
            else:
                r = await client.get(f"{svc['base_url']}/.well-known/agent-card.json")
                status = "ok" if r.status_code == 200 else "error"
            return {"status": status, "name": svc["name"], "url": svc["base_url"]}
        except Exception:
            return {"status": "error", "name": svc["name"], "url": svc["base_url"]}

    async with _client() as client:
        tasks = [check_one(client, svc) for svc in SERVICES.values()]
        results = await asyncio.gather(*tasks)
    return list(results)

# ── API: MCP-инструменты ─────────────────────────────────────────
MCP_TOOLS = {
    "loan_schedule_annuity": "loan_schedule_annuity",
    "loan_schedule_differential": "loan_schedule_differential",
    "deposit_schedule_compound": "deposit_schedule_compound",
    "compare_loan_schedules": "compare_loan_schedules",
    "investment_calculator": "investment_calculator",
}

@app.post("/api/mcp/{tool_name}")
async def call_mcp_tool(tool_name: str, data: Dict[str, Any]):
    if tool_name not in MCP_TOOLS:
        raise HTTPException(404, f"Неизвестный инструмент: {tool_name}")

    mcp_url = SERVICES["lab1_mcp"]["base_url"].rstrip("/") + "/mcp"
    tool_name_real = MCP_TOOLS[tool_name]

    async with _client(timeout=60.0) as client:
        # 1. initialize
        init = await client.post(
            mcp_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "gui", "version": "1"},
                },
            },
            headers={"Accept": "application/json, text/event-stream"},
        )
        init.raise_for_status()
        session_id = init.headers.get("mcp-session-id")

        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if session_id:
            headers["mcp-session-id"] = session_id

        # 2. notifications/initialized
        await client.post(
            mcp_url,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers=headers,
        )

        # 3. tools/call
        resp = await client.post(
            mcp_url,
            json={
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": tool_name_real, "arguments": data},
            },
            headers=headers,
        )
        resp.raise_for_status()

        # Парсим SSE-ответ
        result = None
        for line in resp.text.splitlines():
            if line.startswith("data: "):
                try:
                    msg = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                if msg.get("id") == 10:
                    result = msg
                    break
        if result is None:
            result = json.loads(resp.text)

        r = result.get("result", {})
        sc = r.get("structuredContent", {})
        if isinstance(sc, dict) and "structured_content" in sc:
            return sc["structured_content"]
        content = r.get("content", [])
        if content:
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return {"text": text}
        return sc

# ── API: A2A-агенты ─────────────────────────────────────────────
A2A_SERVICES = {
    "lab2_adk": SERVICES["lab2_adk"]["base_url"],
    "lab3_langchain": SERVICES["lab3_langchain"]["base_url"],
    "lab4_smolagents": SERVICES["lab4_smolagents"]["base_url"],
}

@app.post("/api/a2a/message")
async def send_a2a_message(req: A2AMessage):
    if req.service not in A2A_SERVICES:
        raise HTTPException(404, f"Неизвестный агент: {req.service}")
    
    base_url = A2A_SERVICES[req.service]
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "kind": "message",
                "messageId": "gui-msg-1",
                "parts": [{"kind": "text", "text": req.message}],
            }
        },
    }
    
    async with _client(timeout=120.0) as client:
        r = await client.post(base_url, json=payload)
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        data = r.json()

    # Извлекаем текст ответа агента из A2A-структуры
    text = ""
    state = "unknown"
    try:
        result = data.get("result", {})
        status = result.get("status", {})
        state = status.get("state", "unknown")
        msg = status.get("message", {})
        parts = msg.get("parts", [])
        if parts:
            text = parts[0].get("text", "")
        # Fallback: последнее сообщение агента в history
        if not text:
            for item in reversed(result.get("history", [])):
                if item.get("role") == "agent":
                    p = item.get("parts", [])
                    if p:
                        text = p[0].get("text", "")
                        break
    except Exception:
        pass

    if data.get("error"):
        text = f"Ошибка агента: {data['error'].get('message', data['error'])}"
        state = "error"

    return {"service": req.service, "text": text, "state": state, "raw": data}

# ── Статика ──────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/style.css")
async def style_css():
    return FileResponse(str(STATIC_DIR / "style.css"))

@app.get("/app.js")
async def app_js():
    return FileResponse(str(STATIC_DIR / "app.js"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GUI_PORT", "8090"))
    print(f"🌐 GUI запущен на http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)