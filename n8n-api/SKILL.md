---
name: n8n-api
description: Manage and inspect Shrubnet's n8n automation server via the n8n Public API. Use when the user asks about n8n workflows, executions, credentials metadata, tags, users, webhook automation, debugging workflow runs, activating/deactivating workflows, creating/updating workflows, or checking the n8n server at n8n.cluster.shrubnet.com. Stores API credentials in the skill folder .env, never in SKILL.md.
---

# n8n API Skill

Interact with Shrubnet n8n at `https://n8n.cluster.shrubnet.com` using the n8n Public API.

## Configuration

Load credentials from this skill directory:

- `.env` — real local credentials; do not print, paste, or commit.
- `.env.example` — safe template.

Expected variables:

```bash
N8N_BASE_URL=https://n8n.cluster.shrubnet.com
N8N_API_KEY=...
```

Authentication header:

```text
X-N8N-API-KEY: $N8N_API_KEY
```

## Preferred helper

Use `scripts/n8n_api.py` for common operations. It automatically loads `.env` and avoids echoing the token.

Examples:

```bash
skills/n8n-api/scripts/n8n_api.py workflows --limit 20
skills/n8n-api/scripts/n8n_api.py workflow <workflow-id>
skills/n8n-api/scripts/n8n_api.py executions --limit 20 --workflow-id <workflow-id>
skills/n8n-api/scripts/n8n_api.py execution <execution-id> --include-data
skills/n8n-api/scripts/n8n_api.py raw GET /api/v1/tags
```

Use direct `curl` only when the helper does not cover the endpoint. If using `curl`, source `.env` without printing it.

## Safety rules

- Treat workflow definitions, execution payloads, and credential metadata as sensitive.
- Use read-only endpoints first when investigating.
- Confirm with the user before destructive or external-impact changes:
  - activating/deactivating production workflows
  - creating/updating/deleting workflows
  - deleting executions
  - creating/updating/deleting credentials
  - triggering workflows that send email, Slack, HTTP calls, billing actions, or other external side effects
- Never expose `N8N_API_KEY` in chat, logs, committed files, screenshots, or command output.
- Do not inspect `includeData=true` execution payloads unless needed; execution data can contain secrets or private user data.

## Common workflows

### Check API access

```bash
skills/n8n-api/scripts/n8n_api.py workflows --limit 1
```

Success means the API key and host are valid.

### Inventory workflows

```bash
skills/n8n-api/scripts/n8n_api.py workflows --limit 100
```

If `nextCursor` is returned, repeat with `--cursor <value>`.

### Inspect one workflow

```bash
skills/n8n-api/scripts/n8n_api.py workflow <workflow-id>
```

Look for:

- `name`
- `active`
- `nodes`
- `connections`
- trigger nodes
- external side-effect nodes such as Email, Slack, HTTP Request, database, CRM, or file operations

### Debug recent runs

```bash
skills/n8n-api/scripts/n8n_api.py executions --limit 20 --workflow-id <workflow-id>
skills/n8n-api/scripts/n8n_api.py execution <execution-id> --include-data
```

Use `includeData=true` only when the summary is insufficient.

### Create or update workflows

1. Fetch the current workflow JSON first when updating.
2. Save a local backup in `/tmp` before mutation.
3. Validate JSON shape: workflow `name`, `nodes`, `connections`, and `settings`.
4. Confirm with the user if the workflow can affect external systems.
5. Use `raw` helper or direct API for the write.
6. Re-fetch and compare the resulting workflow.

### Activate/deactivate workflows

Confirm first unless the user explicitly asked for that exact action.

```bash
skills/n8n-api/scripts/n8n_api.py raw POST /api/v1/workflows/<workflow-id>/activate
skills/n8n-api/scripts/n8n_api.py raw POST /api/v1/workflows/<workflow-id>/deactivate
```

## Reference

Read `references/api-notes.md` when you need endpoint details beyond the common helper commands.
