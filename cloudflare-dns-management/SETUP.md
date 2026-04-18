# Cloudflare DNS API Setup

One-time credential provisioning. After this, the skill can manage any zone that your token has `Zone:DNS:Edit` permission for.

## Prerequisites

- A Cloudflare account with at least one zone (domain) added
- The zone's registrar nameservers must point to the two Cloudflare nameservers shown in the dashboard (e.g., `*.ns.cloudflare.com`) — otherwise API calls succeed but records won't resolve publicly

## 1. Generate an API Token

1. Log in at https://dash.cloudflare.com
2. Right-side user icon → **My Profile** → **API Tokens**
3. **Create Token**
4. Either use the built-in **Edit zone DNS** template, or create a custom token with:
   - **Permissions:** `Zone > DNS > Edit`, `Zone > Zone > Read`
   - **Zone Resources:** either `All zones` (broad, convenient) or `Include > Specific zone > <your zone>` (scoped, safer)
   - **Client IP Address Filtering:** leave empty unless you have a static IP
   - **TTL:** optional expiration
5. **Continue to summary** → **Create Token**
6. Copy the token **immediately** — it's shown once and cannot be retrieved later

The token looks like: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t`

## 2. Store the Credentials

### Option A — per-skill `.env` (recommended; matches other skills in this repo)

Copy the template and fill it in:

```bash
cd /home/hoyack/Documents/skills/cloudflare-dns-management
cp .env.example .env
$EDITOR .env
chmod 600 .env
```

`.env` is gitignored by the root `.gitignore`.

Load into the current shell before running curl commands:

```bash
set -a; source /home/hoyack/Documents/skills/cloudflare-dns-management/.env; set +a
```

### Option B — shell profile

Append to `~/.bashrc` or `~/.zshrc`:

```bash
export CLOUDFLARE_API_TOKEN="<your-token>"
```

## 3. Verify the Token

```bash
# Token self-check (doesn't need any scopes other than the token itself)
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  https://api.cloudflare.com/client/v4/user/tokens/verify \
  | python3 -m json.tool
```

Expected: `"status": "active"` and `"success": true`.

## 4. Sanity-Check Zone Access

```bash
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  https://api.cloudflare.com/client/v4/zones \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"zones={len(d['result'])}:\"); [print(f\"  {z['name']:30} id={z['id']}  status={z['status']}  ns={','.join(z['name_servers'])}\") for z in d['result']]"
```

Expect one line per zone the token can access. If empty, the token was scoped to specific zones and none match, or no zones exist yet.

## 5. Register the MCP Server

### Remote MCP (recommended)

Cloudflare hosts the MCP server — no local install required. Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "cloudflare": {
      "url": "https://mcp.cloudflare.com/mcp",
      "headers": {
        "Authorization": "Bearer <paste-token-here>"
      }
    }
  }
}
```

Restart Claude Code. The MCP exposes just two tools — `search` and `execute` — that between them cover Cloudflare's full 2,500+ endpoint API. The agent writes JavaScript in a sandbox to filter the OpenAPI spec and issue requests.

### Local MCP via `mcp-remote` (alternative)

If you want the MCP traffic to go through your local host instead of hitting Cloudflare's endpoint directly:

```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.cloudflare.com/sse"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "<paste-token-here>"
      }
    }
  }
}
```

## 6. Verify MCP Registration

After restart, `mcp__cloudflare__*` tools should appear. The two you'll use:

- `search` — search the Cloudflare OpenAPI spec
- `execute` — execute an API call

Ask the agent to list your Cloudflare zones to confirm end-to-end.

## Security Notes

- Treat the token like a password — `Zone:DNS:Edit` is enough to hijack any domain the token covers
- Prefer **zone-scoped** tokens over **all-zones** tokens when feasible
- Rotate periodically; revoke at https://dash.cloudflare.com/profile/api-tokens
- Do NOT commit `~/.mcp.json` or `.env` containing the token
- If the token is ever exposed in conversation history, revoke immediately — the token self-check lets an attacker confirm validity before using it
