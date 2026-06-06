# AI Dashboard Fake Enterprise Seed Data

This directory contains deterministic synthetic data for Phase 1 of the Enterprise AI Operations Assistant.

Generated files:

- `tickets.json`: 150 Jira-style AI Dashboard tickets
- `project_documents.json`: 50 project documents across architecture, meeting notes, release plans, deployment procedures, and incident reports
- `deployment_logs.json`: 50 deployment logs across deployment failures, authentication failures, database migration issues, and API timeout errors

Regenerate all datasets:

```powershell
python scripts\generate_all_datasets.py
```

Validate counts and required categories:

```powershell
python scripts\validate_seed_data.py
```
