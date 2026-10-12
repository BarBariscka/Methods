"""Инструмент для расчета аннуитетного кредита."""

from fastmcp import Context
from mcp.types import TextContent
from opentelemetry import trace
from pydantic import Field

from mcp_instance import mcp
from calculations import annuity_schedule
from validators import check_principal, check_rate, check_months
from metrics import TOOL_CALLS, CALCULATION_ERRORS, API_CALLS
from tools.utils import ToolResult, format_calculation_result

tracer = trace.get_tracer(__name__)


@mcp.tool(
    name="loan_schedule_annuity",
    description="""Аннуитетный кредит: расчёт фиксированного ежемесячного платежа и помесячного графика.

Инструмент строит таблицу платежей по аннуитетной схеме. Для каждого месяца возвращаются:
- payment: платёж, interest: проценты, principal_component: тело, remaining_principal: остаток,
  cumulative_interest / cumulative_principal: накопленные суммы.

Пример вызова: {"principal": 1000000, "annual_rate_percent": 12, "months": 24}
""",
    annotations={
        "title": "График аннуитетного кредита",
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
    tags={"credit", "loan", "annuity", "schedule"},
)
async def loan_schedule_annuity(
    principal: float = Field(
        ...,
        description="Сумма кредита (> 0, ≤ лимита)"
    ),
    annual_rate_percent: float = Field(
        ...,
        description="Годовая ставка в процентах (0..лимит)"
    ),
    months: int = Field(
        ...,
        description="Срок в месяцах (1..лимит)"
    ),
    ctx: Context = None
) -> ToolResult:
    """
    Аннуитетный кредит: расчёт фиксированного ежемесячного платежа и помесячного графика.

    Инструмент строит таблицу платежей по аннуитетной схеме. Для каждого месяца возвращаются:
    - payment: платёж, interest: проценты, principal_component: тело, remaining_principal: остаток,
      cumulative_interest / cumulative_principal: накопленные суммы.

    Args:
        principal: Сумма кредита (> 0, ≤ лимита).
        annual_rate_percent: Годовая ставка в процентах (0..лимит).
        months: Срок в месяцах (1..лимит).
        ctx: Контекст для логирования и прогресс-отчетов.

    Returns:
        ToolResult: Результат расчета с графиком платежей и сводкой.

    Raises:
        McpError: При неверных/слишком больших значениях.
    Note:
        Денежные величины округляются до 2 знаков. В последний месяц — коррекция, чтобы остаток стал 0.00.
    """
    tool_name = "loan_schedule_annuity"
    
    with tracer.start_as_current_span(tool_name) as span:
        span.set_attribute("principal", principal)
        span.set_attribute("annual_rate_percent", annual_rate_percent)
        span.set_attribute("months", months)
        
        if ctx:
            await ctx.info(f"🔢 Рассчитываем аннуитетный кредит: {principal} руб., {annual_rate_percent}% годовых, {months} мес.")
            await ctx.report_progress(progress=0, total=100)
        
        API_CALLS.labels(
            service="mcp",
            endpoint=tool_name,
            status="started"
        ).inc()
        
        try:
            # Валидация параметров
            check_principal(principal)
            check_rate(annual_rate_percent)
            check_months(months)
            
            if ctx:
                await ctx.report_progress(progress=50, total=100)
            
            # Выполнение расчета
            result = annuity_schedule(principal, annual_rate_percent, months)
            
            if ctx:
                await ctx.report_progress(progress=100, total=100)
                await ctx.info("✅ Расчет завершен успешно")
            
            # Форматирование результата
            formatted_text = format_calculation_result(result, "Аннуитетный кредит")
            
            span.set_attribute("success", True)
            span.set_attribute("monthly_payment", result["summary"].get("monthly_payment", 0))
            span.set_attribute("total_paid", result["summary"].get("total_paid", 0))
            
            TOOL_CALLS.labels(tool_name=tool_name, status="success").inc()
            API_CALLS.labels(
                service="mcp",
                endpoint=tool_name,
                status="success"
            ).inc()
            
            return ToolResult(
                content=[TextContent(type="text", text=formatted_text)],
                structured_content=result,
                meta={
                    "tool_name": tool_name,
                    "principal": principal,
                    "annual_rate_percent": annual_rate_percent,
                    "months": months,
                }
            )
            
        except ValueError as e:
            span.set_attribute("error", "validation_error")
            span.set_attribute("error_message", str(e))
            
            TOOL_CALLS.labels(tool_name=tool_name, status="validation_error").inc()
            CALCULATION_ERRORS.labels(tool_name=tool_name, error_type="validation").inc()
            API_CALLS.labels(
                service="mcp",
                endpoint=tool_name,
                status="error"
            ).inc()
            
            if ctx:
                await ctx.error(f"❌ Ошибка валидации: {e}")
            
            from mcp.shared.exceptions import McpError, ErrorData
            raise McpError(
                ErrorData(
                    code=-32602,  # Invalid params
                    message=f"Неверные параметры: {e}"
                )
            )
        except Exception as e:
            span.set_attribute("error", "calculation_error")
            span.set_attribute("error_message", str(e))
            
            TOOL_CALLS.labels(tool_name=tool_name, status="error").inc()
            CALCULATION_ERRORS.labels(tool_name=tool_name, error_type="calculation").inc()
            API_CALLS.labels(
                service="mcp",
                endpoint=tool_name,
                status="error"
            ).inc()
            
            if ctx:
                await ctx.error(f"❌ Ошибка расчета: {e}")
            
            from mcp.shared.exceptions import McpError, ErrorData
            raise McpError(
                ErrorData(
                    code=-32603,  # Internal error
                    message=f"Ошибка при выполнении расчета: {e}"
                )
            )
