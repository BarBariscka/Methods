"""Обёртка над ErrorHandlingMiddleware: дружелюбные сообщения для Pydantic ValidationError."""

from __future__ import annotations

from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware

from utils.pydantic_validation_messages import maybe_mcp_error_from_validation


class FriendlyErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """Как ErrorHandlingMiddleware, но ошибки валидации аргументов (Pydantic) — по-русски, код -32602."""

    def _transform_error(self, error: Exception) -> Exception:
        from mcp import McpError

        if isinstance(error, McpError):
            return error
        friendly = maybe_mcp_error_from_validation(error)
        if friendly is not None:
            return friendly
        return super()._transform_error(error)
