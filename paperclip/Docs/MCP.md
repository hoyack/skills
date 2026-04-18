# Paperclip MCP Server

Model Context Protocol (MCP) server for Paperclip AI, enabling MCP-compatible clients (Claude, Cursor, etc.) to interact with Paperclip through natural language.

## Overview

The Paperclip MCP server exposes Paperclip's REST API as MCP tools, allowing AI assistants to:
- Manage issues and tasks
- Control agents
- Monitor costs and activity
- Handle approvals
- View dashboards

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│  Paperclip MCP   │────▶│  Paperclip API  │
│ (Claude/Cursor) │     │     Server       │     │   :3100/api     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- Running Paperclip instance
- Paperclip company ID

### Install MCP Server

```bash
cd ~/Documents/skills/paperclip/mcp-server
pip install -e .
```

### Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```dotenv
PAPERCLIP_BASE_URL=http://192.168.1.68:3100/api
PAPERCLIP_API_KEY=your_api_key_or_session
PAPERCLIP_COMPANY_ID=61a140bd-2ec1-4369-8329-3e31636ab3c2
```

**Note:** The MCP server uses session-based authentication. You'll need to either:
1. Generate a board API key in Paperclip UI → Settings → API Keys
2. Or modify the server to use cookie-based auth

### Get Company ID

```bash
# Login and get company ID
curl -X POST http://192.168.1.68:3100/api/auth/sign-in/email \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'

# Then fetch companies
curl http://192.168.1.68:3100/api/companies \
  -b "better-auth.session_token=your-token"
```

## MCP Configuration

### Add to ~/.mcp.json

```json
{
  "mcpServers": {
    "paperclip": {
      "command": "python",
      "args": ["/home/hoyack/Documents/skills/paperclip/mcp-server/src/paperclip_mcp/server.py"],
      "env": {
        "PAPERCLIP_BASE_URL": "http://192.168.1.68:3100/api",
        "PAPERCLIP_COMPANY_ID": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
        "PAPERCLIP_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Alternative: Using npx (if published)

```json
{
  "mcpServers": {
    "paperclip": {
      "command": "npx",
      "args": ["-y", "paperclip-mcp"],
      "env": {
        "PAPERCLIP_BASE_URL": "http://192.168.1.68:3100/api",
        "PAPERCLIP_COMPANY_ID": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
        "PAPERCLIP_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### Issues

| Tool | Description |
|------|-------------|
| `list_issues` | List all issues in company |
| `get_issue` | Get issue by ID |
| `create_issue` | Create new issue |
| `update_issue` | Update issue status/priority |
| `checkout_issue` | Checkout issue for work |
| `release_issue` | Release issue checkout |
| `comment_on_issue` | Add comment to issue |
| `delete_issue` | Delete an issue |

### Agents

| Tool | Description |
|------|-------------|
| `list_agents` | List all agents |
| `get_agent` | Get agent details |
| `invoke_agent_heartbeat` | Trigger agent heartbeat |

### Goals

| Tool | Description |
|------|-------------|
| `list_goals` | List company goals |
| `create_goal` | Create new goal |
| `update_goal` | Update goal |

### Approvals

| Tool | Description |
|------|-------------|
| `list_approvals` | List pending approvals |
| `approve` | Approve a request |
| `reject` | Reject a request |
| `request_approval_revision` | Request changes |

### Monitoring

| Tool | Description |
|------|-------------|
| `get_cost_summary` | Get cost breakdown |
| `get_dashboard` | Get dashboard summary |
| `list_activity` | List recent activity |

## Usage Examples

### Example 1: Create an Issue

```
User: Create a high priority issue titled "Fix authentication bug" in Paperclip

AI: I'll create that issue for you.

[Uses mcp__paperclip__create_issue]

Done! Created issue SER-12: "Fix authentication bug" with high priority.
```

### Example 2: List Agents

```
User: What agents do I have in Paperclip?

AI: Let me check your agents.

[Uses mcp__paperclip__list_agents]

You have 2 agents:
1. CEO (codex_local) - Status: idle
2. Clawdius (openclaw_gateway) - Status: idle
```

### Example 3: Get Dashboard

```
User: Show me the Paperclip dashboard

AI: Here's your dashboard summary:

[Uses mcp__paperclip__get_dashboard]

- Company: Service Orchard
- Active Issues: 11
- Completed Today: 3
- Agents Online: 2
- Monthly Spend: $0.00
```

## Testing the MCP Server

### Manual Test

```bash
# Start the server
python ~/Documents/skills/paperclip/mcp-server/src/paperclip_mcp/server.py

# In another terminal, test with mcp-cli or similar
```

### Test with Claude

1. Add MCP config to Claude settings
2. Restart Claude
3. Ask: "List my Paperclip issues"

## Troubleshooting

### "Connection refused" Error

**Cause:** Paperclip API not accessible

**Fix:** Check Paperclip is running:
```bash
curl http://192.168.1.68:3100/api/health
```

### "Unauthorized" Error

**Cause:** Invalid or missing API key

**Fix:** 
1. Generate API key in Paperclip UI → Settings → API Keys
2. Update `.env` file
3. Restart MCP server

### "Company not found" Error

**Cause:** Wrong company ID

**Fix:** Verify company ID:
```bash
curl http://192.168.1.68:3100/api/companies -b "$COOKIE"
```

## Development

### Project Structure

```
mcp-server/
├── src/
│   └── paperclip_mcp/
│       ├── __init__.py
│       ├── server.py          # Main MCP server
│       └── client.py          # Paperclip API client
├── .env.example
├── pyproject.toml
└── README.md
```

### Adding New Tools

Edit `src/paperclip_mcp/server.py`:

```python
@mcp.tool()
async def my_new_tool(param: str) -> dict:
    """Description of what this tool does"""
    result = await paperclip_client.my_new_endpoint(param)
    return result
```

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Paperclip API Reference](./API.md)
- [Original MCP Server Repo](https://github.com/wizarck/paperclip-mcp)
