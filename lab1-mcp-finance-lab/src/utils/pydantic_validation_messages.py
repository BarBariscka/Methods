"""Человекочитаемые сообщения для ошибок валидации Pydantic (в т.ч. вызовы MCP-инструментов)."""

from __future__ import annotations

from typing import Any

try:
    from pydantic import ValidationError
except ImportError:
    ValidationError = None  # type: ignore[misc, assignment]


_ARG_HINTS_RU: dict[str, str] = {
    "principal": "сумма кредита (число > 0 в пределах лимита)",
    "annual_rate_percent": "годовая процентная ставка в процентах",
    "months": "срок в месяцах (целое число в допустимом диапазоне)",
    "initial_amount": "начальная сумма вклада или инвестиций",
    "monthly_contribution": "ежемесячное пополнение (может быть 0)",
    "contribution_at_beginning": "true — взнос в начале месяца, false — в конце",
}


def _unwrap_validation_error(exc: BaseException) -> Any:
    """Достаёт pydantic.ValidationError из цепочки причин."""
    if ValidationError is None:
        return None
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, ValidationError):
            return current
        current = current.__cause__ or getattr(current, "__context__", None)
    return None


def format_validation_error_ru(ve: Any) -> str:
    """Форматирует ValidationError в короткий текст по-русски."""
    lines: list[str] = ["Неверные аргументы вызова инструмента."]
    try:
        errors = ve.errors()
    except Exception:
        return f"Неверные аргументы: {ve!s}"

    for err in errors:
        loc = err.get("loc") or ()
        loc_parts = [str(p) for p in loc if p not in ("body", "call", "arguments")]
        field_key = loc_parts[-1] if loc_parts else ""
        hint = _ARG_HINTS_RU.get(field_key, "")
        msg = (err.get("msg") or "").strip()
        typ = err.get("type") or ""

        if typ == "model_type" and "Input should be a valid dictionary" in msg:
            detail = hint or f"поле «{field_key}»"
            lines.append(f"• {field_key}: передайте объект {detail}, не null и не пустой ключ.")
        elif typ == "missing":
            lines.append(f"• {field_key}: отсутствует обязательное значение ({hint or 'см. описание поля'}).")
        else:
            extra = f" — {hint}" if hint else ""
            lines.append(f"• {field_key}: {msg}{extra}")

    return "\n".join(lines)


def maybe_mcp_error_from_validation(exc: BaseException) -> Any:
    """Если exc содержит ValidationError — вернуть McpError с русским текстом, иначе None."""
    ve = _unwrap_validation_error(exc)
    if ve is None:
        return None
    try:
        from mcp.types import ErrorData
        from mcp import McpError
    except ImportError:
        return None
    text = format_validation_error_ru(ve)
    return McpError(ErrorData(code=-32602, message=text))
