---
name: unifi-network-management
description: Manage UniFi Network appliances (UDM Pro, Cloud Key, etc.) via the UniFi Network API. Use this skill when configuring port forwarding, firewall rules, VLANs, or network settings on UniFi devices. Triggers include mentions of "UDM Pro", "UniFi", "port forward", "firewall rule", or when the user needs to expose services through a UniFi router/gateway. This skill does NOT manage UniFi Protect (cameras) or UniFi Access (door access) — only network/routing functions.
---

# UniFi Network Management

Manage UniFi Network appliances via the UniFi Network API. This skill is primarily used for:
- **Port forwarding** — Expose internal services to the internet
- **Firewall rules** — Allow/block traffic between networks
- **Network configuration** — VLANs, WAN/LAN settings
- **Site management** — Switch sites on multi-site controllers

## Scope

- **In scope:** Port forwarding, firewall rules, network/site settings, static routes, VPN configuration
- **Out of scope:** UniFi Protect (cameras), UniFi Access (door access), UniFi Talk (VOIP), device adoption, firmware updates

## Prerequisites

1. **UniFi Network Application** running on UDM Pro, Cloud Key, or self-hosted
2. **UniFi API Key** — Generated at `Settings → Control Plane → API Access` in the UniFi Network app
3. **Environment variables configured** in `.env`:
   - `UNIFI_API_KEY` — Your API key
   - `UNIFI_CONTROLLER_URL` — Full URL to your controller (e.g., `https://10.0.0.1:443` or `https://unifi.hoyack.com:443`)
   - `UNIFI_VERIFY_SSL` — Set to `false` for self-signed certificates on local controllers
4. **Default site** — Most home setups use the default site. If you have multiple sites, you'll need the site ID.

## API Reference

The UniFi Network API uses a REST-like interface with JSON responses. Key endpoints:

- `GET /proxy/network/api/self/sites` — List sites
- `GET /proxy/network/api/s/{site}/rest/portforward` — List port forwarding rules
- `POST /proxy/network/api/s/{site}/rest/portforward` — Create port forwarding rule
- `DELETE /proxy/network/api/s/{site}/rest/portforward/{id}` — Delete rule
- `GET /proxy/network/api/s/{site}/rest/firewallrule` — List firewall rules

For UDM Pro/UniFi OS consoles, all API calls go through `/proxy/network/api/...`. For standalone Network Applications (legacy), use `/api/...`.

## Using the API

The skill stores credentials in `.env` in the skill directory. Use these with curl or any HTTP client:

```bash
# Load credentials
source /home/hoyack/.openclaw/workspace/skills/unifi-network-management/.env

# Test connectivity - list sites
curl -s -k -H "X-API-KEY: ${UNIFI_API_KEY}" \
  "${UNIFI_CONTROLLER_URL}/proxy/network/api/self/sites" | jq .

# List port forwarding rules for default site
curl -s -k -H "X-API-KEY: ${UNIFI_API_KEY}" \
  "${UNIFI_CONTROLLER_URL}/proxy/network/api/s/default/rest/portforward" | jq '.data'

# Create a port forward (example: HTTPS to k3s cluster)
curl -s -k -H "X-API-KEY: ${UNIFI_API_KEY}" \
  -H "Content-Type: application/json" \
  -X POST \
  "${UNIFI_CONTROLLER_URL}/proxy/network/api/s/default/rest/portforward" \
  -d '{
    "name": "k3s-https",
    "src": "any",
    "dst_port": "443",
    "fwd": "10.0.0.47",
    "fwd_port": "30271",
    "proto": "tcp",
    "enabled": true
  }'
```

## Common Operations

### Port Forwarding for k3s/Traefik

From `ROUTER_CONFIG.md`, you need to forward external ports to the k3s NodePort:

```bash
# HTTPS (443 → 30271)
curl -s -k -H "X-API-KEY: ${UNIFI_API_KEY}" \
  -H "Content-Type: application/json" \
  -X POST \
  "${UNIFI_CONTROLLER_URL}/proxy/network/api/s/default/rest/portforward" \
  -d '{
    "name": "alamo-https",
    "src": "any",
    "dst_port": "443",
    "fwd": "10.0.0.47",
    "fwd_port": "30271",
    "proto": "tcp",
    "enabled": true
  }'

# HTTP (80 → 31824)
curl -s -k -H "X-API-KEY: ${UNIFI_API_KEY}" \
  -H "Content-Type: application/json" \
  -X POST \
  "${UNIFI_CONTROLLER_URL}/proxy/network/api/s/default/rest/portforward" \
  -d '{
    "name": "alamo-http",
    "src": "any",
    "dst_port": "80",
    "fwd": "10.0.0.47",
    "fwd_port": "31824",
    "proto": "tcp",
    "enabled": true
  }'
```

### Find the Site ID

```bash
curl -s -k -H "X-API-KEY: ${UNIFI_API_KEY}" \
  "${UNIFI_CONTROLLER_URL}/proxy/network/api/self/sites" | jq '.data[] | {name, _id}'
```

Replace `default` with your site name if different.

## Troubleshooting

### SSL Certificate Errors

Local UniFi controllers typically use self-signed certificates. Set `UNIFI_VERIFY_SSL=false` or use `-k` with curl.

### 401 Unauthorized

- Verify the API key hasn't been revoked in the UniFi UI
- Check that the user who generated the API key still has admin access
- Try regenerating the key at `Settings → Control Plane → API Access`

### 404 Not Found

- Verify you're using `/proxy/network/api/...` for UDM Pro/UniFi OS, or `/api/...` for standalone Network Application
- Check the site ID is correct

### Port Forward Not Working

- Verify the target IP and port are reachable from the UDM Pro
- Check if the firewall rule was auto-created (UniFi does this automatically for port forwards)
- Ensure the WAN interface has the expected IP (check with `ip addr` on the UDM Pro)

## Files

- `.env` — API credentials (never commit to git)
- `ROUTER_CONFIG.md` (workspace root) — Cluster networking requirements

## Related

- `ROUTER_CONFIG.md` in workspace root — Documents required port forwards for the k3s cluster
- `cloudflare-dns-management` skill — If you need DNS to point to the WAN IP
- `digitalocean-management` skill — For cloud-hosted alternatives
