FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    APP_NAME="Studly API" \
    APP_ENV=production \
    APP_VERSION=1.0.0 \
    HTTP_PORT=8080

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY --chown=app:app cmd ./cmd
COPY --chown=app:app internal ./internal

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('HTTP_PORT', '8080'), timeout=2)" || exit 1

CMD ["sh", "-c", "exec python -m uvicorn cmd.app.main:app --host 0.0.0.0 --port ${HTTP_PORT}"]