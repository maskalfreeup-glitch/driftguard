FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN groupadd -g 10001 driftguard && \
    useradd -u 10001 -g driftguard -s /bin/bash -m driftguard

COPY sentinel/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY sentinel /app/sentinel

RUN chown -R driftguard:driftguard /app

USER driftguard

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "sentinel.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
