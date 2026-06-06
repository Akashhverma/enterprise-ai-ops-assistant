#!/usr/bin/env sh
set -eu

SERVER="${MCP_SERVER:-ticket}"
HOST="${MCP_HOST:-0.0.0.0}"

case "$SERVER" in
  ticket)
    MODULE="mcp_servers.ticket_server"
    PORT="${TICKET_MCP_PORT:-8101}"
    ;;
  document)
    MODULE="mcp_servers.document_server"
    PORT="${DOCUMENT_MCP_PORT:-8102}"
    ;;
  log)
    MODULE="mcp_servers.log_server"
    PORT="${LOG_MCP_PORT:-8103}"
    ;;
  *)
    echo "Unknown MCP_SERVER value: $SERVER" >&2
    exit 2
    ;;
esac

exec python -m "$MODULE" --transport http --host "$HOST" --port "$PORT"
