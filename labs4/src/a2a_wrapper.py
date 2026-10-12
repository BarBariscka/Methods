"""Обертка SmolAgents агента для A2A протокола."""
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator

logger = logging.getLogger(__name__)


def _to_text(result: Any) -> str:
    """Приводит результат агента к строке.

    CodeAgent.run() может вернуть RunResult, число, список или строку —
    A2A ожидает текст, поэтому нормализуем значение.
    """
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    # RunResult из smolagents: берём поле output
    output = getattr(result, "output", None)
    if output is not None:
        return str(output)
    return str(result)


class SmolAgentsA2AWrapper:
    """Обертка для преобразования SmolAgents агента в A2A-совместимый интерфейс."""
    
    def __init__(self, agent):
        self.agent = agent
        self.sessions: Dict[str, list] = {}  # Хранение истории сессий
    
    def _get_session_history(self, session_id: str) -> list:
        """Получает историю сессии."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]
    
    async def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        """Выполняет запрос к агенту и возвращает результат."""
        try:
            # Получаем историю сессии
            chat_history = self._get_session_history(session_id)
            
            # Выполняем агента в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.agent.run(query)
            )
            result = _to_text(result)
            
            # Обновляем историю
            chat_history.append(("user", query))
            chat_history.append(("assistant", result))
            
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": result,
                "is_error": False,
                "is_event": False
            }
        except Exception as e:
            logger.error(f"Error in invoke: {e}", exc_info=True)
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"Ошибка: {str(e)}",
                "is_error": True,
                "is_event": False
            }
    
    async def stream(self, query: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Потоковое выполнение запроса к агенту."""
        try:
            # Получаем историю сессии
            chat_history = self._get_session_history(session_id)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.agent.run(query)
            )
            result = _to_text(result)
            
            # Отправляем результат по частям для имитации streaming
            chunk_size = 50
            for i in range(0, len(result), chunk_size):
                chunk = result[i:i+chunk_size]
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": chunk,
                    "is_error": False,
                    "is_event": False
                }
            
            # Обновляем историю
            chat_history.append(("user", query))
            chat_history.append(("assistant", result))
            
            # Финальный чанк
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "",
                "is_error": False,
                "is_event": False
            }
            
        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"Ошибка: {str(e)}",
                "is_error": True,
                "is_event": False
            }
    
    # Для совместимости с A2A
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]


