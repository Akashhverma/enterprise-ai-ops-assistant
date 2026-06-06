from __future__ import annotations

import argparse
import json
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "seed"
GENERATED_AT = "2026-05-31T00:00:00Z"

PROJECT_NAME = "AI Dashboard"

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

COMPONENTS = [
    "usage analytics panel",
    "model latency widget",
    "cost allocation view",
    "tenant health feed",
    "prompt quality explorer",
    "incident correlation board",
    "release readiness dashboard",
    "access governance page",
    "embedding coverage chart",
    "executive summary export",
]

OWNERS = [
    "Aarav Mehta",
    "Maya Iyer",
    "Rohan Shah",
    "Nisha Rao",
    "Kabir Singh",
    "Leena Thomas",
    "Dev Patel",
    "Priya Nair",
    "Anika Bose",
    "Vikram Kapoor",
    "Sara Fernandes",
    "Neil D'Souza",
]

TEAMS = [
    "AI Platform",
    "Dashboard Experience",
    "Enterprise SRE",
    "Data Platform",
    "Security Engineering",
    "Release Engineering",
]

ENVIRONMENTS = ["dev", "staging", "production"]

EXTERNAL_DEPENDENCIES = [
    "AUTH-782 SSO claims mapping update",
    "DATA-441 warehouse replication lag fix",
    "OBS-319 trace sampling policy rollout",
    "SEC-228 service account rotation",
    "REL-517 release pipeline approval",
    "MLP-904 model telemetry schema update",
    "NET-116 private endpoint firewall rule",
    "DBA-673 read replica capacity review",
    "None",
]

TICKET_THEMES = [
    {
        "name": "API timeout",
        "title_patterns": [
            "{component} intermittently times out through {service}",
            "{service} returns 504 during {component} refresh",
            "Slow query path blocks {component} in {environment}",
        ],
        "symptoms": [
            "p95 latency crossed the dashboard SLO for tenant-facing requests",
            "interactive filters spin for longer than 20 seconds before failing",
            "workers retry the same trace window and saturate the API pool",
        ],
        "impact": [
            "operators cannot triage model incidents from the live board",
            "executive users see incomplete cost and usage summaries",
            "SRE dashboards miss current deployment health markers",
        ],
    },
    {
        "name": "Authentication",
        "title_patterns": [
            "SSO users cannot access {component} after role sync",
            "{service} rejects valid enterprise tokens in {environment}",
            "RBAC mismatch hides {component} for support admins",
        ],
        "symptoms": [
            "OIDC group claims arrive without the expected dashboard role alias",
            "token exchange succeeds but the session bootstrap request is denied",
            "newly provisioned support users receive a stale permission snapshot",
        ],
        "impact": [
            "support teams cannot open customer-specific health dashboards",
            "release managers lose access during production verification",
            "tenant admins cannot audit model usage permissions",
        ],
    },
    {
        "name": "Data freshness",
        "title_patterns": [
            "{component} shows stale metrics from {service}",
            "Telemetry delay causes incorrect status on {component}",
            "{environment} aggregation job skips AI usage windows",
        ],
        "symptoms": [
            "hourly usage aggregates stop advancing while raw events continue",
            "late-arriving embeddings are excluded from quality scorecards",
            "project health summaries show yesterday's deployment status",
        ],
        "impact": [
            "customer success teams rely on outdated adoption metrics",
            "product owners cannot compare model performance after release",
            "incident commanders lose confidence in the operational timeline",
        ],
    },
    {
        "name": "Deployment",
        "title_patterns": [
            "{service} deployment blocked by config drift in {environment}",
            "Rollback needed after {component} release validation fails",
            "Canary promotion for {service} fails health gate",
        ],
        "symptoms": [
            "the canary pod never reaches ready state after environment injection",
            "post-deploy smoke checks fail on tenant-scoped dashboard endpoints",
            "feature flags remain enabled after the rollback job completes",
        ],
        "impact": [
            "the release train is paused for the AI Dashboard program",
            "production verification cannot complete within the maintenance window",
            "dependent analytics features remain behind a release hold",
        ],
    },
    {
        "name": "Database migration",
        "title_patterns": [
            "Migration lock detected while updating {component}",
            "{service} cannot read new AI metrics schema in {environment}",
            "Backfill job corrupts ordering for {component}",
        ],
        "symptoms": [
            "migration workers wait on an exclusive lock for the dashboard schema",
            "new nullable fields are treated as required by the reporting query",
            "backfilled rows lose the deployment timestamp used for correlation",
        ],
        "impact": [
            "reports cannot reconcile deployment outcomes with incident volume",
            "dashboard tiles fail for tenants with high event cardinality",
            "SREs cannot compare pre-release and post-release behavior",
        ],
    },
    {
        "name": "UI regression",
        "title_patterns": [
            "{component} layout breaks for enterprise workspaces",
            "{service} payload renders duplicate rows in {component}",
            "Filtering state resets when users open {component}",
        ],
        "symptoms": [
            "saved filters are dropped when a workspace has more than 30 services",
            "the table virtualization layer reuses stale row measurements",
            "export controls render before the permissions payload is available",
        ],
        "impact": [
            "platform operators cannot scan incidents across large portfolios",
            "business stakeholders export inconsistent weekly summaries",
            "tenant administrators repeat manual filtering after every refresh",
        ],
    },
]


def parse_output_dir() -> Path:
    parser = argparse.ArgumentParser(description="Generate AI Dashboard fake enterprise datasets.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where JSON files should be written.",
    )
    return parser.parse_args().output_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_tickets(count: int = 150, seed: int = 42) -> list[dict[str, str]]:
    rng = random.Random(seed)
    start_date = date(2026, 1, 6)
    priorities = ["P0", "P1", "P2", "P3", "P4"]
    statuses = ["Backlog", "In Progress", "Blocked", "In Review", "Resolved", "Closed"]
    tickets: list[dict[str, str]] = []

    for index in range(count):
        theme = TICKET_THEMES[index % len(TICKET_THEMES)]
        service = SERVICES[(index * 3) % len(SERVICES)]
        component = COMPONENTS[(index * 5) % len(COMPONENTS)]
        environment = ENVIRONMENTS[(index + index // 7) % len(ENVIRONMENTS)]
        owner = OWNERS[(index * 4 + 1) % len(OWNERS)]
        priority = priorities[min(index % 6, len(priorities) - 1)]
        status = statuses[(index * 5 + 2) % len(statuses)]
        created = start_date + timedelta(days=index % 142)
        ticket_id = f"AIDASH-{1001 + index}"

        title_template = theme["title_patterns"][index % len(theme["title_patterns"])]
        title = title_template.format(
            component=component,
            service=service,
            environment=environment,
        )

        symptom = rng.choice(theme["symptoms"])
        impact = rng.choice(theme["impact"])
        detection_source = rng.choice(
            [
                "synthetic monitor",
                "customer support escalation",
                "release verification checklist",
                "SRE anomaly detector",
                "weekly adoption review",
            ]
        )
        expected_outcome = rng.choice(
            [
                "dashboard panels should load within the enterprise SLO",
                "role-aware users should see the same project inventory across sessions",
                "deployment health should reconcile with logs and active incidents",
                "aggregated metrics should match the warehouse snapshot for the same hour",
            ]
        )

        if index > 8 and index % 4 == 0:
            dependency = f"AIDASH-{1001 + index - rng.randint(2, 8)}"
        else:
            dependency = EXTERNAL_DEPENDENCIES[(index * 2 + 3) % len(EXTERNAL_DEPENDENCIES)]

        description = (
            f"{PROJECT_NAME} issue in {environment} affecting {component}. "
            f"Observed symptom: {symptom}. Impact: {impact}. "
            f"Detected by {detection_source} while validating {service}. "
            f"Expected outcome: {expected_outcome}. "
            f"Initial triage should inspect traces, recent deployments, feature flags, "
            f"and related tickets before marking the incident resolved."
        )

        tickets.append(
            {
                "ticket_id": ticket_id,
                "title": title,
                "description": description,
                "priority": priority,
                "status": status,
                "owner": owner,
                "dependency": dependency,
                "created_date": created.isoformat(),
            }
        )

    return tickets


def build_documents(count: int = 50, seed: int = 73) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    documents: list[dict[str, Any]] = []
    document_types = [
        "architecture document",
        "meeting notes",
        "release plan",
        "deployment procedure",
        "incident report",
    ]

    for index in range(count):
        doc_type = document_types[index % len(document_types)]
        service = SERVICES[(index * 2 + 1) % len(SERVICES)]
        team = TEAMS[(index * 3) % len(TEAMS)]
        environment = ENVIRONMENTS[(index + 1) % len(ENVIRONMENTS)]
        owner = OWNERS[(index * 5) % len(OWNERS)]
        created = date(2026, 1, 10) + timedelta(days=index * 3)
        doc_id = f"DOC-AIDASH-{index + 1:03d}"

        titles = {
            "architecture document": f"{PROJECT_NAME} {service} architecture and data contracts",
            "meeting notes": f"{PROJECT_NAME} operations review notes for {service}",
            "release plan": f"{PROJECT_NAME} release plan for {service} {environment}",
            "deployment procedure": f"{PROJECT_NAME} deployment procedure for {service}",
            "incident report": f"{PROJECT_NAME} incident report for {service} degradation",
        }

        related_tickets = [
            f"AIDASH-{1001 + ((index * 3) % 150)}",
            f"AIDASH-{1001 + ((index * 3 + 17) % 150)}",
        ]

        sections = _document_sections(
            doc_type=doc_type,
            service=service,
            team=team,
            environment=environment,
            related_tickets=related_tickets,
            rng=rng,
        )

        documents.append(
            {
                "document_id": doc_id,
                "title": titles[doc_type],
                "document_type": doc_type,
                "project": PROJECT_NAME,
                "owner_team": team,
                "owner": owner,
                "service": service,
                "environment": environment,
                "version": f"v{1 + index // 10}.{index % 10}",
                "created_date": created.isoformat(),
                "related_ticket_ids": related_tickets,
                "tags": _document_tags(doc_type, service, environment),
                "sections": sections,
            }
        )

    return documents


def _document_sections(
    doc_type: str,
    service: str,
    team: str,
    environment: str,
    related_tickets: list[str],
    rng: random.Random,
) -> list[dict[str, str]]:
    if doc_type == "architecture document":
        return [
            {
                "heading": "Context",
                "body": (
                    f"{service} supports the AI Dashboard by normalizing operational telemetry, "
                    f"authorization context, and deployment metadata for enterprise tenants."
                ),
            },
            {
                "heading": "Key Interfaces",
                "body": (
                    "Primary interfaces include the tenant-scoped REST API, the metrics event stream, "
                    "the dashboard read model, and the audit event sink."
                ),
            },
            {
                "heading": "Reliability Notes",
                "body": (
                    f"{team} owns SLO review, circuit-breaker thresholds, schema compatibility, "
                    f"and rollback readiness for {environment} releases."
                ),
            },
        ]

    if doc_type == "meeting notes":
        decision = rng.choice(
            [
                "tighten canary promotion criteria before the next production rollout",
                "prioritize trace correlation for timeout and authentication incidents",
                "move dashboard freshness checks into release verification",
            ]
        )
        return [
            {
                "heading": "Discussion",
                "body": (
                    f"The operations review focused on {service}, open support escalations, "
                    f"and recurring evidence gaps across tickets {', '.join(related_tickets)}."
                ),
            },
            {
                "heading": "Decision",
                "body": f"The team agreed to {decision}.",
            },
            {
                "heading": "Action Items",
                "body": (
                    f"{team} will publish owner rotation updates, validate alert thresholds, "
                    "and confirm all deployment logs include tenant and trace identifiers."
                ),
            },
        ]

    if doc_type == "release plan":
        return [
            {
                "heading": "Scope",
                "body": (
                    f"The release updates {service} for {environment} with dashboard query tuning, "
                    "freshness indicators, and improved incident correlation metadata."
                ),
            },
            {
                "heading": "Readiness Gates",
                "body": (
                    "Required gates include migration dry run, API p95 latency check, SSO smoke test, "
                    "rollback rehearsal, and support knowledge-base validation."
                ),
            },
            {
                "heading": "Risks",
                "body": (
                    "Main risks are tenant-specific feature flags, warehouse replication lag, "
                    "and mismatched schema versions between analytics workers and dashboard APIs."
                ),
            },
        ]

    if doc_type == "deployment procedure":
        return [
            {
                "heading": "Pre-Deployment",
                "body": (
                    f"Confirm {service} image digest, database migration status, feature flag plan, "
                    "and active incident freeze exceptions before starting the deployment."
                ),
            },
            {
                "heading": "Execution",
                "body": (
                    "Deploy to canary, wait for health probes, compare dashboard synthetic checks, "
                    "promote gradually, then capture trace and audit samples."
                ),
            },
            {
                "heading": "Rollback",
                "body": (
                    "Rollback must disable new dashboard flags, restore the previous image, "
                    "and verify that deployment logs are linked to the active release ticket."
                ),
            },
        ]

    return [
        {
            "heading": "Summary",
            "body": (
                f"{service} experienced degraded behavior in {environment}. "
                f"The event was linked to tickets {', '.join(related_tickets)}."
            ),
        },
        {
            "heading": "Root Cause",
            "body": rng.choice(
                [
                    "A stale permission cache blocked valid users after an SSO group mapping change.",
                    "A migration lock delayed dashboard reads and caused downstream API timeouts.",
                    "A canary deployment used a mismatched environment variable for the telemetry stream.",
                    "Warehouse replication lag made the dashboard present stale AI usage aggregates.",
                ]
            ),
        },
        {
            "heading": "Corrective Actions",
            "body": (
                "Add synthetic coverage, enforce deployment evidence capture, update runbooks, "
                "and create follow-up backlog items for unresolved monitoring gaps."
            ),
        },
    ]


def _document_tags(doc_type: str, service: str, environment: str) -> list[str]:
    normalized_type = doc_type.replace(" ", "-")
    return [
        "ai-dashboard",
        normalized_type,
        service,
        environment,
        "enterprise-ops",
    ]


def build_deployment_logs(count: int = 50, seed: int = 91) -> list[dict[str, str]]:
    rng = random.Random(seed)
    log_types = [
        "deployment failure",
        "authentication failure",
        "database migration issue",
        "api timeout error",
    ]
    base_dt = datetime(2026, 2, 3, 9, 15, tzinfo=timezone.utc)
    logs: list[dict[str, str]] = []

    for index in range(count):
        log_type = log_types[index % len(log_types)]
        service = SERVICES[(index * 7 + 2) % len(SERVICES)]
        environment = ENVIRONMENTS[(index + 2) % len(ENVIRONMENTS)]
        deployment_id = f"DEP-AIDASH-{2026}{(index % 6) + 1:02d}-{index + 1:03d}"
        timestamp = base_dt + timedelta(days=index * 2, minutes=index * 11)
        related_ticket_id = f"AIDASH-{1001 + ((index * 5 + 9) % 150)}"
        trace_id = f"trace-{rng.randrange(16**12):012x}"

        details = _log_details(log_type, service, environment, rng)

        logs.append(
            {
                "log_id": f"LOG-AIDASH-{index + 1:04d}",
                "log_type": log_type,
                "deployment_id": deployment_id,
                "project": PROJECT_NAME,
                "service": service,
                "environment": environment,
                "severity": details["severity"],
                "status": details["status"],
                "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                "error_code": details["error_code"],
                "message": details["message"],
                "trace_id": trace_id,
                "related_ticket_id": related_ticket_id,
                "probable_cause": details["probable_cause"],
                "remediation_hint": details["remediation_hint"],
            }
        )

    return logs


def _log_details(log_type: str, service: str, environment: str, rng: random.Random) -> dict[str, str]:
    if log_type == "deployment failure":
        reason = rng.choice(
            [
                "readiness probe failed after config injection",
                "canary health score stayed below promotion threshold",
                "container image digest did not match approved release manifest",
            ]
        )
        return {
            "severity": "ERROR",
            "status": "failed",
            "error_code": "DEPLOY_HEALTH_GATE_FAILED",
            "message": (
                f"{service} deployment to {environment} failed because {reason}; "
                "release controller halted promotion and requested rollback evidence."
            ),
            "probable_cause": "Release manifest, feature flag, or environment configuration drift.",
            "remediation_hint": "Compare release manifest with deployed config, rollback canary, and rerun smoke checks.",
        }

    if log_type == "authentication failure":
        reason = rng.choice(
            [
                "OIDC group claim was missing dashboard-admin mapping",
                "service token audience did not match the API gateway policy",
                "permission cache returned an expired enterprise role snapshot",
            ]
        )
        return {
            "severity": "WARN",
            "status": "degraded",
            "error_code": "AUTHZ_POLICY_DENIED",
            "message": (
                f"{service} rejected authenticated dashboard traffic in {environment}; {reason}."
            ),
            "probable_cause": "SSO mapping, token audience, or cached authorization policy mismatch.",
            "remediation_hint": "Refresh role cache, inspect IdP claim mapping, and verify service account audience.",
        }

    if log_type == "database migration issue":
        reason = rng.choice(
            [
                "migration waited on dashboard_metrics exclusive lock",
                "new nullable column was read as required by analytics worker",
                "backfill skipped tenant partition with high event volume",
            ]
        )
        return {
            "severity": "ERROR",
            "status": "failed",
            "error_code": "DB_MIGRATION_BLOCKED",
            "message": (
                f"{service} migration in {environment} did not complete; {reason}."
            ),
            "probable_cause": "Schema version skew or lock contention during dashboard data migration.",
            "remediation_hint": "Pause rollout, release blocking transactions, run migration dry-run, and validate schema readers.",
        }

    reason = rng.choice(
        [
            "upstream metrics query exceeded the 15 second gateway deadline",
            "tenant filter expansion generated a high-cardinality warehouse query",
            "retry storm saturated the dashboard API connection pool",
        ]
    )
    return {
        "severity": "ERROR",
        "status": "degraded",
        "error_code": "API_GATEWAY_TIMEOUT",
        "message": (
            f"{service} returned timeout responses in {environment}; {reason}."
        ),
        "probable_cause": "Slow upstream query, excessive retries, or insufficient API worker capacity.",
        "remediation_hint": "Inspect p95 traces, reduce retry concurrency, and apply query or cache mitigation.",
    }


def tickets_payload(tickets: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "dataset": "ai_dashboard_jira_style_tickets",
        "project": PROJECT_NAME,
        "generated_at": GENERATED_AT,
        "record_count": len(tickets),
        "schema": {
            "ticket_id": "string",
            "title": "string",
            "description": "string",
            "priority": "P0 | P1 | P2 | P3 | P4",
            "status": "Backlog | In Progress | Blocked | In Review | Resolved | Closed",
            "owner": "string",
            "dependency": "string",
            "created_date": "YYYY-MM-DD",
        },
        "tickets": tickets,
    }


def documents_payload(documents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dataset": "ai_dashboard_project_documents",
        "project": PROJECT_NAME,
        "generated_at": GENERATED_AT,
        "record_count": len(documents),
        "document_types": [
            "architecture document",
            "meeting notes",
            "release plan",
            "deployment procedure",
            "incident report",
        ],
        "documents": documents,
    }


def logs_payload(logs: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "dataset": "ai_dashboard_deployment_logs",
        "project": PROJECT_NAME,
        "generated_at": GENERATED_AT,
        "record_count": len(logs),
        "log_types": [
            "deployment failure",
            "authentication failure",
            "database migration issue",
            "api timeout error",
        ],
        "logs": logs,
    }


def write_tickets(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = output_dir / "tickets.json"
    write_json(path, tickets_payload(build_tickets()))
    return path


def write_documents(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = output_dir / "project_documents.json"
    write_json(path, documents_payload(build_documents()))
    return path


def write_deployment_logs(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = output_dir / "deployment_logs.json"
    write_json(path, logs_payload(build_deployment_logs()))
    return path


def write_all(output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    return [
        write_tickets(output_dir),
        write_documents(output_dir),
        write_deployment_logs(output_dir),
    ]


def print_written(paths: list[Path]) -> None:
    for path in paths:
        print(f"wrote {path}")
