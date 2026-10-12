"""MCP сервер для финансовых расчётов (кредиты, вклады, инвестиции) с HTTP транспортом."""

# Standard library
import os
import sys

# Third-party
from dotenv import load_dotenv, find_dotenv

# Перенастраиваем вывод в UTF-8: в консоли Windows по умолчанию cp1251/cp866,
# и print() с эмодзи (✅, ❌, 🌐) падает с UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

# Load environment variables
load_dotenv(find_dotenv())

# Constants
PORT = int(os.getenv("PORT", "8000"))

# Импортируем единый экземпляр FastMCP
from mcp_instance import mcp

# Middleware (до init_tracing, чтобы применялись ко всем запросам)
try:
    from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
    from fastmcp.server.middleware.timing import TimingMiddleware
    from fastmcp.server.middleware.logging import LoggingMiddleware

    from middleware.friendly_error_handling import FriendlyErrorHandlingMiddleware

    def _error_callback(error: Exception, context: object) -> None:
        try:
            from metrics import API_CALLS
            API_CALLS.labels(service="mcp", endpoint="tool", status="error").inc()
        except Exception:
            pass

    mcp.add_middleware(
        FriendlyErrorHandlingMiddleware(
            include_traceback=False,
            transform_errors=True,
            error_callback=_error_callback,
        )
    )
    mcp.add_middleware(
        RateLimitingMiddleware(max_requests_per_second=50.0, burst_capacity=20)
    )
    mcp.add_middleware(TimingMiddleware())
    mcp.add_middleware(
        LoggingMiddleware(include_payloads=False, max_payload_length=500)
    )
except ImportError:
    pass  # Middleware опциональны при старых версиях fastmcp

# Импортируем метрики
try:
    from metrics import API_CALLS, CALCULATION_ERRORS, TOOL_CALLS
    print("✅ Метрики импортированы успешно")
except Exception as e:
    print(f"❌ Ошибка импорта метрик: {e}")

    class DummyCounter:
        def labels(self, **kwargs):
            return self

        def inc(self):
            pass

    API_CALLS = DummyCounter()
    CALCULATION_ERRORS = DummyCounter()
    TOOL_CALLS = DummyCounter()

# Глобальные настройки
try:
    import fastmcp
    fastmcp.settings.port = PORT
    fastmcp.settings.host = "0.0.0.0"
except Exception:
    pass

# Инициализация трейсинга
from utils.tracing import init_tracing
init_tracing()

# Регистрация инструментов (декоратор @mcp.tool в каждом модуле)
from tools.loan_schedule_annuity import loan_schedule_annuity
from tools.loan_schedule_differential import loan_schedule_differential
from tools.deposit_schedule_compound import deposit_schedule_compound
from tools.compare_loan_schedules import compare_loan_schedules
from tools.investment_calculator import investment_calculator_tool

# Custom routes для метрик и health
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(_request):
    """Endpoint для Prometheus метрик."""
    from starlette.responses import Response
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)


@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(_request):
    """Endpoint для health check."""
    from starlette.responses import Response
    return Response("OK", media_type="text/plain")


def main():
    """Запуск MCP сервера с HTTP транспортом."""
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    endpoint = "/sse" if transport == "sse" else "/mcp"

    print("=" * 60)
    print("🌐 ЗАПУСК MCP СЕРВЕРА — MCP FINANCE")
    print("=" * 60)
    print(f"🚀 MCP Server: http://0.0.0.0:{PORT}{endpoint} (транспорт: {transport})")
    print(f"📊 Метрики: http://0.0.0.0:{PORT}/metrics")
    print(f"🏥 Health check: http://0.0.0.0:{PORT}/health")
    print("=" * 60)
    print("⏳ Запускаем сервер...")

    # Транспорт: streamable-http (по умолчанию, эндпоинт /mcp) или sse (эндпоинт /sse).
    # Лабы 3–5 ходят в MCP по REST, лаба 6 — по streamable-http, лаба 2 (ADK) — по SSE.

    try:
        mcp.run(transport=transport, host="0.0.0.0", port=PORT)
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки (Ctrl+C)")
        print("✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        raise


if __name__ == "__main__":
    main()
