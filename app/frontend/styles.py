from __future__ import annotations


CSS = """
<style>
:root {
  --ops-bg: #f6f8fb;
  --ops-panel: #ffffff;
  --ops-border: #d8dee8;
  --ops-text: #182230;
  --ops-muted: #667085;
  --ops-accent: #116466;
  --ops-accent-2: #2c6bed;
  --ops-warn: #b54708;
  --ops-danger: #b42318;
  --ops-success: #027a48;
}

.block-container {
  padding-top: 1.5rem;
  padding-bottom: 2rem;
  max-width: 1480px;
}

div[data-testid="stSidebar"] {
  background: #101828;
}

div[data-testid="stSidebar"] * {
  color: #f8fafc;
}

.ops-header {
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  padding: 18px 20px;
  background: var(--ops-panel);
  margin-bottom: 16px;
}

.ops-header h1 {
  color: var(--ops-text);
  font-size: 28px;
  line-height: 1.2;
  margin: 0 0 4px 0;
  letter-spacing: 0;
}

.ops-header p {
  color: var(--ops-muted);
  margin: 0;
  font-size: 14px;
}

.ops-card {
  border: 1px solid var(--ops-border);
  border-radius: 8px;
  padding: 14px 16px;
  background: var(--ops-panel);
  min-height: 86px;
}

.ops-card-label {
  color: var(--ops-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0;
  margin-bottom: 8px;
}

.ops-card-value {
  color: var(--ops-text);
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
}

.ops-pill {
  display: inline-block;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid var(--ops-border);
  background: #f8fafc;
  color: var(--ops-text);
}

.ops-pill.success { color: var(--ops-success); background: #ecfdf3; border-color: #abefc6; }
.ops-pill.partial { color: var(--ops-warn); background: #fffaeb; border-color: #fedf89; }
.ops-pill.failed { color: var(--ops-danger); background: #fef3f2; border-color: #fecdca; }
.ops-pill.skipped { color: #475467; background: #f2f4f7; border-color: #d0d5dd; }
.ops-pill.info { color: var(--ops-accent-2); background: #eff4ff; border-color: #b2ccff; }

.ops-evidence {
  border-left: 3px solid var(--ops-accent);
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 0 8px 8px 0;
  margin-bottom: 8px;
}

.ops-evidence-title {
  font-weight: 700;
  color: var(--ops-text);
  margin-bottom: 4px;
}

.ops-muted {
  color: var(--ops-muted);
}

.ops-section-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--ops-text);
  margin: 8px 0 10px 0;
}
</style>
"""

