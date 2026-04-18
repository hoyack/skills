---
name: cloudflare-dns-management
description: Manage DNS records on Cloudflare via the Cloudflare MCP server or Cloudflare API v4. Use this skill whenever the user wants to view, create, update, or delete DNS records for a domain managed by Cloudflare, or when redirecting a domain on Cloudflare to a hosting provider (such as Netlify, DigitalOcean, Vercel, or any origin server). Triggers include any mention of "Cloudflare DNS", "Cloudflare", "CF DNS", "orange cloud", "proxied", "CNAME flattening", or general DNS management terms like "DNS records", "A record", "CNAME", "point domain to" when the domain is known to be on Cloudflare. Also triggers when another skill (like netlify-landing-page-deploy or digitalocean-management) needs DNS records updated on a Cloudflare-managed domain. This skill handles listing zones, reading existing records, creating/updating/deleting individual records, batch operations, and managing Cloudflare-specific features like proxy status (orange/grey cloud). It does NOT handle Cloudflare Workers, Pages, R2, WAF, or other non-DNS Cloudflare services. It does NOT handle DNS for domains on other providers — use ionos-dns-management, or the appropriate provider skill for those.
---

# Cloudflare DNS Management

Manage DNS zones and records on Cloudflare-managed domains via the official Cloudflare MCP server or direct Cloudflare API v4 calls. Cloudflare's DNS has a major advantage over most providers: it supports **CNAME flattening at the apex**, meaning you can point a bare domain (`example.com`) to a hostname like `mysite.netlify.app` without needing an A record or ALIAS workaround.

## Scope

This skill covers DNS record management for domains whose nameservers point to Cloudflare. Specifically:

- **In scope:** Listing zones, reading records, creating/updating/deleting records, batch record operations, managing proxy status (orange cloud vs. grey cloud), and CNAME flattening at apex
- **Out of scope:** Cloudflare Workers, Pages, R2, D1, WAF rules, firewall rules, Zero Trust, SSL certificate configuration, Page Rules, and any non-DNS Cloudflare product. Also out of scope: domain registration/transfer and DNSSEC key management

## Prerequisites

1. **Cloudflare API Token** — Generated at `https://dash.cloudflare.com/profile/api-tokens` with `Zone:DNS:Edit` permission for the target zones
2. **Environment variable** configured: `CLOUDFLARE_API_TOKEN`
3. **The domain's nameservers must point to Cloudflare** — Typically `*.ns.cloudflare.com`. If nameservers haven't been changed at the registrar, Cloudflare API calls will succeed but records won't resolve publicly.

See `SETUP.md` for step-by-step credential provisioning.

## MCP Server Configuration

Cloudflare offers an official MCP server that covers the **entire** Cloudflare API — over 2,500 endpoints — using only two tools: `search()` and `execute()`. This "Code Mode" approach consumes approximately 1,000 tokens regardless of how many API endpoints exist, making it extremely efficient.

### Remote MCP Server (Recommended)

The simplest setup — no local installation required:

```json
{
  "mcpServers": {
    "cloudflare": {
      "url": "https://mcp.cloudflare.com/mcp",
      "headers": {
        "Authorization": "Bearer <CLOUDFLARE_API_TOKEN>"
      }
    }
  }
}
```

This gives the agent access to the full Cloudflare API via two tools:

- **`search()`** — Search the Cloudflare OpenAPI spec for relevant endpoints. The agent writes JavaScript to filter `spec.paths` and find the endpoints it needs.
- **`execute()`** — Execute an API call against the Cloudflare API. The agent writes JavaScript using `cloudflare.request()` to make the actual call.

### Local MCP Server (Alternative)

If you prefer running locally, use `mcp-remote` to proxy the remote server:

```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.cloudflare.com/sse"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "<stored-securely-in-env>"
      }
    }
  }
}
```

### API Token Scopes

For DNS-only operations, create a token with these permissions:
- **Zone : DNS : Edit** — Read and write DNS records
- **Zone : Zone : Read** — List zones (needed to find zone IDs)

For broader operations, add scopes as needed. The MCP server respects the token's permissions.

## Cloudflare-Specific Concepts

### Proxy Status (Orange Cloud / Grey Cloud)

Cloudflare DNS records have a `proxied` field that controls whether traffic flows through Cloudflare's network:

- **`proxied: true` (orange cloud)** — Traffic flows through Cloudflare's CDN, WAF, and DDoS protection. Cloudflare's IP addresses are returned in DNS lookups instead of the origin's IP. Only works for HTTP/HTTPS traffic (A, AAAA, CNAME records).
- **`proxied: false` (grey cloud)** — DNS-only mode. The origin's actual IP/hostname is returned. Required for non-HTTP services (MX, SRV, etc.) and any record type that doesn't support proxying.

**When pointing to Netlify:** Set `proxied: false` (grey cloud). Netlify needs to see its own hostname in the request to route correctly and provision SSL. Proxying through Cloudflare will interfere with Netlify's SSL provisioning.

**When pointing to DigitalOcean App Platform:** Same — `proxied: false` initially, until the app is confirmed working. Proxying can be enabled later if desired.

See `docs/proxy-mode.md` for the full decision matrix.

### CNAME Flattening

Cloudflare supports CNAME records at the zone apex (bare domain). Most DNS providers prohibit this because CNAME records technically conflict with SOA and NS records at the same name. Cloudflare resolves this by "flattening" the CNAME — it follows the CNAME chain and returns the resulting A/AAAA records instead.

This means you can do:
```
example.com  CNAME  mysite.netlify.app  (proxied: false)
```

No need for A records with hardcoded IPs or ALIAS/ANAME workarounds. This is the **preferred** approach for pointing apex domains to Netlify, DigitalOcean, or any other hostname-based hosting.

### TTL

- TTL `1` means "automatic" — Cloudflare chooses an appropriate TTL
- For proxied records, TTL is always automatic regardless of what you set
- For DNS-only records, TTL can be set between 60 and 86400 seconds (1 minute to 24 hours)
- Enterprise zones allow a minimum TTL of 30 seconds

## Operational Workflows

### Workflow 1: Inventory Existing Records

Before any changes, snapshot the current state.

1. **Find the zone ID** — List zones, find the target domain, note the zone ID
2. **List all records** — Retrieve every record in the zone
3. **Present the snapshot** — Show the user a table: name, type, content, TTL, proxied status
4. **Save a backup** — Store the full record set as JSON for potential restoration

### Workflow 2: Point Domain to Netlify

The primary cross-skill workflow after `netlify-landing-page-deploy`.

1. **Inventory existing records** (Workflow 1)
2. **Configure apex domain:**
   - Create or update a CNAME record: `example.com` → `<site-name>.netlify.app` with `proxied: false`
   - Cloudflare will flatten this automatically — no A record needed
   - Delete any existing A/AAAA records for the apex that would conflict
3. **Configure www subdomain:**
   - Create or update a CNAME record: `www.example.com` → `<site-name>.netlify.app` with `proxied: false`
4. **Preserve non-deployment records** — Do NOT touch MX, TXT (SPF/DKIM/DMARC), or any records unrelated to web hosting
5. **Verify** — Use `dig` or `nslookup` to confirm records resolve
6. **Add custom domain on Netlify** — Use the Netlify MCP to register the domain so Netlify provisions SSL

**Critical:** Set `proxied: false` for Netlify deployments. Cloudflare's proxy will break Netlify's automatic SSL provisioning.

See `docs/netlify-pointing.md` for the concrete end-to-end sequence.

### Workflow 3: Point Domain to DigitalOcean

After deploying via `digitalocean-management`:

1. **Inventory existing records** (Workflow 1)
2. **For App Platform:** Create CNAME records pointing to the `.ondigitalocean.app` hostname, `proxied: false`
3. **For Droplets:** Create A/AAAA records pointing to the Droplet's IP address. `proxied: true` is fine here if you want Cloudflare CDN/WAF.
4. **Preserve non-deployment records**

### Workflow 4: Create or Update Individual Records

1. **Inventory existing records** (Workflow 1)
2. **Check for conflicts** — CNAME exclusivity, duplicate records
3. **Apply** — POST to create, PUT to overwrite, PATCH to partial-update
4. **Confirm** — Read back the record

### Workflow 5: Batch Record Operations

Cloudflare supports batch DNS record operations (POST, PUT, PATCH, DELETE) in a single API call via the `/batch` endpoint. Free plans support up to 200 changes per batch; paid plans up to 3,500.

1. **Inventory existing records** (Workflow 1)
2. **Compose the batch** — Collect all creates, updates, and deletes into a single request
3. **Present the batch to the user** for confirmation
4. **Execute** — `POST /zones/{zone_id}/dns_records/batch`
5. **Verify** — Read back records to confirm

Batch operations are atomic — either all changes succeed or none do. This is safer than individual calls for large changes.

See `docs/batch-operations.md` for patterns and limits.

## Safety Rules

1. **Always snapshot before modifying.** Retrieve and present the current record set before any changes.

2. **Never delete MX records without explicit user instruction.** MX records control email. Accidental deletion breaks email delivery.

3. **Set `proxied: false` when pointing to Netlify or similar PaaS.** Proxying interferes with SSL provisioning on these platforms. The user can enable proxying later once everything is confirmed working, but only if they understand the implications.

4. **Respect CNAME exclusivity.** A CNAME at a name cannot coexist with other record types at that same name (except at the apex where Cloudflare handles flattening). Before creating a CNAME, remove conflicting records. Before creating a non-CNAME, check for existing CNAMEs.

5. **Preserve TTL unless instructed otherwise.** When updating records, keep the existing TTL. Default to `1` (automatic) for new records.

6. **Never expose API tokens.** Read from environment variables only. Never log, display, or include in output.

7. **Use batch operations for large changes.** When modifying more than 3-4 records, prefer the batch endpoint. It's atomic and faster.

## Record Types Quick Reference

| Type | Purpose | Proxiable | Example Content |
|------|---------|-----------|----------------|
| A | IPv4 address | Yes | `75.2.60.5` |
| AAAA | IPv6 address | Yes | `2600:1f18::1` |
| CNAME | Alias to hostname | Yes | `mysite.netlify.app` |
| MX | Mail server | No | `10 mail.example.com` |
| TXT | Arbitrary text | No | `v=spf1 include:...` |
| NS | Nameserver | No | `ns1.cloudflare.com` |
| SRV | Service location | No | `0 5 5060 sip.example.com` |
| CAA | Certificate authority | No | `0 issue "letsencrypt.org"` |
| PTR | Reverse DNS | No | `host.example.com` |

**Proxiable:** Only A, AAAA, and CNAME records can be proxied (orange cloud). All other types are always DNS-only.

## Netlify-Specific DNS Patterns on Cloudflare

Cloudflare's CNAME flattening makes the setup cleaner than on most providers:

**Apex domain (`example.com`):**
```
example.com  CNAME  <site-name>.netlify.app  proxied: false  TTL: auto
```

**WWW subdomain (`www.example.com`):**
```
www.example.com  CNAME  <site-name>.netlify.app  proxied: false  TTL: auto
```

Both use CNAME. No A records, no IP addresses to hardcode. If Netlify changes their infrastructure IPs, nothing breaks.

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `401 Unauthorized` | Invalid or expired API token | Check `CLOUDFLARE_API_TOKEN` |
| `403 Forbidden` | Token lacks required scope | Regenerate with `Zone:DNS:Edit` and `Zone:Zone:Read` |
| `404 Not Found` | Zone or record ID doesn't exist | Re-list zones/records |
| `409 Conflict` | Record conflicts (CNAME exclusivity) | Remove conflicting records first |
| `1004 DNS Validation Error` | Invalid record data | Check type, content format, name |
| DNS not resolving | Nameservers not pointed to Cloudflare | Verify NS records at registrar |
| SSL errors after pointing to Netlify | `proxied: true` on Netlify-targeted records | Set `proxied: false` |

## Integration with Other Skills

- **`netlify-landing-page-deploy`** — After deploying, this skill configures Cloudflare DNS to point to Netlify
- **`digitalocean-management`** — After deploying on DO, this skill configures DNS to point to the DO app/Droplet
- **`ionos-dns-management`** — Sibling skill for IONOS-hosted domains. Same workflow patterns, different API.
- **`netlify-dns`** — Sibling skill for when DNS is on Netlify itself
- Future DNS provider skills (Route 53, Google Cloud DNS, etc.) will follow the same structure

## API Reference (docs/)

Per-topic references for the Cloudflare DNS API.

- [docs/zones.md](docs/zones.md) — Zone object, listing, nameserver verification, zone status
- [docs/records.md](docs/records.md) — Record CRUD (POST/GET/PUT/PATCH/DELETE), per-type content format, CNAME exclusivity, `data` vs `content` fields
- [docs/batch-operations.md](docs/batch-operations.md) — `/batch` endpoint, atomic semantics, plan limits, safe patterns
- [docs/proxy-mode.md](docs/proxy-mode.md) — Orange vs. grey cloud, SSL-mode interactions, decision matrix per destination
- [docs/netlify-pointing.md](docs/netlify-pointing.md) — Full end-to-end walkthrough for pointing a Cloudflare domain at Netlify

Pipeline-wide endpoint reference: `references/cloudflare-dns-api-reference.md`.

## What This Skill Does NOT Do

- **Cloudflare Workers, Pages, R2, D1** — Use the full Cloudflare MCP server or a dedicated Cloudflare platform skill
- **WAF, firewall rules, Page Rules** — Security configuration is out of scope
- **SSL/TLS certificate management** — Cloudflare handles SSL automatically for proxied records; Netlify handles it for non-proxied
- **Domain registration or transfer** — Handle through Cloudflare Registrar dashboard
- **DNSSEC management** — Handled through the Cloudflare dashboard
- **DNS for domains on other providers** — Use the appropriate provider skill
