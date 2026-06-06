FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY pyproject.toml ./
COPY app ./app
COPY mcp_servers ./mcp_servers
COPY data ./data
COPY docker ./docker
COPY streamlit_app.py ./streamlit_app.py

RUN pip install --upgrade pip \
    && pip install .

RUN mkdir -p /home/appuser/.streamlit \
    && chown -R appuser:appgroup /app /home/appuser
USER appuser

EXPOSE 8501

CMD ["sh", "/app/docker/start-streamlit.sh"]
