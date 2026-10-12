# SmolAgents Agent — A2A-сервер
# Python 3.12 (совпадает с requires-python в pyproject.toml)
FROM python:3.12-slim-bookworm

WORKDIR /app

# Системные зависимости + uv (менеджер пакетов проекта)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Метаданные и lock-файл — слой кешируется при неизменных зависимостях
COPY pyproject.toml uv.lock README.md ./

# Исходники
COPY src/ ./src/

# Установка зависимостей строго по lock-файлу
RUN uv sync --frozen --no-dev

# Непривилегированный пользователь
RUN useradd --create-home --shell /bin/bash --uid 1000 agent && \
    chown -R agent:agent /app

USER agent

# A2A-сервер слушает порт 10000 внутри контейнера
EXPOSE 10000

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

CMD ["uv", "run", "python", "src/start_a2a.py"]