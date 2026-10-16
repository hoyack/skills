# Twenty CRM GraphQL Error Fix

## Issue
Error: `Unknown type "EmailThreadConfiguration"` in browser console when accessing Twenty CRM.

## Root Cause
The Twenty CRM v1.21.0 image had feature flags enabled (`CALENDAR_PROVIDER_GOOGLE=true`) that referenced GraphQL types not fully implemented in the schema.

## Fix Applied

### Updated `twenty-crm/docker-compose.yml`

**Before:**
```yaml
environment:
  - CALENDAR_PROVIDER_GOOGLE=true
  - MESSAGE_QUEUE_PROVIDER=pg-boss
```

**After:**
```yaml
environment:
  - CALENDAR_PROVIDER_GOOGLE=false
  - IS_MESSAGING_ENABLED=false
```

### Services Restarted
```bash
cd twenty-crm && docker compose down && docker compose up -d
```

## Current Status

| Service | Status | URL |
|---------|--------|-----|
| Twenty CRM | ✅ Healthy | http://<your-host-ip> |
| Nginx Proxy | ✅ Running | http://<your-host-ip> |
| Database | ✅ Healthy | - |

## Access URLs

- **Local:** http://localhost:3000
- **Via Nginx (local):** http://localhost
- **LAN Access:** http://<your-host-ip>

## Test Commands

```bash
# Test local access
curl http://localhost/healthz

# Test LAN access
curl http://<your-host-ip>/healthz

# Direct server test
curl http://localhost:3000/healthz
```

## Clear Browser Cache

If you still see errors, clear your browser cache or use an incognito/private window to test.

## Next Steps

1. Open http://<your-host-ip> in your browser
2. Create admin account (if not done)
3. Get API key from Settings → APIs & Webhooks
4. Update `~/.mcp.json` with the API key
5. Restart Claude Code for MCP servers

## All Services Status

```
✅ SearXNG       - http://<your-host-ip>:8090
✅ Twenty CRM    - http://<your-host-ip>
✅ Firecrawl     - http://<your-host-ip>:3002
✅ Nginx Proxy   - http://<your-host-ip> (port 80)
```
