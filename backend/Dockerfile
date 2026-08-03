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

# .pytest_cache is created here for the same reason frontend/Dockerfile creates
# .astro: local dev shadows it with an anonymous volume, and Docker seeds a
# volume's ownership from the image directory it shadows — absent from the image,
# the volume lands root-owned and pytest cannot write it. Unused in production.
RUN useradd -u 10001 -m appuser \
    && mkdir -p /app/.pytest_cache \
    && chown -R appuser:appuser /app
ENV HOME=/home/appuser \
    UV_CACHE_DIR=/home/appuser/.cache/uv
USER appuser

# Serving-only boot: migrate/bootstrap_admin/createcachetable are one-shot,
# run-once-per-deploy steps and MUST NOT execute per replica — with
# desiredCount > 1 every replica running `migrate` concurrently races DDL
# against the same database (docs/BD.md "Migration execution points"). Those
# steps run as a separate, blocking one-off ECS task registered and awaited
# by .github/workflows/deploy-prod.yml BEFORE the service update, never here.
# Local dev keeps the old self-migrating chain via compose.yaml's `command:`
# override on the `backend` service, which this CMD is only the fallback for.
CMD ["sh", "-c", "uv run python manage.py check --deploy && uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS}"]
