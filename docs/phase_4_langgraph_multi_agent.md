# Phase 4 LangGraph Multi-Agent System

## Goal

Build an agentic AI workflow that answers enterprise operations questions by planning retrieval, calling MCP tools, and synthesizing a structured report.

## Workflow

```text
User Question
  -> Planner Agent
  -> Parallel Execution
       -> Ticket Agent
       -> Document Agent
       -> Log Agent
  -> Report Agent
```

## Folder Structure

```text
enterprise-ai-ops-assistant/
|-- app/
|   |-- __init__.py
|   `-- agents/
|       |-- __init__.py
|       |-- config.py
|       |-- graph.py
|       |-- mcp_tool_client.py
|       |-- models.py
|       |-- planner.py
|       |-- report.py
|       |-- retrieval_agents.py
|       `-- state.py
|-- scripts/
|   |-- run_langgraph_workflow.py
|   `-- validate_langgraph_workflow.py
`-- docs/
    `-- phase_4_langgraph_multi_agent.md
```

## Agents

| Agent | Responsibility |
|---|---|
| Planner Agent | Extracts intent, entities, source plans, filters, and preferred tools |
| Ticket Agent | Calls ticket MCP tools and returns structured ticket evidence |
| Document Agent | Calls document MCP tools and returns structured document evidence |
| Log Agent | Calls log MCP tools and returns structured log evidence |
| Report Agent | Synthesizes final structured answer, citations, confidence, and next actions |

## State Management

The graph state is defined in `app/agents/state.py`.

Important state keys:

```text
user_question
plan
ticket_agent
document_agent
log_agent
final_report
tool_calls
errors
started_at
completed_at
```

`tool_calls` and `errors` use reducer semantics so parallel agent branches can append safely.

## Tool Calling

The workflow calls the same tool contracts exposed by the FastMCP layer:

```text
ticket.search_tickets
ticket.get_ticket_by_id
ticket.list_open_tickets
ticket.list_blockers

document.search_documents
document.get_document

log.search_logs
log.get_recent_failures
```

`LocalMCPToolClient` is the default adapter for deterministic local execution. It can be replaced by a remote MCP client without changing graph nodes.

## Retry Logic

Two retry layers are included:

1. LangGraph node retry policy through `RetryPolicy`.
2. MCP tool-call retry loop inside `LocalMCPToolClient`.

Controlled user/data errors are captured and returned in structured agent outputs.

## Run

Install dependencies:

```powershell
python -m pip install -e .
```

Validate:

```powershell
python scripts\validate_langgraph_workflow.py
```

Run a custom question:

```powershell
python scripts\run_langgraph_workflow.py "Why did the production dashboard deployment fail?"
```

