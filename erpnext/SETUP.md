# ERPNext Docker Setup

## Prerequisites

- Docker Engine with Compose v2+
- Minimum 4GB RAM recommended
- Port 8888 available (remapped from default 8080)

## Quick Start

### 1. Clone the frappe_docker repo

```bash
mkdir -p ~/erpnext-docker && cd ~/erpnext-docker
git clone --depth 1 https://github.com/frappe/frappe_docker.git .
```

### 2. Start with the PWD (Play With Docker) compose file

The `pwd.yml` file is the all-in-one quickstart that includes MariaDB, Redis, and auto-creates a site with ERPNext installed.

```bash
# If port 8080 is taken, edit pwd.yml to remap:
# Change "8080:8080" to "8888:8080" under frontend > ports

docker compose -f pwd.yml up -d
```

### 3. Wait for site creation

The `create-site` container bootstraps the database and installs ERPNext. This takes 2-5 minutes.

```bash
# Watch progress
docker compose -f pwd.yml logs create-site --follow

# Done when you see: "Current Site set to frontend"
```

### 4. Access ERPNext

Open http://localhost:8888 (or :8080 if you kept the default port).

**Default credentials:** `Administrator` / `admin`

## Services (10 containers)

| Service | Image | Purpose |
|---------|-------|---------|
| frontend | `frappe/erpnext:v16.12.0` | Nginx reverse proxy (port 8888) |
| backend | `frappe/erpnext:v16.12.0` | Werkzeug app server |
| websocket | `frappe/erpnext:v16.12.0` | Socket.IO realtime |
| queue-short | `frappe/erpnext:v16.12.0` | Short task worker |
| queue-long | `frappe/erpnext:v16.12.0` | Long task worker |
| scheduler | `frappe/erpnext:v16.12.0` | Cron/scheduled jobs |
| configurator | `frappe/erpnext:v16.12.0` | One-shot config init |
| create-site | `frappe/erpnext:v16.12.0` | One-shot site creation |
| db | `mariadb:10.6` | MariaDB database |
| redis-cache | `redis:6.2-alpine` | Application cache |
| redis-queue | `redis:6.2-alpine` | Job queue |

## Post-Setup: Generate API Keys

1. Log in as Administrator at http://localhost:8888
2. Navigate to: `http://localhost:8888/app/user/Administrator`
3. Scroll to **API Access** section
4. Click **Generate Keys**
5. Copy the **API Secret** immediately (shown only once)
6. Your **API Key** is displayed in the same section
7. Update `.env` in this skill:
   ```
   ERPNEXT_API_KEY=<your-api-key>
   ERPNEXT_API_SECRET=<your-api-secret>
   ERPNEXT_AUTH_TOKEN=token <your-api-key>:<your-api-secret>
   ```

### Test the credentials

```bash
curl http://localhost:8888/api/method/frappe.auth.get_logged_user \
  -H "Authorization: token <api_key>:<api_secret>"
```

## Common Operations

```bash
# Stop all services
docker compose -f pwd.yml down

# View logs
docker compose -f pwd.yml logs -f backend

# Restart backend only
docker compose -f pwd.yml restart backend

# Run bench command inside container
docker compose -f pwd.yml exec backend bench --site frontend list-apps

# Backup
docker compose -f pwd.yml exec backend bench --site frontend backup
# Backups are stored in: sites/frontend/private/backups/

# Restore
docker compose -f pwd.yml exec backend bench --site frontend restore <backup-file>

# Update ERPNext (change version in pwd.yml image tags)
# Edit: image: frappe/erpnext:v16.13.0
docker compose -f pwd.yml pull
docker compose -f pwd.yml down
docker compose -f pwd.yml up -d
docker compose -f pwd.yml exec backend bench --site frontend migrate

# Full reset (destroys all data)
docker compose -f pwd.yml down -v
docker compose -f pwd.yml up -d
```

## Production Deployment

For production, use the modular compose approach instead of `pwd.yml`:

```bash
docker compose \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.traefik-ssl.yaml \
  up -d
```

Configure via `.env`:
```
ERPNEXT_VERSION=v16.12.0
DB_PASSWORD=<secure-password>
LETSENCRYPT_EMAIL=admin@yourdomain.com
SITES_RULE=Host(`erp.example.com`)
```

Then create a site:
```bash
docker compose exec backend bench new-site erp.example.com \
  --mariadb-root-password=<DB_PASSWORD> \
  --admin-password=<admin-password> \
  --install-app erpnext
```

## MCP Server Setup

The ERPNext MCP server provides 6 generic tools that cover all DocTypes. It is the **primary interface** for interacting with ERPNext from Claude Code.

### Installation (already done if following this guide)

```bash
cd ~/.openclaw/workspace/mcp-servers
git clone --depth 1 https://github.com/rakeshgangwar/erpnext-mcp-server.git
cd erpnext-mcp-server
npm install
npm run build
```

### Register in Claude Code

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "erpnext": {
      "command": "node",
      "args": ["<HOME>/.openclaw/workspace/mcp-servers/erpnext-mcp-server/build/index.js"],
      "env": {
        "ERPNEXT_URL": "http://localhost:8888",
        "ERPNEXT_API_KEY": "<your-api-key>",
        "ERPNEXT_API_SECRET": "<your-api-secret>"
      }
    }
  }
}
```

Restart Claude Code after editing `~/.mcp.json`. The tools will be available as `mcp__erpnext__*`.

### Verify MCP is working

After restart, the 6 `mcp__erpnext__*` tools should appear in the deferred tools list. Test with:
- `mcp__erpnext__get_doctypes` — list all available DocTypes
- `mcp__erpnext__get_documents` with `{"doctype": "Item", "limit": 3}` — list items

### Rebuild after updates

```bash
cd ~/.openclaw/workspace/mcp-servers/erpnext-mcp-server
git pull && npm install && npm run build
```

Then restart Claude Code.

### Environment Variables

The MCP server reads from the process environment (set in `~/.mcp.json`):
- `ERPNEXT_URL` — Base URL (e.g., `http://localhost:8888`)
- `ERPNEXT_API_KEY` — API key from User > API Access
- `ERPNEXT_API_SECRET` — API secret (shown once during key generation)

Update `ERPNEXT_URL` in `~/.mcp.json` if you change the server address or port.
