# MCP Servers

This package contains three independent FastMCP servers for the AI Dashboard enterprise dataset.

## Servers

```text
mcp_servers.ticket_server    Ticket data tools
mcp_servers.document_server  Project document tools
mcp_servers.log_server       Deployment log tools
```

## Run With STDIO

STDIO is the default transport and is suitable for local MCP clients:

```powershell
python -m mcp_servers.ticket_server
python -m mcp_servers.document_server
python -m mcp_servers.log_server
```

## Run With HTTP

Each server can also run independently over HTTP:

```powershell
python -m mcp_servers.ticket_server --transport http --port 8101
python -m mcp_servers.document_server --transport http --port 8102
python -m mcp_servers.log_server --transport http --port 8103
```

## Data Directory

By default the servers read from `data/seed`.

Override the dataset location with:

```powershell
$env:AI_DASHBOARD_SEED_DIR="data\seed"
```

## Health Checks

When running with HTTP transport, each server exposes:

```text
GET /health
```

