# Python 3.12 — совпадает с requires-python в pyproject.toml
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Метаданные и lock — слой кешируется при неизменных зависимостях
COPY pyproject.toml uv.lock README.md ./

# Исходники нужны до uv sync: hatch собирает wheel из packages = ["src"]
COPY src/ ./src/

RUN uv sync --frozen --no-editable --no-dev

RUN useradd --create-home --shell /bin/bash --uid 1000 mcp && \
    chown -R mcp:mcp /app

USER mcp

EXPOSE 8000

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    UV_SYSTEM_PYTHON=1

CMD ["uv", "run", "python", "src/server.py"]
