# Phase 7 Streamlit Frontend

## Goal

Create a portfolio-ready Streamlit dashboard for the Enterprise AI Operations Assistant.

## Files

```text
enterprise-ai-ops-assistant/
|-- streamlit_app.py
|-- app/
|   `-- frontend/
|       |-- __init__.py
|       |-- client.py
|       |-- config.py
|       |-- local_backend.py
|       `-- styles.py
|-- scripts/
|   |-- run_streamlit.py
|   `-- validate_streamlit_frontend.py
`-- docs/
    `-- phase_7_streamlit_frontend.md
```

## Features

```text
1. Chat interface
2. Ticket viewer
3. Deployment log viewer
4. Retrieved document viewer
5. Agent execution trace
6. MCP tool calls visualization
```

## Run

Start the FastAPI backend:

```powershell
python scripts\run_api.py
```

Start the Streamlit frontend:

```powershell
python scripts\run_streamlit.py
```

Default URL:

```text
http://127.0.0.1:8501
```

The frontend can also run in local fallback mode through the sidebar backend selector.

