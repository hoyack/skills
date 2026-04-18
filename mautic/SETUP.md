# Mautic Setup

Mautic is an open-source marketing automation platform.

## Deployment

Mautic is deployed via Docker Compose with MariaDB and Redis.

```bash
cd ~/skills/mautic
docker-compose up -d
```

## Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| Mautic App | mautic-app | 8080 | Apache/PHP web application |
| Database | mautic-db | - | MariaDB 10.11 |
| Cache | mautic-redis | - | Redis 7 for sessions/cache |
| Cron | mautic-cron | - | Background job processor |

## Initial Setup

1. Access Mautic at http://192.168.1.68:8080
2. Complete the web installer:
   - Database: mautic-db:3306
   - DB Name: mautic
   - DB User: mautic
   - DB Password: <db-password>
   - Admin User: <username>
   - Admin Password: <password>

3. Enable API access:
   - Settings → Configuration → API Settings
   - Enable "API enabled"
   - Save & Close

## API Configuration

The MCP server uses HTTP Basic Auth with the Mautic credentials.

### Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
MAUTIC_BASE_URL=http://192.168.1.68:8080/api
MAUTIC_USERNAME=<username>
MAUTIC_PASSWORD=<password>
```

### Testing the API

```bash
# Test connectivity
curl -u <username>:<password> \
  http://192.168.1.68:8080/api/contacts?limit=1
```

## MCP Server Setup

The MCP server is located in `mcp-server/` directory.

```bash
cd ~/skills/mautic/mcp-server
npm install
```

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "mautic": {
      "command": "node",
      "args": ["/home/hoyack/skills/mautic/mcp-server/index.js"],
      "env": {
        "MAUTIC_BASE_URL": "http://192.168.1.68:8080/api",
        "MAUTIC_USERNAME": "<username>",
        "MAUTIC_PASSWORD": "<password>"
      }
    }
  }
}
```

## Troubleshooting

### API Returns 403 Forbidden
- Verify API is enabled in Mautic settings
- Check that the user has API permissions

### API Returns 401 Unauthorized
- Verify username and password are correct
- Check that the user account is active

### Cron Jobs Not Running
- Check cron container logs: `docker logs mautic-cron`
- Verify cron jobs in Mautic settings
