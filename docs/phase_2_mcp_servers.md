# Phase 2 MCP Servers

## Goal

Create three independent FastMCP servers over the AI Dashboard fake enterprise dataset.

## Folder Structure

```text
enterprise-ai-ops-assistant/
|-- .env.example
|-- pyproject.toml
|-- data/
|   `-- seed/
|       |-- tickets.json
|       |-- project_documents.json
|       `-- deployment_logs.json
|-- mcp_servers/
|   |-- README.md
|   |-- __init__.py
|   |-- ticket_server.py
|   |-- document_server.py
|   |-- log_server.py
|   `-- common/
|       |-- __init__.py
|       |-- config.py
|       |-- errors.py
|       |-- logging_config.py
|       |-- repository.py
|       |-- search.py
|       |-- server.py
|       |-- tooling.py
|       `-- types.py
`-- scripts/
    |-- validate_mcp_data_access.py
    |-- generate_all_datasets.py
    |-- generate_tickets_dataset.py
    |-- generate_project_documents_dataset.py
    `-- generate_deployment_logs_dataset.py
```

## Server Inventory

### Ticket MCP Server

Module:

```text
mcp_servers.ticket_server
```

Tools:

```text
search_tickets(query, priority, status, owner, limit)
get_ticket_by_id(ticket_id)
list_open_tickets(priority, owner, limit)
list_blockers(owner, dependency, limit)
```

### Document MCP Server

Module:

```text
mcp_servers.document_server
```

Tools:

```text
search_documents(query, document_type, service, environment, limit)
get_document(document_id)
```

### Log MCP Server

Module:

```text
mcp_servers.log_server
```

Tools:

```text
search_logs(query, log_type, severity, service, environment, since, until, limit)
get_recent_failures(service, environment, limit)
```

## Run Commands

Install dependencies:

```powershell
python -m pip install -e .
```

Run over STDIO:

```powershell
python -m mcp_servers.ticket_server
python -m mcp_servers.document_server
python -m mcp_servers.log_server
```

Run over HTTP:

```powershell
python -m mcp_servers.ticket_server --transport http --port 8101
python -m mcp_servers.document_server --transport http --port 8102
python -m mcp_servers.log_server --transport http --port 8103
```

## Validation

```powershell
python scripts\validate_mcp_data_access.py
python -m compileall mcp_servers scripts
```

