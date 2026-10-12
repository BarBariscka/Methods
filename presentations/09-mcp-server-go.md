# Лабораторная работа 9. MCP-сервер финансовых расчётов на Go

> | | |
> |---|---|
> | **Каталог** | `lab9-mcp-finance-go/` |
> | **Go-модуль** | `github.com/cloud-ru/mcp-finance-go` |
> | **Технологии** | Go ≥ 1.21, go modules, Prometheus, OpenTelemetry, Docker |
> | **Тесты** | `go test ./...` |
> | **Ориентировочное время** | 4–6 часов |

---

## 1. Цель работы

Реализовать аналог лабораторной работы 1 на **Go** — MCP-сервер для финансовых расчётов
в статически типизированной экосистеме, с метриками Prometheus и health check, чтобы
сравнить два подхода к разработке MCP-сервисов.

---

## 2. Теоретическая часть

### MCP без фреймворка

В Python используется FastMCP, который берёт на себя запуск сервера, маршрутизацию
и сериализацию. В Go такого фреймворка нет — протокол реализуется вручную поверх HTTP:

1. HTTP-обработчик endpoint `/mcp`.
2. Разбор тела запроса как JSON-RPC: `{"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}`.
3. Диспетчер по `method`: `initialize`, `tools/list`, `tools/call`.
4. Извлечение параметров и вызов обработчика инструмента.
5. Формирование JSON-RPC-ответа.

### Что даёт статическая типизация

| Аспект | Python (FastMCP) | Go |
|---|---|---|
| Схема инструмента | Строится из type hints + docstring в рантайме | Структуры `ScheduleEntry`, `LoanSummary`, `CalculationResult` — ошибки компиляции |
| Извлечение параметров | `Field` + автоматическая валидация | Ручное извлечение с проверкой типа: `params["principal"].(float64)` |
| Возврат ошибок | `ValueError`, `McpError` | `(interface{}, error)` |
| Скомпилированный бинарник | Нет | Да — один файл, быстрый старт |

### Плюсы и минусы Go-подхода

**Плюсы:** статическая типизация, высокая производительность, один статический бинарник
без зависимостей, встроенный `go test`, отличная стандартная библиотека и удобная
конкурентность.

**Минусы:** ручная реализация протокола (больше кода), нет готовых декораторов,
спецификации инструментов приходится описывать отдельно, кривая обучения для тех,
кто пришёл из Python.

---

## 3. Задание

1. Изучить структуру `internal/` и `pkg/`, файл `go.mod` и реализацию пяти инструментов:
   - `loan_schedule_annuity` — расчёт аннуитетного кредита;
   - `loan_schedule_differential` — расчёт дифференцированного кредита;
   - `deposit_schedule_compound` — расчёт вклада с капитализацией;
   - `compare_loan_schedules` — сравнение типов кредитов;
   - `investment_calculator` — калькулятор инвестиций.
2. **Реализовать точку входа** `cmd/server/main.go`: обработка JSON-RPC-методов,
   endpoint `/mcp`, метрики `/metrics` и health check `/health`.
3. Запустить сервер и проверить `/metrics` и `/health`.
4. Прогнать тесты: `go test ./...`.
5. Сравнить результаты расчётов с Python-версией из лаб. 1: одинаковые входные данные →
   одинаковые графики.
6. **Самостоятельное задание** (раздел 7): добавить инструмент `early_repayment`.
7. Собрать Docker-образ и развернуть в AI Agents.

> ⚠️ **Важно:** файла `cmd/server/main.go` в текущем состоянии репозитория **нет**.
> Транспорт MCP необходимо реализовать самостоятельно — это часть задания.

---

## 4. Этапы выполнения

### Этап 1. Подготовка

```bash
cd lab9-mcp-finance-go
go mod download
go build ./...
```

Убедиться, что Go версии ≥ 1.21:

```bash
go version
```

### Этап 2. Реализация точки входа

Создать `cmd/server/main.go`:

- HTTP-сервер на `PORT` (по умолчанию 8000);
- маршрут `/mcp` — обработка JSON-RPC;
- маршрут `/metrics` — вывод метрик Prometheus;
- маршрут `/health` — ответ `OK`.

Пример вызова инструмента:

```bash
curl -X POST http://localhost:8000/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "loan_schedule_annuity",
    "params": {
      "principal": 1000000,
      "annual_rate_percent": 12,
      "months": 12
    }
  }'
```

### Этап 3. Реализация инструментов

Изучить `internal/calculations/`:

```
internal/calculations/
├── annuity.go          # Аннуитетный кредит
├── annuity_test.go
├── differential.go      # Дифференцированный кредит
├── differential_test.go
├── deposit.go          # Вклад с капитализацией
├── compare.go          # Сравнение схем
├── investment.go       # Калькулятор инвестиций
└── types.go            # Структуры данных
```

Изучить `internal/tools/tools.go` — обработчики инструментов, и `internal/validators/validators.go` —
проверки параметров.

### Этап 4. Проверка endpoint-ов

```bash
go run ./cmd/server          # порт 8000

curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Этап 5. Тесты

```bash
go test ./...
go test -v ./internal/calculations/
```

### Этап 6. Самостоятельное задание

См. раздел 7.

### Этап 7. Сравнение с Python

Одинаковые входные данные в лаб. 1 и лаб. 9 должны дать одинаковые графики.
Зафиксировать результат в отчёте.

### Этап 8. Сборка и публикация

```bash
docker build -t mcp-finance-server-go .
docker tag mcp-finance-server-go \
  localhost:5000/mcp-finance-go:v1.0.0
docker push localhost:5000/mcp-finance-go:v1.0.0
```

Далее — создать MCP-сервер в UI AI Agents и подключить к агенту.

---

## 5. Ключевые инженерные решения

### Обработчик инструмента

```go
// internal/tools/tools.go
type ToolHandler func(ctx context.Context,
    params map[string]interface{}) (interface{}, error)

func LoanScheduleAnnuityHandler(cfg *config.Config,
    tracer trace.Tracer) ToolHandler {
    return func(ctx context.Context,
        params map[string]interface{}) (interface{}, error) {
        toolName := "loan_schedule_annuity"

        ctx, span := tracer.Start(ctx, toolName)
        defer span.End()

        principal, ok := params["principal"].(float64)
        if !ok {
            return nil, fmt.Errorf("invalid parameter: principal")
        }
        annualRatePercent, ok := params["annual_rate_percent"].(float64)
        if !ok {
            return nil, fmt.Errorf(
                "invalid parameter: annual_rate_percent")
        }
        monthsFloat, ok := params["months"].(float64)
        if !ok {
            return nil, fmt.Errorf("invalid parameter: months")
        }
        months := int(monthsFloat)

        span.SetAttributes(
            attribute.Float64("principal", principal),
            attribute.Float64("annual_rate_percent", annualRatePercent),
            attribute.Int("months", months),
        )
        metrics.APICalls.WithLabelValues(
            "mcp", toolName, "started").Inc()

        if err := validators.CheckPrincipal(cfg, principal); err != nil {
            metrics.ToolCalls.WithLabelValues(
                toolName, "validation_error").Inc()
            metrics.CalculationErrors.WithLabelValues(
                toolName, "validation").Inc()
            return nil, fmt.Errorf("неверные параметры: %w", err)
        }

        result, err := calculations.AnnuitySchedule(
            principal, annualRatePercent, months)
        if err != nil {
            metrics.ToolCalls.WithLabelValues(
                toolName, "error").Inc()
            return nil, err
        }

        metrics.ToolCalls.WithLabelValues(
            toolName, "success").Inc()
        return result, nil
    }
}
```

**Важно:** JSON числа всегда приходят как `float64` — даже целые. Поэтому `months`
извлекается как `float64`, а затем приводится к `int`.

### Алгоритм аннуитетного кредита

```go
// internal/calculations/annuity.go
func AnnuitySchedule(principal, annualRatePercent float64,
                     months int) (*CalculationResult, error) {
    P := principal
    n := months
    r := annualRatePercent / 100.0 / 12.0

    schedule := make([]ScheduleEntry, 0, n)
    remaining := P
    cumI := 0.0
    cumP := 0.0

    var monthlyPayment float64
    if r == 0.0 {
        monthlyPayment = P / float64(n)   // нулевая ставка
    } else {
        monthlyPayment = P * r / (1.0 - math.Pow(1.0+r, float64(-n)))
    }

    for m := 1; m <= n; m++ {
        var interest float64
        if r == 0.0 {
            interest = 0.0
        } else {
            interest = remaining * r
        }

        principalComponent := monthlyPayment - interest
        var monthly float64

        if m == n {
            // коррекция последнего платежа
            principalComponent = remaining
            monthly = principalComponent + interest
        } else {
            monthly = monthlyPayment
        }

        interest = utils.Round2(interest)
        principalComponent = utils.Round2(principalComponent)
        monthly = utils.Round2(monthly)

        remaining = utils.Round2(remaining - principalComponent)
        cumI = utils.Round2(cumI + interest)
        cumP = utils.Round2(cumP + principalComponent)

        if remaining < -0.01 {
            return nil, fmt.Errorf(
                "численная ошибка: остаток кредита стал отрицательным")
        }

        remainingPrincipal := remaining
        if remainingPrincipal < 0 {
            remainingPrincipal = 0.0
        }

        schedule = append(schedule, ScheduleEntry{
            Month:               float64(m),
            Payment:             monthly,
            Interest:            interest,
            PrincipalComponent:  principalComponent,
            RemainingPrincipal:  remainingPrincipal,
            CumulativeInterest:  cumI,
            CumulativePrincipal: cumP,
        })
    }

    summary := LoanSummary{
        Principal:         utils.Round2(P),
        AnnualRatePercent: utils.Round2(annualRatePercent),
        Months:            float64(n),
        MonthlyPayment:    utils.Round2(monthlyPayment),
        TotalPaid:         totalPaid,
        TotalInterest:     cumI,
    }

    return &CalculationResult{Summary: summary, Schedule: schedule}, nil
}
```

Обратите внимание на две особенности, обеспечивающие совпадение с Python-версией:

1. **Коррекция последнего платежа** — в последнем месяце тело равно остатку,
   чтобы `remaining_principal` стал ровно `0.00`.
2. **Округление до 2 знаков** (`utils.Round2`) на каждом шаге — иначе на длинных сроках
   накапливается расхождение с Python.

### Метрики Prometheus

- `tool_calls_total` — количество вызовов инструментов, лейблы `tool_name`, `status`;
- `calculation_errors_total` — ошибки расчётов, лейблы `tool_name`, `error_type`;
- `api_calls_total` — вызовы API, лейблы `service`, `endpoint`, `status`.

### Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `PORT` | Порт сервера | `8000` |
| `OTEL_ENDPOINT` | Endpoint для OpenTelemetry (опционально) | — |
| `OTEL_SERVICE_NAME` | Имя сервиса для трейсинга | `mcp-finance-server` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `MAX_PRINCIPAL` | Максимальная сумма кредита/вклада | `1e9` |
| `MAX_CONTRIBUTION` | Максимальный ежемесячный взнос | `1e8` |
| `MAX_MONTHS` | Максимальный срок в месяцах | `600` |
| `MAX_RATE` | Максимальная процентная ставка | `200` |
| `MAX_BALANCE_CAP` | Максимальный баланс | `1e12` |

Подробное описание всех переменных — в файле `env_options.json`.
Спецификация инструментов (описания, параметры, коды ошибок) — в `mcp_tools.json`.

---

## 6. Структура проекта

```
lab9-mcp-finance-go/
├── cmd/
│   └── server/
│       └── main.go              # Точка входа (реализуется в рамках работы)
├── internal/
│   ├── calculations/           # Бизнес-логика расчётов
│   │   ├── annuity.go
│   │   ├── differential.go
│   │   ├── deposit.go
│   │   ├── compare.go
│   │   ├── investment.go
│   │   └── types.go
│   ├── validators/              # Валидация параметров + тесты
│   ├── tools/                  # Обработчики MCP-инструментов
│   ├── config/                 # Конфигурация
│   ├── metrics/                # Prometheus-метрики
│   └── tracing/                # OpenTelemetry
├── pkg/
│   └── utils/                  # Утилиты (Round2 и др.) + тесты
├── Dockerfile
├── go.mod
├── mcp_tools.json              # Спецификация инструментов
├── env_options.json            # Описание переменных окружения
└── README.md
```

---

## 7. Самостоятельное задание

Добавить инструмент **`early_repayment`** — расчёт экономии при досрочном погашении кредита.
Должны поддерживаться два сценария:

1. **Уменьшение срока** — платёж остаётся прежним, срок сокращается;
2. **Уменьшение платежа** — срок остаётся прежним, платёж пересчитывается.

Входные параметры:

- `principal`, `annual_rate_percent`, `months` — параметры исходного кредита;
- `early_month` — месяц досрочного погашения;
- `early_amount` — сумма досрочного платежа;
- `strategy` — `"shorten_term"` или `"reduce_payment"`.

Выход: итоговая переплата, экономия в рублях и процентах, новый график платежей.

**Обязательно написать табличные тесты (table-driven tests)**:

```go
func TestEarlyRepayment(t *testing.T) {
    tests := []struct {
        name        string
        earlyMonth  int
        earlyAmount float64
        strategy    string
        wantSaving  bool   // ожидается ли экономия > 0
    }{
        {"сокращение срока", 12, 200000, "shorten_term", true},
        {"уменьшение платежа", 12, 200000, "reduce_payment", true},
        {" слишком ранний месяц", 1, 10000, "shorten_term", false},
        {"нулевая сумма", 12, 0, "reduce_payment", false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            res, err := calculations.EarlyRepaymentSchedule(
                1000000, 12, 60, tt.earlyMonth, tt.earlyAmount, tt.strategy)
            if err != nil {
                t.Fatalf("unexpected error: %v", err)
            }
            if tt.wantSaving && res.Saving <= 0 {
                t.Errorf("expected positive saving, got %.2f",
                         res.Saving)
            }
        })
    }
}
```

---

## 8. Сравнительная таблица Python vs Go

| Критерий | Python (FastMCP) | Go (без фреймворка) |
|---|---|---|
| Объём кода | Меньше: декораторы и генерация схем | Больше: ручная маршрутизация и сериализация |
| Типобезопасность | Типы проверяются в рантайме | Ошибки ловятся компилятором |
| Зависимости | Много (FastMCP, pydantic, prometheus…) | Мало (стандартная библиотека + prometheus) |
| Дистрибуция | Нужен интерпретатор и venv | Один статический бинарник |
| Производительность | Ограничена GIL | Высокая, встроенная конкурентность |
| Тесты | pytest | `go test`, табличные тесты из коробки |
| Ошибки | Исключения (`ValueError`, `McpError`) | Возвращаемые значения `(T, error)` |
| Скорость разработки | Выше для прототипов | Ниже, но надёжнее в проде |

---

## 9. Контрольные вопросы

1. Как MCP-протокол реализуется без фреймворка типа FastMCP и какие методы JSON-RPC
   необходимо реализовать?
2. Что даёт статическая типизация при описании схем инструментов и обработке параметров?
3. Какие метрики экспортирует `/metrics`, с какими лейблами и как их читать в Prometheus?
4. В чём плюсы и минусы разработки MCP-сервера на Go по сравнению с Python?
5. Зачем нужна коррекция последнего платежа и как она влияет на совпадение результатов
   с Python-версией?
6. Что такое табличные тесты и почему они удобны в Go?

---

## 10. Критерии приёмки

- [ ] Сервер отвечает на `/mcp`, `/metrics` и `/health`.
- [ ] Все 5 базовых инструментов возвращают `summary` и `schedule`.
- [ ] `go test ./...` проходит; добавлены табличные тесты (самостоятельное задание).
- [ ] Добавлен инструмент `early_repayment` (самостоятельное задание).
- [ ] Результаты совпадают с Python-версией лаб. 1.
- [ ] Сравнительная таблица Python vs Go заполнена.
- [ ] Docker-образ собран и развёрнут в AI Agents.

---

## 11. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| Точка входа отсутствует | Файл `cmd/server/main.go` не был в репозитории | Написать транспорт MCP самостоятельно |
| Неверный тип параметра | JSON-числа приходят как `float64` | Извлекать `float64`, приводить `int(monthsFloat)` |
| Ошибки компиляции | Неверные импорты или версия Go | `go version` (≥ 1.21), `go mod tidy` |
| Ошибки валидации | Не совпадают лимиты | Сверить значения с `env_options.json` |
| Расхождение с Python | Разная стратегия округления | Округлять до 2 знаков на каждом шаге, корректировать последний платёж |
| Отрицательный остаток | Численная ошибка расчёта | Проверка `remaining < -0.01` возвращает ошибку вместо некорректного результата |