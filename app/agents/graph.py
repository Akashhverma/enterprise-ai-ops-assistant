from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from mcp_servers.common.logging_config import configure_logging

from .mcp_tool_client import MCPToolClient, create_mcp_tool_client
from .models import AgentOutput, FinalReport, PlannerOutput
from .planner import PlannerAgent
from .report import ReportAgent
from .retrieval_agents import DocumentAgent, LogAgent, TicketAgent
from .state import OpsAssistantState, empty_state


logger = configure_logging(__name__)


def build_ops_assistant_graph(tool_client: MCPToolClient | None = None):
    client = tool_client or create_mcp_tool_client(logger=logger)
    planner_agent = PlannerAgent()
    ticket_agent = TicketAgent(client)
    document_agent = DocumentAgent(client)
    log_agent = LogAgent(client)
    report_agent = ReportAgent()

    builder = StateGraph(OpsAssistantState)
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_interval=0.25,
        backoff_factor=2.0,
        max_interval=2.0,
    )

    def planner_node(state: OpsAssistantState) -> dict[str, Any]:
        question = _required_question(state)
        plan = planner_agent.plan(question)
        logger.info("planner intent=%s", plan.intent)
        return {
            "started_at": _now(),
            "plan": plan.model_dump(),
        }

    def ticket_node(state: OpsAssistantState) -> dict[str, Any]:
        plan = _required_plan(state)
        output = ticket_agent.run(plan)
        return _agent_state_update("ticket_agent", output)

    def document_node(state: OpsAssistantState) -> dict[str, Any]:
        plan = _required_plan(state)
        output = document_agent.run(plan)
        return _agent_state_update("document_agent", output)

    def log_node(state: OpsAssistantState) -> dict[str, Any]:
        plan = _required_plan(state)
        output = log_agent.run(plan)
        return _agent_state_update("log_agent", output)

    def report_node(state: OpsAssistantState) -> dict[str, Any]:
        question = _required_question(state)
        plan = _required_plan(state)
        ticket_output = _agent_output_from_state(state, "ticket_agent")
        document_output = _agent_output_from_state(state, "document_agent")
        log_output = _agent_output_from_state(state, "log_agent")

        final_report = report_agent.run(
            question=question,
            plan=plan,
            ticket_output=ticket_output,
            document_output=document_output,
            log_output=log_output,
            graph_errors=state.get("errors", []),
        )
        logger.info("report confidence=%s citations=%s", final_report.confidence, len(final_report.citations))
        return {
            "completed_at": _now(),
            "final_report": final_report.model_dump(),
        }

    builder.add_node("planner_agent", planner_node, retry_policy=retry_policy)
    builder.add_node("ticket_agent", ticket_node, retry_policy=retry_policy)
    builder.add_node("document_agent", document_node, retry_policy=retry_policy)
    builder.add_node("log_agent", log_node, retry_policy=retry_policy)
    builder.add_node("report_agent", report_node, retry_policy=retry_policy)

    builder.add_edge(START, "planner_agent")
    builder.add_edge("planner_agent", "ticket_agent")
    builder.add_edge("planner_agent", "document_agent")
    builder.add_edge("planner_agent", "log_agent")
    builder.add_edge(["ticket_agent", "document_agent", "log_agent"], "report_agent")
    builder.add_edge("report_agent", END)

    return builder.compile()


def run_ops_question(question: str, *, tool_client: MCPToolClient | None = None) -> FinalReport:
    graph = build_ops_assistant_graph(tool_client=tool_client)
    final_state = graph.invoke(empty_state(question))
    final_report = final_state.get("final_report")
    if not final_report:
        raise RuntimeError("LangGraph workflow completed without a final_report.")
    return FinalReport.model_validate(final_report)


def _agent_state_update(key: str, output: AgentOutput) -> dict[str, Any]:
    dumped = output.model_dump()
    return {
        key: dumped,
        "tool_calls": [call.model_dump() for call in output.tool_calls],
        "errors": output.errors,
    }


def _required_question(state: OpsAssistantState) -> str:
    question = state.get("user_question")
    if not question:
        raise ValueError("State is missing user_question.")
    return question


def _required_plan(state: OpsAssistantState) -> PlannerOutput:
    plan = state.get("plan")
    if not plan:
        raise ValueError("State is missing planner output.")
    return PlannerOutput.model_validate(plan)


def _agent_output_from_state(state: OpsAssistantState, key: str) -> AgentOutput:
    value = state.get(key)
    if not value:
        return AgentOutput(
            agent_name=key,  # type: ignore[arg-type]
            status="failed",
            summary=f"{key} did not return output.",
            errors=[f"{key} did not return output."],
        )
    return AgentOutput.model_validate(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
