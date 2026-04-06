# SearXNG Docker Setup

## Prerequisites

- Docker Engine with Compose v2+
- Port 8090 available (remapped from default 8080)

## Quick Start

### 1. Create directory

```bash
mkdir -p ~/searxng-docker/core-config && cd ~/searxng-docker
```

### 2. Download compose files

```bash
curl -fsSL \
  -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml \
  -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example
```

### 3. Configure

```bash
# Set port
echo "SEARXNG_PORT=8090" > .env

# Generate secret and create settings
SECRET=$(openssl rand -hex 32)
cat > core-config/settings.yml <<EOF
use_default_settings: true

server:
  secret_key: "$SECRET"
  limiter: false
  image_proxy: true
  port: 8090
  bind_address: "0.0.0.0"

search:
  formats:
    - html
    - json
    - csv
    - rss
  safesearch: 0
  autocomplete: "google"
EOF
```

### 4. Start

```bash
docker compose up -d
```

### 5. Verify

```bash
# Check containers
docker compose ps

# Test JSON API
curl -s 'http://localhost:8090/search?q=test&format=json' | python3 -m json.tool | head -20

# Web UI
# Open http://localhost:8090
```

## Services (2 containers)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| core | `searxng/searxng:latest` | 8090 (exposed) | Search engine |
| valkey | `valkey/valkey:9-alpine` | 6379 (internal) | Cache layer (Redis-compatible) |

## Important: JSON API Must Be Enabled

The `settings.yml` must include `json` in `search.formats`:
```yaml
search:
  formats:
    - html
    - json
```

Without this, `?format=json` returns an error.

## Important: Secret Key Must Be Changed

SearXNG will crash on startup if `secret_key` is left as `ultrasecretkey`. Always generate a unique key:
```bash
openssl rand -hex 32
```

## Common Operations

```bash
# Stop
docker compose down

# View logs
docker compose logs -f core

# Restart after settings change
docker compose restart core

# Full reset
docker compose down -v
docker compose up -d
```

## Editing Settings After First Start

The container changes file ownership on `core-config/settings.yml`. To edit after startup:
```bash
docker compose stop core
docker run --rm -v $(pwd)/core-config:/cfg alpine \
  sh -c "vi /cfg/settings.yml"
docker compose start core
```

Or edit via a disposable container:
```bash
docker run --rm -v $(pwd)/core-config:/cfg alpine \
  sh -c "sed -i 's/old_value/new_value/' /cfg/settings.yml"
docker compose restart core
```

## Adding/Disabling Engines

Edit `core-config/settings.yml` to customize engines:
```yaml
engines:
  - name: google
    engine: google
    disabled: false

  - name: bing
    engine: bing
    disabled: true   # Disable this engine
```

See all available engines: `curl -s http://localhost:8090/config | python3 -m json.tool`

## MCP Server Setup

The SearXNG MCP server provides 2 tools for Claude Code integration.

### Install

```bash
npm install -g mcp-searxng
```

### Register in Claude Code

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "searxng": {
      "command": "mcp-searxng",
      "env": {
        "SEARXNG_URL": "http://localhost:8090"
      }
    }
  }
}
```

Restart Claude Code. Tools appear as `mcp__searxng__*`.

### Update MCP

```bash
npm install -g mcp-searxng
# Then restart Claude Code
```
