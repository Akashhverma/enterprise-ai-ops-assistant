# Phase 8 Docker & Deployment

## Goal

Production-ready one-command Docker deployment for the Enterprise AI Operations Assistant.

## Services

```text
fastapi       FastAPI backend and LangGraph API
streamlit     Portfolio UI
chromadb      Vector database service
ticket-mcp    Ticket FastMCP server
document-mcp  Document FastMCP server
log-mcp       Log FastMCP server
```

## Files

```text
enterprise-ai-ops-assistant/
|-- docker-compose.yml
|-- .dockerignore
|-- .env.docker
|-- .env.docker.example
|-- docker/
|   |-- api.Dockerfile
|   |-- streamlit.Dockerfile
|   |-- mcp.Dockerfile
|   |-- start-api.sh
|   |-- start-streamlit.sh
|   |-- start-mcp.sh
|   `-- healthcheck.py
`-- scripts/
    `-- docker_smoke_test.py
```

## One-Command Deployment

```powershell
docker-compose up --build
```

Modern Docker Compose also supports:

```powershell
docker compose up --build
```

## URLs

```text
Streamlit UI:     http://127.0.0.1:8501
FastAPI:          http://127.0.0.1:8000
OpenAPI Docs:     http://127.0.0.1:8000/docs
ChromaDB:         http://127.0.0.1:8001
Ticket MCP:       http://127.0.0.1:8101/health
Document MCP:     http://127.0.0.1:8102/health
Log MCP:          http://127.0.0.1:8103/health
```

## Environment

Defaults live in `.env.docker`.

Important values:

```text
OPENAI_API_KEY
OPENAI_MODEL
API_WORKERS
API_CORS_ORIGINS
STREAMLIT_API_BASE_URL
CHROMA_IMAGE
CHROMA_HOST_PORT
TICKET_MCP_PORT
DOCUMENT_MCP_PORT
LOG_MCP_PORT
```

For production, inject secrets from your platform rather than baking them into images.

## Validate

After the stack is running:

```powershell
python scripts\docker_smoke_test.py
```

## Stop

```powershell
docker-compose down
```

To delete Chroma data too:

```powershell
docker-compose down -v
```

