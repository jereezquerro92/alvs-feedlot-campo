FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev
# Build-only dummy: settings refuse to boot keyless outside DEBUG, and no runtime env exists at image-build time. The value never ships.
RUN SECRET_KEY=collectstatic-build-only uv run python manage.py collectstatic --noinput

EXPOSE 8000

ENV UVICORN_WORKERS=4

RUN useradd -u 10001 -m appuser \
    && chown -R appuser:appuser /app
ENV HOME=/home/appuser \
    UV_CACHE_DIR=/home/appuser/.cache/uv
USER appuser

CMD ["sh", "-c", "uv run python manage.py check --deploy && uv run python manage.py migrate --noinput && uv run python manage.py bootstrap_admin && uv run python manage.py createcachetable && uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS}"]
