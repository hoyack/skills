---
name: paperclip
version: 1.0.0
description: >
  Paperclip AI autonomous agent platform for orchestrating AI agents, managing projects,
  and automating software engineering tasks. Integrates with Codex CLI for code editing
  and OpenClaw gateway for agent operations. Provides REST API and optional MCP server
  for programmatic access.
tags: [paperclip, ai-agent, autonomous, codex, openclaw, automation, project-management, mcp]
metadata:
  clawdbot:
    emoji: 📎
    requires:
      bins: []
env:
  PAPERCLIP_BASE_URL:
    description: URL of the Paperclip instance
    required: true
    default: http://192.168.1.68:3100
  PAPERCLIP_EMAIL:
    description: Email for Paperclip authentication
    required: true
  PAPERCLIP_PASSWORD:
    description: Password for Paperclip authentication
    required: true
---

# Paperclip AI Skill

Paperclip AI is an autonomous AI agent platform for orchestrating AI agents, managing projects, and automating software engineering tasks.

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Web UI | http://192.168.1.68:3100 | Main dashboard and agent management |
| API | http://192.168.1.68:3100/api | REST API for programmatic access |
| Health | http://192.168.1.68:3100/api/health | Health check endpoint |

## Authentication

Paperclip uses cookie-based authentication with Better Auth.

### Login via API

```bash
# Get session cookie
COOKIE=$(curl -X POST http://192.168.1.68:3100/api/auth/sign-in/email \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  -v 2>&1 | grep -i "set-cookie" | grep "better-auth" | sed 's/< set-cookie: //' | cut -d';' -f1)

# Use for subsequent requests
curl -s http://192.168.1.68:3100/api/companies -b "$COOKIE"
```

## Core Concepts

### Companies
Organizations that contain projects, agents, and issues. Each company has:
- **ID:** UUID identifier
- **Name:** Display name
- **Issue Prefix:** For ticket numbering (e.g., "SER" → SER-1, SER-2)
- **Agents:** AI agents assigned to the company

### Agents
AI agents that can execute tasks. Each agent has:
- **Role:** CEO, general, specialist
- **Adapter:** How the agent executes (codex_local, openclaw_gateway)
- **Status:** idle, running, paused
- **Capabilities:** What the agent can do

### Projects
Work containers with:
- **Goals:** High-level objectives
- **Issues:** Tasks and work items
- **Workspaces:** Code repositories and files

### Issues
Work items with:
- **Identifier:** SER-1, SER-2, etc.
- **Status:** todo, in_progress, done
- **Priority:** low, medium, high
- **Assignee:** Agent or user responsible

## Common Operations

### Create an Issue

```bash
curl -X POST "http://192.168.1.68:3100/api/companies/$COMPANY_ID/issues" \
  -b "$COOKIE" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.68:3100" \
  -d '{
    "title": "Implement feature X",
    "description": "Detailed description of the feature",
    "priority": "high",
    "status": "todo"
  }'
```

### List All Issues

```bash
curl -s "http://192.168.1.68:3100/api/companies/$COMPANY_ID/issues" \
  -b "$COOKIE" | jq '.[].identifier'
```

### Get Issue Details

```bash
curl -s "http://192.168.1.68:3100/api/companies/$COMPANY_ID/issues/$ISSUE_ID" \
  -b "$COOKIE" | jq '.'
```

### Update Issue Status

```bash
curl -X PATCH "http://192.168.1.68:3100/api/companies/$COMPANY_ID/issues/$ISSUE_ID" \
  -b "$COOKIE" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.68:3100" \
  -d '{"status": "done"}'
```

### List Agents

```bash
curl -s "http://192.168.1.68:3100/api/companies/$COMPANY_ID/agents" \
  -b "$COOKIE" | jq '.[] | {name, role, status, adapterType}'
```

### Create an Agent

```bash
curl -X POST "http://192.168.1.68:3100/api/companies/$COMPANY_ID/agents" \
  -b "$COOKIE" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.68:3100" \
  -d '{
    "name": "Developer Agent",
    "role": "general",
    "adapterType": "codex_local",
    "capabilities": "Full-stack development"
  }'
```

## Using Codex CLI

Codex CLI is authenticated and available inside the container:

```bash
# Check auth status
docker exec paperclip codex login status

# Run Codex command
docker exec -it paperclip codex "Your prompt here"

# Interactive mode
docker exec -it paperclip bash
codex
```

## Integration with OpenClaw

Paperclip agents can use OpenClaw gateway for enhanced capabilities:

1. Configure agent with adapter type `openclaw_gateway`
2. Set gateway URL: `ws://192.168.1.68:18789/`
3. Agent can now use OpenClaw tools (browser, file system, etc.)

## MCP Server (Optional)

If the MCP server is configured, you can use these tools:

| Tool | Purpose |
|------|---------|
| `mcp__paperclip__list_companies` | List all companies |
| `mcp__paperclip__get_company` | Get company details |
| `mcp__paperclip__list_issues` | List issues in a company |
| `mcp__paperclip__create_issue` | Create a new issue |
| `mcp__paperclip__update_issue` | Update issue status/fields |
| `mcp__paperclip__list_agents` | List company agents |
| `mcp__paperclip__create_agent` | Create a new agent |
| `mcp__paperclip__get_activity` | Get activity log |

See [MCP Documentation](./Docs/MCP.md) for setup instructions.

## Workflow Examples

### Create and Assign Work

```bash
# 1. Create issue
ISSUE=$(curl -X POST "http://192.168.1.68:3100/api/companies/$COMPANY_ID/issues" \
  -b "$COOKIE" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.68:3100" \
  -d '{
    "title": "Refactor authentication module",
    "description": "Move auth logic to separate service",
    "priority": "high"
  }' | jq -r '.id')

# 2. Assign to agent
curl -X PATCH "http://192.168.1.68:3100/api/companies/$COMPANY_ID/issues/$ISSUE" \
  -b "$COOKIE" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.68:3100" \
  -d "{\"assigneeAgentId\": \"$AGENT_ID\"}"
```

### Monitor Agent Activity

```bash
# Get recent activity
curl -s "http://192.168.1.68:3100/api/companies/$COMPANY_ID/activity" \
  -b "$COOKIE" | jq '.[:5] | .[].details'
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Login page reloads | Check BETTER_AUTH_TRUSTED_ORIGINS env var |
| Codex auth fails | Fix permissions: `docker exec paperclip chown -R node:node /home/node/.codex` |
| 401 Unauthorized | Cookie expired, re-login |
| 403 Forbidden | Add Origin header to requests |
| API route not found | Check URL path |

## Resources

- [Setup Guide](./SETUP.md) - Full deployment and configuration
- [API Reference](./Docs/API.md) - Complete API documentation
- [MCP Server](./Docs/MCP.md) - MCP server documentation
