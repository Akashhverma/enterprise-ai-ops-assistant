from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.frontend.client import BackendMode, FrontendClient  # noqa: E402
from app.frontend.styles import CSS  # noqa: E402


st.set_page_config(
    page_title="Enterprise AI Operations Assistant",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)


SERVICES = [
    "dashboard-api",
    "auth-service",
    "telemetry-ingestion",
    "analytics-worker",
    "reporting-service",
    "model-insights-service",
    "notification-service",
    "admin-console",
    "feature-store-sync",
    "vector-search-gateway",
]

ENVIRONMENTS = ["dev", "staging", "production"]
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
TICKET_STATUSES = ["Backlog", "In Progress", "Blocked", "In Review", "Resolved", "Closed"]
LOG_TYPES = [
    "deployment failure",
    "authentication failure",
    "database migration issue",
    "api timeout error",
]
SEVERITIES = ["ERROR", "WARN", "INFO", "FATAL"]

SAMPLE_PROMPTS = [
    "Why did the production dashboard deployment fail?",
    "Show blockers related to dashboard timeout incidents.",
    "Summarize recent authentication failures for enterprise users.",
    "Find database migration issues and the likely remediation.",
]


@st.cache_resource
def get_client() -> FrontendClient:
    return FrontendClient()


def init_state() -> None:
    st.session_state.setdefault(
        "messages",
        [
            {
                "role": "assistant",
                "content": "Enterprise AI Operations Assistant is online.",
            }
        ],
    )
    st.session_state.setdefault("last_response", None)
    st.session_state.setdefault("last_debug", None)
    st.session_state.setdefault("last_question", None)
    st.session_state.setdefault("pending_prompt", None)


def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    client = get_client()

    mode = render_sidebar(client)
    render_header(client)

    tabs = st.tabs(
        [
            "Copilot",
            "Tickets",
            "Deployment Logs",
            "Retrieved Documents",
            "Agent Trace",
            "MCP Tools",
        ]
    )

    with tabs[0]:
        render_chat(client, mode)

    with tabs[1]:
        render_ticket_viewer(client, mode)

    with tabs[2]:
        render_log_viewer(client, mode)

    with tabs[3]:
        render_document_viewer(client)

    with tabs[4]:
        render_agent_trace()

    with tabs[5]:
        render_tool_calls()


def render_sidebar(client: FrontendClient) -> BackendMode:
    with st.sidebar:
        st.markdown("### Operations Console")
        mode = st.radio("Backend", ["Auto", "FastAPI", "Local"], horizontal=False)
        backend_mode = mode  # type: ignore[assignment]

        try:
            health = client.health(backend_mode)
            st.success(f"{health['service']} - {health['status']}")
            st.caption(f"Mode: {health.get('environment', 'unknown')} | API: {client.api_base_url}")
            if health.get("fallback_reason"):
                st.caption(f"Fallback: {health['fallback_reason']}")
        except Exception as exc:
            st.error(f"Backend unavailable: {exc}")

        st.divider()
        st.markdown("### Quick Prompts")
        for prompt in SAMPLE_PROMPTS:
            if st.button(prompt, use_container_width=True):
                st.session_state.pending_prompt = prompt

        st.divider()
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Enterprise AI Operations Assistant is online.",
                }
            ]
            st.session_state.last_response = None
            st.session_state.last_debug = None
            st.session_state.last_question = None
            st.rerun()

    return backend_mode


def render_header(client: FrontendClient) -> None:
    summary = client.dataset_summary()
    last_response = st.session_state.get("last_response") or {}
    report = last_response.get("report") or {}

    st.markdown(
        """
        <div class="ops-header">
          <h1>Enterprise AI Operations Assistant</h1>
          <p>AI Dashboard operations copilot for tickets, project documents, deployment logs, and agent execution evidence.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    render_metric_card(cols[0], "Tickets", str(summary["tickets"]))
    render_metric_card(cols[1], "Documents", str(summary["documents"]))
    render_metric_card(cols[2], "Deployment Logs", str(summary["logs"]))
    render_metric_card(cols[3], "Last Confidence", str(report.get("confidence", "n/a")).title())
    render_metric_card(cols[4], "Last Citations", str(len(report.get("citations", []))))


def render_metric_card(container: Any, label: str, value: str) -> None:
    with container:
        st.markdown(
            f"""
            <div class="ops-card">
              <div class="ops-card-label">{label}</div>
              <div class="ops-card-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_chat(client: FrontendClient, mode: BackendMode) -> None:
    left, right = st.columns([0.62, 0.38], gap="large")

    with left:
        st.markdown('<div class="ops-section-title">Copilot Chat</div>', unsafe_allow_html=True)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.session_state.pop("pending_prompt", None)
        typed_prompt = st.chat_input("Ask about tickets, incidents, deployments, logs, or project documents")
        prompt = prompt or typed_prompt

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Running planner, retrieval agents, and report synthesis"):
                try:
                    response = client.query(prompt, include_debug=True, mode=mode)
                    report = response["report"]
                    answer = report["answer"]
                    st.session_state.last_response = response
                    st.session_state.last_debug = response.get("debug")
                    st.session_state.last_question = prompt
                except Exception as exc:
                    answer = f"Request failed: {exc}"
                    response = None

            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)
                if response:
                    render_citation_row(response["report"].get("citations", []))

    with right:
        render_response_summary()


def render_response_summary() -> None:
    response = st.session_state.get("last_response")
    if not response:
        st.info("Run a query to populate report evidence, citations, trace, and MCP tool-call panels.")
        return

    report = response["report"]
    st.markdown('<div class="ops-section-title">Current Report</div>', unsafe_allow_html=True)
    st.markdown(status_pill(report.get("confidence", "low"), "info"), unsafe_allow_html=True)
    st.caption(f"Request: {response['request_id']} | {response['duration_ms']} ms")

    source_summary = report.get("source_summary", {})
    for label, value in source_summary.items():
        with st.expander(label.title(), expanded=True):
            st.write(value)

    if report.get("next_actions"):
        st.markdown("**Next Actions**")
        for action in report["next_actions"]:
            st.write(f"- {action}")


def render_ticket_viewer(client: FrontendClient, mode: BackendMode) -> None:
    st.markdown('<div class="ops-section-title">Ticket Viewer</div>', unsafe_allow_html=True)
    filters = st.columns([2.2, 1, 1, 1.4, 0.9, 0.8])
    query = filters[0].text_input("Ticket search", value="", placeholder="dashboard, timeout, auth")
    priority = filters[1].selectbox("Priority", [""] + PRIORITIES)
    status = filters[2].selectbox("Status", [""] + TICKET_STATUSES)
    owner = filters[3].text_input("Owner", value="", placeholder="Maya")
    blockers_only = filters[4].toggle("Blockers")
    limit = filters[5].number_input("Limit", min_value=5, max_value=50, value=25, step=5)

    try:
        payload = client.tickets(
            mode=mode,
            query=query or None,
            priority=priority or None,
            status=status or None,
            owner=owner or None,
            blockers_only=blockers_only,
            limit=int(limit),
        )
    except Exception as exc:
        st.error(f"Could not load tickets: {exc}")
        return

    results = payload.get("results", [])
    st.caption(f"{payload.get('count', 0)} shown of {payload.get('total_matches', 0)} matches")
    if not results:
        st.warning("No tickets matched the current filters.")
        return

    frame = pd.DataFrame(results)
    display_cols = [
        "ticket_id",
        "priority",
        "status",
        "owner",
        "title",
        "dependency",
        "created_date",
    ]
    st.dataframe(frame[[col for col in display_cols if col in frame.columns]], use_container_width=True)

    selected_id = st.selectbox("Ticket detail", frame["ticket_id"].tolist())
    selected = next(item for item in results if item["ticket_id"] == selected_id)
    render_ticket_detail(selected)


def render_ticket_detail(ticket: dict[str, Any]) -> None:
    cols = st.columns([1, 1, 1, 2])
    cols[0].markdown(status_pill(ticket["priority"], "info"), unsafe_allow_html=True)
    cols[1].markdown(status_pill(ticket["status"].lower().replace(" ", "-"), _status_class(ticket["status"])), unsafe_allow_html=True)
    cols[2].caption(ticket["created_date"])
    cols[3].caption(f"Owner: {ticket['owner']}")
    st.markdown(f"**{ticket['ticket_id']} - {ticket['title']}**")
    st.write(ticket["description"])
    st.caption(f"Dependency: {ticket['dependency']}")


def render_log_viewer(client: FrontendClient, mode: BackendMode) -> None:
    st.markdown('<div class="ops-section-title">Deployment Log Viewer</div>', unsafe_allow_html=True)
    filters = st.columns([2.1, 1.4, 0.9, 1.3, 1.1, 0.9, 0.8])
    query = filters[0].text_input("Log search", value="", placeholder="timeout, migration, auth")
    log_type = filters[1].selectbox("Log type", [""] + LOG_TYPES)
    severity = filters[2].selectbox("Severity", [""] + SEVERITIES)
    service = filters[3].selectbox("Service", [""] + SERVICES)
    environment = filters[4].selectbox("Environment", [""] + ENVIRONMENTS)
    recent = filters[5].toggle("Recent failures", value=True)
    limit = filters[6].number_input("Rows", min_value=5, max_value=50, value=25, step=5)

    try:
        payload = client.logs(
            mode=mode,
            query=query or None,
            log_type=log_type or None,
            severity=severity or None,
            service=service or None,
            environment=environment or None,
            recent_failures=recent,
            limit=int(limit),
        )
    except Exception as exc:
        st.error(f"Could not load logs: {exc}")
        return

    results = payload.get("results", [])
    st.caption(f"{payload.get('count', 0)} shown of {payload.get('total_matches', 0)} matches")
    if not results:
        st.warning("No logs matched the current filters.")
        return

    frame = pd.DataFrame(results)
    display_cols = [
        "timestamp",
        "severity",
        "status",
        "log_type",
        "service",
        "environment",
        "error_code",
        "related_ticket_id",
    ]
    st.dataframe(frame[[col for col in display_cols if col in frame.columns]], use_container_width=True)

    selected_id = st.selectbox("Log detail", frame["log_id"].tolist())
    selected = next(item for item in results if item["log_id"] == selected_id)
    render_log_detail(selected)


def render_log_detail(log: dict[str, Any]) -> None:
    cols = st.columns([1, 1, 1, 1.6])
    cols[0].markdown(status_pill(log["severity"], "failed" if log["severity"] == "ERROR" else "partial"), unsafe_allow_html=True)
    cols[1].markdown(status_pill(log["status"], _status_class(log["status"])), unsafe_allow_html=True)
    cols[2].caption(log["timestamp"])
    cols[3].caption(log["deployment_id"])
    st.markdown(f"**{log['log_id']} - {log['error_code']}**")
    st.write(log["message"])
    st.caption(f"Trace: {log['trace_id']} | Related ticket: {log['related_ticket_id']}")
    st.markdown("**Probable Cause**")
    st.write(log["probable_cause"])
    st.markdown("**Remediation Hint**")
    st.write(log["remediation_hint"])


def render_document_viewer(client: FrontendClient) -> None:
    st.markdown('<div class="ops-section-title">Retrieved Document Viewer</div>', unsafe_allow_html=True)
    debug = st.session_state.get("last_debug") or {}
    document_agent = debug.get("document_agent") or {}
    evidence = document_agent.get("evidence", [])

    if evidence:
        for item in evidence:
            render_evidence_card(item)
        return

    documents = client.documents()
    st.caption("Project document index")
    query = st.text_input("Document index search", value="", placeholder="architecture, release, incident")
    filtered = _filter_documents(documents, query)
    frame = pd.DataFrame(
        [
            {
                "document_id": doc["document_id"],
                "document_type": doc["document_type"],
                "service": doc["service"],
                "environment": doc["environment"],
                "owner_team": doc["owner_team"],
                "title": doc["title"],
            }
            for doc in filtered
        ]
    )
    st.dataframe(frame, use_container_width=True)

    if filtered:
        selected_id = st.selectbox("Document detail", [doc["document_id"] for doc in filtered])
        selected = next(doc for doc in filtered if doc["document_id"] == selected_id)
        for section in selected["sections"]:
            with st.expander(section["heading"], expanded=True):
                st.write(section["body"])


def render_agent_trace() -> None:
    st.markdown('<div class="ops-section-title">Agent Execution Trace</div>', unsafe_allow_html=True)
    debug = st.session_state.get("last_debug")
    if not debug:
        st.info("Run a copilot query to view agent execution trace.")
        return

    plan = debug.get("plan") or {}
    st.markdown("**Planner Agent**")
    cols = st.columns([1.2, 2.5, 1.3])
    cols[0].markdown(status_pill("success", "success"), unsafe_allow_html=True)
    cols[1].write(plan.get("normalized_question", st.session_state.get("last_question", "")))
    cols[2].caption(f"Intent: {plan.get('intent', 'unknown')}")

    agents = [
        ("Ticket Agent", debug.get("ticket_agent") or {}),
        ("Document Agent", debug.get("document_agent") or {}),
        ("Log Agent", debug.get("log_agent") or {}),
    ]
    agent_cols = st.columns(3)
    for column, (label, output) in zip(agent_cols, agents):
        with column:
            status = output.get("status", "skipped")
            st.markdown(
                f"""
                <div class="ops-card">
                  <div class="ops-card-label">{label}</div>
                  <div>{status_pill(status, _status_class(status))}</div>
                  <p class="ops-muted">{output.get("summary", "No output")}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("Planner output", expanded=False):
        st.json(plan)

    errors = debug.get("errors") or []
    if errors:
        with st.expander("Execution errors", expanded=True):
            for error in errors:
                st.error(error)


def render_tool_calls() -> None:
    st.markdown('<div class="ops-section-title">MCP Tool Calls Visualization</div>', unsafe_allow_html=True)
    debug = st.session_state.get("last_debug")
    if not debug:
        st.info("Run a copilot query to view MCP tool calls.")
        return

    calls = debug.get("tool_calls") or []
    if not calls:
        st.warning("No MCP tool calls were recorded for the latest run.")
        return

    frame = pd.DataFrame(calls)
    cols = st.columns([0.58, 0.42], gap="large")
    with cols[0]:
        st.dataframe(
            frame[
                [
                    "server",
                    "tool_name",
                    "transport",
                    "fallback_used",
                    "status",
                    "attempts",
                    "result_count",
                    "error",
                ]
            ],
            use_container_width=True,
        )
    with cols[1]:
        chart = frame.groupby(["server", "status"]).size().reset_index(name="calls")
        chart["series"] = chart["server"] + " / " + chart["status"]
        st.bar_chart(chart, x="series", y="calls", use_container_width=True)

    for index, call in enumerate(calls, start=1):
        with st.expander(f"{index}. {call['server']}.{call['tool_name']}"):
            st.json(call)


def render_citation_row(citations: list[dict[str, Any]]) -> None:
    if not citations:
        return

    st.caption("Citations")
    cols = st.columns(min(len(citations), 4))
    for index, citation in enumerate(citations[:4]):
        with cols[index % len(cols)]:
            st.markdown(
                f"""
                <div class="ops-evidence">
                  <div class="ops-evidence-title">{citation['source_id']}</div>
                  <div class="ops-muted">{citation['source_type']} | {citation['title']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_evidence_card(item: dict[str, Any]) -> None:
    metadata = item.get("metadata", {})
    with st.expander(f"{item['source_id']} - {item['title']}", expanded=True):
        cols = st.columns([1, 1, 1, 1])
        cols[0].caption(f"Type: {metadata.get('document_type', item.get('source_type'))}")
        cols[1].caption(f"Service: {metadata.get('service', 'n/a')}")
        cols[2].caption(f"Environment: {metadata.get('environment', 'n/a')}")
        cols[3].caption(f"Score: {item.get('relevance_score', 0)}")
        st.write(item.get("snippet", ""))
        if metadata:
            st.json(metadata)


def _filter_documents(documents: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    if not query.strip():
        return documents[:25]

    lowered = query.lower()
    filtered = []
    for document in documents:
        searchable = " ".join(
            [
                document.get("title", ""),
                document.get("document_type", ""),
                document.get("service", ""),
                document.get("environment", ""),
                " ".join(document.get("tags", [])),
                " ".join(section.get("body", "") for section in document.get("sections", [])),
            ]
        ).lower()
        if lowered in searchable:
            filtered.append(document)
    return filtered[:25]


def status_pill(label: str, css_class: str) -> str:
    return f'<span class="ops-pill {css_class}">{label}</span>'


def _status_class(status: str) -> str:
    normalized = status.lower().replace(" ", "-")
    if normalized in {"success", "resolved", "closed", "ok"}:
        return "success"
    if normalized in {"partial", "warn", "warning", "in-progress", "in-review", "degraded"}:
        return "partial"
    if normalized in {"failed", "blocked", "error", "fatal"}:
        return "failed"
    if normalized in {"skipped", "backlog"}:
        return "skipped"
    return "info"


if __name__ == "__main__":
    main()
