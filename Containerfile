FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY jetpage/ ./jetpage/

# Install Playwright's Chromium browser and its OS dependencies
RUN uv run playwright install --with-deps chromium

COPY content/ ./content/

ENV PORT=8080 \
    HOST=0.0.0.0 \
    CONTENT_DIR=/app/content

EXPOSE 8080

CMD ["uv", "run", "jetpage"]
