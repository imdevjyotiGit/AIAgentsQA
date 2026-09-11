# Intelligent Test Planning Agent - container image
#
# Build:  docker build -t test-planning-agent:latest .
# Run:    docker run -p 8088:8088 test-planning-agent:latest
#
# The app talks to an LLM endpoint (Ollama by default) and to Jira. Neither is
# bundled here: both are configured at runtime by the user in the UI, so no
# credentials are ever baked into the image.

FROM python:3.11-slim AS base

# Never write .pyc files, never buffer stdout - logs must appear immediately
# in `docker logs` rather than being held in a buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first so this layer is cached across source-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY tools/ ./tools/
COPY web/ ./web/
COPY architecture/ ./architecture/
COPY "Test Plan Template/" "./Test Plan Template/"

# Writable dirs for generated exports and the log file. Created explicitly so
# they exist with the right ownership before the app drops to a non-root user.
RUN mkdir -p /app/.tmp /app/logs

# Run as an unprivileged user. The container has no need for root, and this
# limits the blast radius if the app is ever compromised.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# 0.0.0.0 is required inside a container - binding 127.0.0.1 would make the
# published port unreachable from the host.
ENV HOST=0.0.0.0 \
    PORT=8088 \
    LLM_TIMEOUT_SECONDS=600 \
    OLLAMA_NUM_CTX=16384

EXPOSE 8088

# Uses the dependency-free /health endpoint so a downstream Ollama/Jira outage
# does not cause the container to be marked unhealthy and restarted.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8088/health', timeout=4).status==200 else 1)"

WORKDIR /app/tools
CMD ["python", "server.py"]
