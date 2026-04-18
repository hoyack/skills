# Paperclip AI Setup Guide

Complete setup and configuration guide for Paperclip AI with OpenClaw gateway integration and Codex CLI authentication.

## Overview

Paperclip AI is an autonomous AI agent platform with:
- **Web UI** at http://192.168.1.68:3100
- **REST API** at http://192.168.1.68:3100/api
- **Codex CLI** integration for code editing
- **OpenClaw gateway** integration for agent operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Paperclip AI                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Web UI     │  │   REST API   │  │   Codex CLI  │       │
│  │   :3100      │  │   /api/*     │  │   (internal) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Embedded PostgreSQL Database                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                          │
│                    ws://192.168.1.68:18789                   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- OpenClaw gateway running (for agent integration)
- 4GB RAM minimum
- 10GB disk space

## Initial Deployment

### 1. Create Docker Compose Configuration

```yaml
version: '3.8'

services:
  paperclip:
    image: ghcr.io/paperclipai/paperclip:latest
    container_name: paperclip
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      # Main Paperclip data persistence
      - ~/paperclip-data:/paperclip
      # Codex CLI auth persistence (crucial for OAuth)
      - ~/paperclip-data/.codex:/home/node/.codex:rw
    environment:
      # Network binding
      - PAPERCLIP_BIND=0.0.0.0
      
      # Better Auth configuration (required for authenticated mode)
      - BETTER_AUTH_SECRET=<auth-secret>
      - BETTER_AUTH_TRUSTED_ORIGINS=http://192.168.1.68:3100,http://localhost:3100
      
      # Codex CLI configuration (critical for OAuth to work)
      - CODEX_HOME=/home/node/.codex
      - HOME=/home/node
      
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3100/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 2. Start the Container

```bash
cd ~/Documents/skills/paperclip
docker compose up -d
```

### 3. Verify Startup

```bash
# Check logs
docker logs paperclip --tail 50

# Check health
curl http://192.168.1.68:3100/api/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.3.1",
  "deploymentMode": "authenticated",
  "bootstrapStatus": "bootstrap_pending"
}
```

## Initial Configuration (One-Time Setup)

### Step 1: Generate Bootstrap CEO Invite

```bash
docker exec paperclip pnpm paperclipai auth bootstrap-ceo --base-url http://192.168.1.68:3100
```

Output:
```
Invite URL: http://192.168.1.68:3100/invite/pcp_bootstrap_<token>
Expires: 2026-04-15Txx:xx:xx.xxxZ
```

### Step 2: Access Invite URL and Create Admin Account

1. Open the invite URL in your browser
2. Click "Create account"
3. Fill in:
   - Name: CEO Admin
   - Email: your-email@example.com
   - Password: strong-password
4. Log in with credentials

### Step 3: Accept Bootstrap Invite

After creating the account, you need to accept the bootstrap invite via API:

```bash
# Login and get cookie
COOKIE=$(curl -X POST http://192.168.1.68:3100/api/auth/sign-in/email \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  -v 2>&1 | grep -i "set-cookie" | grep "better-auth" | sed 's/< set-cookie: //' | cut -d';' -f1)

# Accept bootstrap invite
curl -X POST "http://192.168.1.68:3100/api/invites/<invite-token>/accept" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.1.68:3100" \
  -b "$COOKIE" \
  -d '{"requestType": "human"}'
```

## Critical Configuration Fixes

### Fix 1: Cookie Secure Flag (HTTP Support)

**Problem:** Login works but session fails because cookies have `Secure` flag requiring HTTPS.

**Solution:** Set `BETTER_AUTH_TRUSTED_ORIGINS` environment variable to allow HTTP:

```yaml
environment:
  - BETTER_AUTH_TRUSTED_ORIGINS=http://192.168.1.68:3100,http://localhost:3100
```

This removes the `Secure` flag from cookies, allowing them to work over HTTP.

### Fix 2: Codex Auth Permissions

**Problem:** Codex authentication works but Paperclip agents can't access the auth file.

**Solution:** Ensure proper permissions on the `.codex` directory:

```bash
# Fix ownership (runs as node user in container)
docker exec paperclip chown -R node:node /home/node/.codex

# Set readable permissions
docker exec paperclip chmod 644 /home/node/.codex/auth.json
```

### Fix 3: CODEX_HOME Environment Variable

**Problem:** Codex CLI can't find auth file in sandboxed adapter environment.

**Solution:** Set `CODEX_HOME` explicitly:

```yaml
environment:
  - CODEX_HOME=/home/node/.codex
  - HOME=/home/node
```

## Codex OAuth Authentication

### Step 1: Authenticate Codex CLI

Run device auth flow inside the container:

```bash
docker exec paperclip codex login --device-auth
```

You'll see:
```
Open this link: https://auth.openai.com/codex/device
Enter code: XXXX-XXXX
```

Complete the flow in your browser within 15 minutes.

### Step 2: Verify Authentication

```bash
docker exec paperclip codex login status
```

Expected: `Logged in using ChatGPT`

### Step 3: Persist Auth Across Restarts

The auth is stored in `~/paperclip-data/.codex/` which is mounted to `/home/node/.codex` in the container. This survives container restarts.

**Important:** If auth.json is owned by root (happens during OAuth), fix permissions:

```bash
docker exec paperclip chown -R node:node /home/node/.codex
```

## OpenClaw Gateway Integration

Paperclip agents can use OpenClaw gateway for operations. Configure agents with:

- **Adapter Type:** `openclaw_gateway`
- **Gateway URL:** `ws://192.168.1.68:18789/`

## Troubleshooting

### Login Page Reloads After Submit

**Cause:** Cookies have `Secure` flag but you're using HTTP.

**Fix:** Set `BETTER_AUTH_TRUSTED_ORIGINS` environment variable.

### Codex Test Fails with "OPENAI_API_KEY is not set"

**Cause:** Agent can't access Codex auth file or permissions are wrong.

**Fix:**
```bash
# Check auth exists
docker exec paperclip ls -la /home/node/.codex/auth.json

# Fix permissions
docker exec paperclip chown -R node:node /home/node/.codex

# Verify
docker exec paperclip codex login status
```

### "Bootstrap CEO invite is only required for authenticated mode"

**Cause:** CLI doesn't detect deployment mode correctly from config.

**Fix:** Ensure config.json has `deploymentMode` (not just `mode`):

```json
{
  "server": {
    "deploymentMode": "authenticated"
  }
}
```

### Database Permission Errors

**Cause:** PostgreSQL data directory has wrong permissions.

**Fix:**
```bash
# Reset data (WARNING: destroys all data)
docker stop paperclip
docker rm paperclip
sudo rm -rf ~/paperclip-data/instances
mkdir -p ~/paperclip-data/.codex
docker compose up -d
```

## API Authentication

All API requests require authentication via cookie:

```bash
# Login and extract cookie
COOKIE=$(curl -X POST http://192.168.1.68:3100/api/auth/sign-in/email \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  -v 2>&1 | grep -i "set-cookie" | grep "better-auth" | sed 's/< set-cookie: //' | cut -d';' -f1)

# Use cookie for subsequent requests
curl -s http://192.168.1.68:3100/api/companies -b "$COOKIE"
```

## Maintenance

### Backup Database

```bash
# Create backup
docker exec paperclip pnpm paperclipai db:backup

# Backups stored in ~/paperclip-data/instances/default/data/backups/
```

### Update Container

```bash
docker pull ghcr.io/paperclipai/paperclip:latest
docker compose up -d
```

### View Logs

```bash
# Real-time
docker logs -f paperclip

# Recent
docker logs paperclip --tail 100
```

## Security Considerations

1. **BETTER_AUTH_SECRET:** Use a strong random secret in production
2. **Cookie Security:** The `Secure` flag is disabled for HTTP - use HTTPS in production
3. **Network Binding:** Currently bound to 0.0.0.0 (all interfaces) - restrict in production
4. **Codex Auth:** Auth tokens stored in container - ensure volume permissions are correct

## Related Documentation

- [API Reference](./Docs/API.md)
- [MCP Server](./Docs/MCP.md)
- [SKILL.md](./SKILL.md) - Quick reference for using Paperclip
