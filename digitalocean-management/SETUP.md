# DigitalOcean MCP Setup

One-time setup to make the DigitalOcean MCP server available to Claude Code / OpenClaw. After this, the `digitalocean-management` skill can drive all covered services end-to-end.

## Prerequisites

- **Node.js ≥ 18** on the host running the MCP server (`node -v` to check)
- **DigitalOcean account** with API token access
- **SSH key** (recommended) added to the DigitalOcean account for Droplet provisioning

## 1. Create a DigitalOcean Personal Access Token

1. Log in at https://cloud.digitalocean.com
2. Left sidebar → **API** → **Tokens**
3. Click **Generate New Token**
4. Name: `claude-code-mcp` (or similar)
5. Expiration: pick per policy; 90 days is reasonable for rotating setups, no-expiry OK for local dev
6. **Scopes:** Grant per-service scopes matching what you expect to need. For the full skill, select:
   - `read` and `write` on: `apps`, `droplet`, `database`, `domain`, `ssh_key`, `image`, `load_balancer`, `firewall`, `vpc`, `floating_ip`, `cdn`, `spaces`, `spaces_key`, `kubernetes`, `container_registry`, `monitoring`, `uptime`, `account`, `billing`
   - For a narrower setup (e.g., App Platform only), you can select fewer
7. Click **Generate Token** and **copy immediately** — the value is shown once

## 2. Store the Credentials

### Option A — per-skill `.env` (recommended; matches other skills in this repo)

Copy the template and fill it in:

```bash
cd /home/hoyack/Documents/skills/digitalocean-management
cp .env.example .env
$EDITOR .env
chmod 600 .env
```

`.env` is already gitignored by the root `.gitignore`.

For ad-hoc curl testing from a shell:

```bash
set -a; source /home/hoyack/Documents/skills/digitalocean-management/.env; set +a
curl -s -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  https://api.digitalocean.com/v2/account | python3 -m json.tool
```

### Option B — shell profile

Append to `~/.bashrc` or `~/.zshrc`:

```bash
export DIGITALOCEAN_API_TOKEN="<your-token>"
```

Then `source ~/.bashrc`.

## 3. Register the MCP Server

Add to `~/.mcp.json` (merge with existing `mcpServers` — do not overwrite):

```json
{
  "mcpServers": {
    "digitalocean": {
      "command": "npx",
      "args": ["-y", "@digitalocean/mcp", "--services", "apps,droplets,databases,networking"],
      "env": {
        "DIGITALOCEAN_API_TOKEN": "<paste-token-here>"
      }
    }
  }
}
```

**Service scoping:** the `--services` flag controls which tool surface the MCP exposes. Start with only what you need; add more services later by editing the config and restarting Claude Code. Enabling all 9 services floods the tool catalog and degrades tool-selection accuracy.

Suggested starting scopes by intent:

| Goal | `--services` value |
|---|---|
| Deploy a web app from GitHub | `apps` |
| Deploy app + managed Postgres | `apps,databases` |
| Provision raw VPS | `droplets,networking,accounts` |
| Full infrastructure scope | `apps,droplets,databases,networking,spaces,accounts,insights` |

**Watch out for the npx-bin gotcha we hit with Netlify:** if `npx -y @digitalocean/mcp` silently fails (exits 1 with no stderr), the package's `bin` name doesn't match its package name. Workaround: `npm install -g @digitalocean/mcp` and use the global binary name in the `command` field. See `netlify-landing-page-deploy/SETUP.md` for the same pattern.

Then restart Claude Code.

## 4. Verify

After restart, the agent should have access to tools prefixed `mcp__digitalocean__*`. Quick sanity checks:

- Ask the agent to list apps or droplets
- Or exercise the remote endpoint directly to confirm the PAT works:
  ```bash
  curl -s -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
    https://api.digitalocean.com/v2/account | python3 -m json.tool | head -15
  ```
  Expect to see the account's `uuid`, `email`, `status` etc.

If tools are missing:

- Check `node -v` ≥ 18 on the host
- Run `npx -y @digitalocean/mcp --services apps` manually and confirm it starts without error (it will wait on stdio — that's normal for MCP servers)
- Confirm the PAT is valid with the curl above
- Check `~/.mcp.json` is valid JSON and has no trailing commas
- Check the MCP log at `~/.cache/claude-cli-nodejs/<project>/mcp-logs-digitalocean/` for the latest `.jsonl`

## 5. SSH Key Setup (for Droplet provisioning)

If you plan to create Droplets, upload at least one SSH key first so you can access the Droplet after it boots:

```bash
# If you don't have a key yet:
ssh-keygen -t ed25519 -C "your-email@example.com"

# Register it with DO:
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"claude-code\",\"public_key\":\"$(cat ~/.ssh/id_ed25519.pub)\"}" \
  https://api.digitalocean.com/v2/account/keys
```

The returned `fingerprint` can be passed to `droplet-create` so the Droplet accepts your key on first boot.

## 6. GitHub Integration (for App Platform)

App Platform deploys from GitHub via a GitHub app. First-time setup:

1. In the DO dashboard, start the flow to create a new app
2. Connect your GitHub account (installs the DigitalOcean GitHub app)
3. Grant access to the repos (or the whole org) that will host apps
4. After that, the MCP's `app-create` tool can reference any granted repo

## Security Notes

- Treat the PAT like a password — full account access
- Do NOT commit `~/.mcp.json` or `.env` containing the PAT
- Rotate the PAT periodically; revoke old tokens at https://cloud.digitalocean.com/account/api/tokens
- If you narrowed the scope at token creation, a leaked token is less destructive — prefer narrow scopes over a write-all token when the skill use case allows
