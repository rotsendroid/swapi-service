# Multi-stage Dockerfile for FastAPI service
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --upgrade uv
# with extra for running tests
RUN uv venv .venv && uv sync --extra dev

FROM python:3.13-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
# For pytest setup
COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/
EXPOSE 8000
RUN pip install --upgrade uv
CMD ["/bin/sh", "-c", "cd src && uv run alembic upgrade head && uv run fastapi run api/main.py"]
