# Twenty CRM Docker Setup

## Prerequisites

- Docker Engine with Compose v2+
- Minimum 2GB RAM available
- Ports 3000 available (or remap in .env)

## Quick Start

### 1. Create deployment directory

```bash
mkdir -p ~/twenty-docker && cd ~/twenty-docker
```

### 2. Download compose and env files

```bash
curl -sL -o docker-compose.yml \
  https://raw.githubusercontent.com/twentyhq/twenty/main/packages/twenty-docker/docker-compose.yml

curl -sL -o .env \
  https://raw.githubusercontent.com/twentyhq/twenty/refs/heads/main/packages/twenty-docker/.env.example
```

### 3. Generate secrets and configure

```bash
# Generate secure secrets
APP_SECRET=$(openssl rand -base64 32)
PG_PASSWORD=$(openssl rand -hex 16)

# Write .env
cat > .env <<EOF
TAG=latest

PG_DATABASE_USER=postgres
PG_DATABASE_PASSWORD=${PG_PASSWORD}
PG_DATABASE_HOST=db
PG_DATABASE_PORT=5432
REDIS_URL=redis://redis:6379

SERVER_URL=http://localhost:3000

APP_SECRET=${APP_SECRET}

STORAGE_TYPE=local
EOF
```

### 4. Pull images and start

```bash
docker compose pull
docker compose up -d
```

### 5. Verify

```bash
# Check all 4 services are healthy
docker compose ps

# Test health endpoint
curl -f http://localhost:3000/healthz
```

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| server | `twentycrm/twenty:latest` | 3000 (exposed) | API + frontend |
| worker | `twentycrm/twenty:latest` | none | Background jobs |
| db | `postgres:16` | 5432 (internal) | PostgreSQL database |
| redis | `redis` | 6379 (internal) | Cache + queue |

## Post-Setup: Create API Key

1. Open http://localhost:3000
2. Create your admin account (first-time signup)
3. Go to **Settings > APIs & Webhooks**
4. Click **"+ Create key"**
5. Copy the key and update `.env` in this skill:
   ```
   TWENTY_CRM_API_KEY=<your-key>
   ```

## Common Operations

```bash
# Stop all services
docker compose down

# View server logs
docker compose logs -f server

# Backup database
docker exec twenty-db-1 pg_dump -U postgres default > backup_$(date +%Y%m%d).sql

# Restore database
docker compose stop server worker
docker exec -i twenty-db-1 psql -U postgres default < backup.sql
docker compose up -d

# Update to latest version
docker compose pull
docker compose down
docker compose up -d

# Full reset (destroys all data)
docker compose down -v
docker compose up -d
```

## MCP Server Setup

The Twenty CRM MCP server provides 29 tools for Claude Code integration. It is the **primary interface** for interacting with Twenty CRM.

### Installation (already done if following this guide)

```bash
cd ~/.openclaw/workspace/mcp-servers
git clone --depth 1 https://github.com/jezweb/twenty-mcp.git
cd twenty-mcp
npm install
npm run build
```

### Register in Claude Code

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "twenty-crm": {
      "command": "node",
      "args": ["<HOME>/.openclaw/workspace/mcp-servers/twenty-mcp/dist/index.js"],
      "env": {
        "TWENTY_API_KEY": "<your-api-key>",
        "TWENTY_BASE_URL": "http://localhost:3000"
      }
    }
  }
}
```

Restart Claude Code after editing `~/.mcp.json`. The tools will be available as `mcp__twenty-crm__*`.

### Verify MCP is working

After restart, the 29 `mcp__twenty-crm__*` tools should appear in the deferred tools list. Test with:
- `mcp__twenty-crm__search_contacts` — search for a known contact
- `mcp__twenty-crm__list_all_objects` — list all available CRM objects

### Rebuild after updates

```bash
cd ~/.openclaw/workspace/mcp-servers/twenty-mcp
git pull && npm install && npm run build
```

Then restart Claude Code.

## Production Notes

- Set `SERVER_URL` to your actual domain (e.g., `https://crm.example.com`)
- Use a reverse proxy (Nginx/Traefik) with SSL termination
- For multi-instance, switch `STORAGE_TYPE` to `S3` with appropriate credentials
- Minimum 2GB RAM required; the server process will crash if memory is insufficient
- Update `TWENTY_BASE_URL` in `~/.mcp.json` if you change the server URL
