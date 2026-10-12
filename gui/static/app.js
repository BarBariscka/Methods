// ── Утилиты ──────────────────────────────────────────────────────
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
setInterval(loadServices, 30000); // Обновлять статус каждые 30 сек