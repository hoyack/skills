# LAN Access Configuration ✅

## Overview

Nginx reverse proxy has been configured to make Twenty CRM accessible from your LAN.

## Access URLs

| URL | Access Type |
|-----|-------------|
| http://localhost:3000 | Direct access (local only) |
| http://<your-host-ip> | Via nginx proxy (LAN access) ✅ |
| http://localhost | Via nginx proxy (local) ✅ |

**For remote LAN access:** Use http://<your-host-ip> from any device on your network.

---

## What's Configured

### Nginx Container
- **Image:** nginx:alpine
- **Container:** nginx-proxy
- **Port:** 80 (mapped to host port 80)
- **Network:** skills-network (shared with other services)

### Files Created
```
nginx/
├── docker-compose.yml    # Nginx service definition
└── nginx.conf            # Reverse proxy configuration
```

### Nginx Configuration Features
- Reverse proxy to Twenty CRM (twenty-server:3000)
- WebSocket support (for real-time CRM features)
- Proper headers for proxy pass
- Increased timeouts for CRM operations

---

## Testing

### From the server itself:
```bash
# Direct access
curl http://localhost:3000/healthz

# Via nginx
curl http://localhost/healthz
curl http://<your-host-ip>/healthz
```

### From another device on your LAN:
Open a browser and navigate to: **http://<your-host-ip>**

You should see the Twenty CRM login page.

---

## All Services - Access Summary

| Service | Local URL | LAN URL | Port |
|---------|-----------|---------|------|
| **SearXNG** | http://localhost:8090 | http://<your-host-ip>:8090 | 8090 |
| **Twenty CRM** | http://localhost:3000 | http://<your-host-ip> | 80 (nginx) |
| **Firecrawl** | http://localhost:3002 | http://<your-host-ip>:3002 | 3002 |

---

## Next Steps for Twenty CRM Setup

1. **Open Twenty CRM** from your remote device:
   - Navigate to: http://<your-host-ip>

2. **Create admin account** (if not already done)

3. **Get API key** for MCP:
   - Settings → APIs & Webhooks
   - Create new key
   - Copy the key

4. **Update MCP config** (on the server):
   ```bash
   nano ~/.mcp.json
   ```
   Update the `TWENTY_API_KEY` value.

5. **Restart Claude Code** to load the MCP servers

---

## Troubleshooting

### Cannot access from LAN
1. Check firewall rules:
   ```bash
   sudo ufw status
   # or
   sudo iptables -L -n | grep 80
   ```

2. Verify nginx is listening on all interfaces:
   ```bash
   sudo netstat -tlnp | grep 80
   ```

3. Check nginx container logs:
   ```bash
   cd nginx && docker compose logs -f
   ```

### Port 80 already in use
If port 80 is already in use, change the port mapping in `nginx/docker-compose.yml`:
```yaml
ports:
  - "8080:80"  # Use port 8080 instead
```
Then access via: http://<your-host-ip>:8080

---

## Commands

```bash
# View nginx logs
cd nginx && docker compose logs -f

# Restart nginx
cd nginx && docker compose restart

# Stop nginx
cd nginx && docker compose down

# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## Security Note

This configuration exposes Twenty CRM on port 80 without SSL. It's suitable for LAN access only. For external internet access, you should:
1. Set up SSL/TLS certificates (Let's Encrypt)
2. Add authentication
3. Configure a firewall to restrict access
