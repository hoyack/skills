# Paperclip AI Skill

Complete skill package for Paperclip AI autonomous agent platform.

## What's Included

```
paperclip/
├── SETUP.md                 # Complete setup and configuration guide
├── SKILL.md                 # Quick reference for using Paperclip
├── README.md                # This file
├── docker-compose.yml       # Docker deployment configuration
├── .env                     # Environment variables
├── .env.example             # Environment template
├── Docs/
│   ├── API.md              # Complete REST API documentation
│   └── MCP.md              # MCP server documentation
└── mcp-server/             # Paperclip MCP server (cloned from wizarck/paperclip-mcp)
    ├── src/
    │   └── paperclip_mcp/
    │       └── server.py   # MCP server implementation
    ├── .env                # MCP server configuration
    └── README.md           # MCP server readme
```

## Quick Start

### 1. Deploy Paperclip

```bash
cd ~/Documents/skills/paperclip
docker compose up -d
```

### 2. Complete Setup

Follow the detailed steps in [SETUP.md](./SETUP.md):
1. Generate bootstrap invite
2. Create admin account
3. Accept bootstrap invite
4. Configure Codex OAuth

### 3. Access Paperclip

- **Web UI**: http://192.168.1.68:3100
- **API**: http://192.168.1.68:3100/api

## Configuration Highlights

### Critical Settings for HTTP Deployment

```yaml
environment:
  # Required for cookie auth to work over HTTP
  - BETTER_AUTH_TRUSTED_ORIGINS=http://192.168.1.68:3100,http://localhost:3100
  
  # Required for Codex auth to persist
  - CODEX_HOME=/home/node/.codex
  - HOME=/home/node
```

### Codex OAuth Setup

```bash
# Authenticate Codex inside container
docker exec paperclip codex login --device-auth

# Complete flow in browser, then fix permissions
docker exec paperclip chown -R node:node /home/node/.codex
```

## MCP Server Integration

The skill includes an MCP server for Paperclip, allowing MCP-compatible clients (Claude, Cursor, etc.) to interact with Paperclip.

### MCP Tools Available

| Category | Tools |
|----------|-------|
| **Issues** | `list_issues`, `get_issue`, `create_issue`, `update_issue`, `checkout_issue`, `release_issue`, `comment_on_issue`, `delete_issue` |
| **Agents** | `list_agents`, `get_agent`, `invoke_agent_heartbeat` |
| **Goals** | `list_goals`, `create_goal`, `update_goal` |
| **Approvals** | `list_approvals`, `approve`, `reject` |
| **Monitoring** | `get_cost_summary`, `get_dashboard`, `list_activity` |

### Configure MCP

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "paperclip": {
      "command": "python",
      "args": ["/home/hoyack/Documents/skills/paperclip/mcp-server/src/paperclip_mcp/server.py"],
      "env": {
        "PAPERCLIP_BASE_URL": "http://192.168.1.68:3100/api",
        "PAPERCLIP_COMPANY_ID": "your-company-id",
        "PAPERCLIP_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](./SETUP.md) | Complete deployment and configuration guide |
| [SKILL.md](./SKILL.md) | Quick reference for using Paperclip |
| [Docs/API.md](./Docs/API.md) | Complete REST API reference |
| [Docs/MCP.md](./Docs/MCP.md) | MCP server documentation |

## Key Features

- ✅ **Autonomous AI Agents** - Create and manage AI agents
- ✅ **Project Management** - Issues, goals, and projects
- ✅ **Codex Integration** - Code editing with GPT/Codex
- ✅ **OpenClaw Gateway** - Enhanced agent capabilities
- ✅ **REST API** - Full programmatic access
- ✅ **MCP Server** - Natural language interaction
- ✅ **Persistent Auth** - Codex OAuth survives restarts

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login page reloads | Check `BETTER_AUTH_TRUSTED_ORIGINS` env var |
| Codex test fails | Fix permissions: `docker exec paperclip chown -R node:node /home/node/.codex` |
| 401 Unauthorized | Session expired, re-login |
| Bootstrap fails | Ensure config.json has `deploymentMode: "authenticated"` |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Paperclip AI                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │    Web UI    │  │   REST API   │  │        Codex CLI         │   │
│  │   :3100      │  │   /api/*     │  │    (inside container)    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Embedded PostgreSQL Database                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     OpenClaw Gateway :18789                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     MCP Server (Optional)                            │
│            Exposes Paperclip API as MCP tools                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Support

- [Paperclip GitHub](https://github.com/paperclipai/paperclip)
- [MCP Server Source](https://github.com/wizarck/paperclip-mcp)
- [MCP Documentation](https://modelcontextprotocol.io)
