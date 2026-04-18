# DigitalOcean API Overview

Base URL and conventions shared by every service in this folder. Most skill operations go through the MCP server, but falling back to raw HTTP is sometimes necessary (operations not yet in MCP, rate limit inspection, etc.).

## Base URL

```
https://api.digitalocean.com/v2
```

## Authentication

Personal Access Token (PAT) via `Authorization: Bearer <PAT>`:

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  https://api.digitalocean.com/v2/account
```

Tokens are account-scoped with per-service permission bits. Grant only what's needed at token creation — a leaked write-all token is a full compromise.

## Pagination

List endpoints return:
```json
{
  "droplets": [...],
  "links": {
    "pages": {
      "next": "https://api.digitalocean.com/v2/droplets?page=2",
      "last": "..."
    }
  },
  "meta": { "total": 42 }
}
```

Supports `?page=N&per_page=M`. Default `per_page=20`, max `200`. For many resources, `?per_page=200` is the right default.

## Rate Limits

- 5,000 requests per hour per token
- 250 requests per minute burst
- Exceeded → `429 Too Many Requests`. Backoff and honor `RateLimit-Reset` header.

## Common Response Shapes

**Success:** resource name as the top-level key.
```json
{ "droplet": { "id": 123, "name": "web-01", ... } }
```

**Error:**
```json
{ "id": "unauthorized", "message": "Unable to authenticate you" }
```

**Async operations** (resize, snapshot, etc.) return a `200` with an `action` object that has its own ID. Poll `/v2/actions/{id}` until `status == "completed"`.

## IDs

- Numeric integers for most resources (droplets, images, actions, SSH keys)
- UUIDs for newer resources (apps, databases, VPCs, load balancers, CDN endpoints)
- Slugs for some (regions, sizes, images)

Don't assume a type — inspect the field.

## Timestamps

ISO 8601 UTC: `2026-04-15T14:30:00Z`.

## Region Slugs

| UI Name | API Slug | App Platform Slug |
|---|---|---|
| New York 1 | `nyc1` | `nyc` |
| New York 3 | `nyc3` | `nyc` |
| San Francisco 3 | `sfo3` | `sfo` |
| Toronto 1 | `tor1` | `tor` |
| Amsterdam 3 | `ams3` | `ams` |
| Frankfurt 1 | `fra1` | `fra` |
| London 1 | `lon1` | `lon` |
| Bangalore 1 | `blr1` | `blr` |
| Singapore 1 | `sgp1` | `sgp` |
| Sydney 1 | `syd1` | `syd` |

Region availability differs by product. Managed databases and DOKS aren't in every region — check the control panel when provisioning.

## Preferred Tool Selection

1. **MCP tools** (`mcp__digitalocean__*`) — preferred for anything they cover
2. **`doctl` CLI** — official CLI; great for scripting and idempotent scenarios
3. **Raw HTTP** — fallback for operations not yet in MCP, or for bulk queries

## Services Not in the MCP (as of this writing)

Some operations still require raw HTTP or `doctl`:

- DNSSEC toggles for domains
- Detailed metric/graph queries (the "Insights" MCP covers alerts and uptime only)
- Bare metal provisioning
- GPU Droplets (Paperspace line)
- Volumes (block storage attached to Droplets)
- Certificates (ACME / custom upload)
- Reserved IPv6 blocks

For these, curl against `api.digitalocean.com/v2` with the PAT.
