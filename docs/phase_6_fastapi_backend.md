# Phase 6 FastAPI Backend

## Goal

Expose the Enterprise AI Operations Assistant through HTTP APIs backed by the LangGraph workflow.

## Folder Structure

```text
enterprise-ai-ops-assistant/
|-- app/
|   |-- main.py
|   |-- api/
|   |   |-- __init__.py
|   |   |-- dependencies.py
|   |   |-- models.py
|   |   `-- routes.py
|   |-- core/
|   |   |-- __init__.py
|   |   |-- config.py
|   |   |-- errors.py
|   |   `-- logging.py
|   |-- services/
|   |   |-- __init__.py
|   |   `-- langgraph_service.py
|   `-- agents/
|       `-- ...
|-- scripts/
|   |-- run_api.py
|   `-- validate_api.py
`-- docs/
    `-- phase_6_fastapi_backend.md
```

## Endpoints

```text
GET  /health
POST /query
POST /chat
GET  /tickets
GET  /logs
```

## Run

```powershell
python scripts\run_api.py
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

Validation:

```powershell
python scripts\validate_api.py
```

