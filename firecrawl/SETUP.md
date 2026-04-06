# Firecrawl Docker Setup

## Prerequisites

- Docker Engine with Compose v2+
- Minimum 8GB RAM recommended (Playwright + API are memory-hungry)
- Port 3002 available

## Quick Start

### 1. Clone the Firecrawl repo

```bash
mkdir -p ~/firecrawl-docker && cd ~/firecrawl-docker
git clone --depth 1 https://github.com/mendableai/firecrawl.git .
```

### 2. Switch to pre-built images

Edit `docker-compose.yaml` — replace the three `build:` directives with pre-built images:

```yaml
# For x-common-service (api):
image: ghcr.io/firecrawl/firecrawl

# For playwright-service:
image: ghcr.io/firecrawl/playwright-service:latest

# For nuq-postgres:
image: ghcr.io/firecrawl/nuq-postgres:latest
```

### 3. Configure environment

```bash
cat > .env <<'EOF'
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false
BULL_AUTH_KEY=firecrawl-admin-2026
TEST_API_KEY=fc-test-key-local
LOGGING_LEVEL=INFO
NUM_WORKERS_PER_QUEUE=4
CRAWL_CONCURRENT_REQUESTS=5
MAX_CONCURRENT_JOBS=3
BROWSER_POOL_SIZE=3
SEARXNG_ENDPOINT=http://host.docker.internal:8090
EOF
```

### 4. Pull and start

```bash
docker compose pull
docker compose up -d
```

### 5. Verify

```bash
# Check containers
docker compose ps

# Test scrape
curl -X POST http://localhost:3002/v1/scrape \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}'
```

## Services (5 containers)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| api | `ghcr.io/firecrawl/firecrawl` | 3002 (exposed) | REST API server + workers |
| playwright-service | `ghcr.io/firecrawl/playwright-service` | 3000 (internal) | Headless browser |
| redis | `redis:alpine` | 6379 (internal) | Cache + rate limiting |
| rabbitmq | `rabbitmq:3-management` | 5672 (internal) | Job queue |
| nuq-postgres | `ghcr.io/firecrawl/nuq-postgres` | 5432 (internal) | PostgreSQL database |

## Queue Admin Panel

Access at: `http://localhost:3002/admin/firecrawl-admin-2026/queues`

## Common Operations

```bash
# Stop all services
docker compose down

# View API logs
docker compose logs -f api

# Restart API only
docker compose restart api

# Full reset
docker compose down -v
docker compose up -d
```

## Optional: LLM Integration

For `/v1/extract` and `summary` format, add to `.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4-turbo
```

Or for local LLMs via Ollama:
```
OLLAMA_BASE_URL=http://host.docker.internal:11434
MODEL_NAME=llama3
```

## Optional: SearXNG Integration

Firecrawl uses SearXNG for `/v1/search`. If SearXNG is running locally:
```
SEARXNG_ENDPOINT=http://host.docker.internal:8090
```

## MCP Server Setup

The Firecrawl MCP server provides 12 tools for Claude Code integration.

### Install

```bash
npm install -g firecrawl-mcp
```

### Register in Claude Code

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "firecrawl-mcp",
      "env": {
        "FIRECRAWL_API_KEY": "fc-test-key-local",
        "FIRECRAWL_API_URL": "http://localhost:3002"
      }
    }
  }
}
```

Restart Claude Code. Tools appear as `mcp__firecrawl__*`.

### Update MCP

```bash
npm install -g firecrawl-mcp
# Then restart Claude Code
```
