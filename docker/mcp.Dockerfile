FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY pyproject.toml ./
COPY mcp_servers ./mcp_servers
COPY data ./data
COPY docker ./docker
COPY scripts ./scripts

RUN pip install --upgrade pip \
    && pip install .

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8101 8102 8103

CMD ["sh", "/app/docker/start-mcp.sh"]
