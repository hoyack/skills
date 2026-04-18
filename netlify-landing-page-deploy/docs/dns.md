# DNS Reference

Netlify can manage DNS as an authoritative nameserver (NS records delegated to `dns{1-4}.p0{x}.nsone.net`) or attach to externally-managed DNS via CNAME. This doc covers the Netlify-managed case; for IONOS/Cloudflare-managed records pointing at Netlify, see those skills.

**This doc is a shared reference used by both `netlify-landing-page-deploy` and the sibling `netlify-dns` skill.**

## Concepts

- **DNS Zone** — a domain Netlify authoritatively serves DNS for (e.g., `example.com`)
- **DNS Record** — an individual A/AAAA/CNAME/MX/TXT/etc. entry inside a zone
- **Custom Domain** — a domain attached to a project; the domain can live in any DNS provider
- **Domain Alias** — additional domains attached to the same project (redirects or primary)

Attaching a custom domain to a project and creating a DNS zone are **two separate operations**. You can have:
- A project with a custom domain whose DNS lives at another provider (most common)
- A Netlify-managed DNS zone without any project attached yet
- Both (zone managed by Netlify AND project has the matching custom domain)

## DNS Zone Object

From `GET /api/v1/dns_zones`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Zone ID |
| `name` | string | Domain (`example.com`) |
| `account_id` | string | Owning team |
| `site_id` | UUID / null | Associated project, if any |
| `user_id` | string | Creator |
| `created_at` | ISO 8601 | |
| `updated_at` | ISO 8601 | |
| `records` | array | Inline records (sometimes omitted on list views) |
| `dns_servers` | string[] | Netlify nameservers to delegate to |
| `errors` | array | Delegation / propagation issues |
| `supported_record_types` | string[] | A, AAAA, CNAME, MX, TXT, NS, SRV, CAA, etc. |

## DNS Record Object

From `GET /api/v1/dns_zones/:zone_id/dns_records`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Record ID |
| `hostname` | string | Full name (`www.example.com`) |
| `type` | string | `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`, `SRV`, `CAA` |
| `value` | string | Record data (IP for A, target for CNAME, etc.) |
| `ttl` | int | Seconds; null = Netlify default (3600) |
| `priority` | int | For MX and SRV records |
| `weight` | int | SRV only |
| `port` | int | SRV only |
| `flag` | int | CAA only |
| `tag` | string | CAA only |
| `dns_zone_id` | string | Parent zone |
| `site_id` | UUID / null | Associated project |
| `managed` | bool | True if Netlify auto-manages (e.g., the A record pointing at the load balancer) |

## Common Operations

### List DNS zones

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones"
```

### Create a DNS zone

```bash
curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"name": "example.com", "account_slug": "team-slug"}' \
  "https://api.netlify.com/api/v1/dns_zones"
```

After creation, the response includes `dns_servers` — update the domain's registrar to delegate to those nameservers.

### Get a zone with its records

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID"
```

### List records in a zone

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records"
```

### Create a DNS record

```bash
curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "hostname": "www.example.com",
    "value": "my-project.netlify.app",
    "ttl": 3600
  }' \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records"
```

For an apex domain (`example.com` itself) pointing at Netlify, Netlify auto-creates an ALIAS/ANAME-style A record when you attach a custom domain to a project in a Netlify-managed zone.

### Delete a record

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records/$RECORD_ID"
```

### Delete a zone

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID"
```

## Attach a Custom Domain to a Project

### Scenario A — Netlify-managed DNS (nameservers delegated)

1. Create DNS zone for `example.com` (above)
2. Update registrar nameservers to the `dns_servers` returned by the zone creation
3. Set `custom_domain` on the project:
   ```bash
   curl -X PATCH -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
     -d '{"custom_domain": "example.com"}' \
     "https://api.netlify.com/api/v1/sites/$SITE_ID"
   ```
4. Netlify creates the A/ALIAS record automatically; SSL provisions within minutes.

### Scenario B — External DNS (IONOS, Cloudflare, etc.)

1. At the external provider, create:
   - Apex `A` or `ALIAS`/`ANAME` → `75.2.60.5` (Netlify load balancer), OR Netlify's dedicated IP if assigned
   - `www` `CNAME` → `<project>.netlify.app`
2. Set `custom_domain` on the project (same PATCH as above)
3. Netlify polls for DNS, then provisions SSL via Let's Encrypt

Netlify's recommended apex target is a dedicated IP or the default load-balancer IP. Check project → **Domain management** for the current value; hard-coding IPs goes stale.

## SSL

Automatic via Let's Encrypt. No API action needed in most cases. Inspect status:

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl"
```

Force re-provisioning:

```bash
curl -X POST -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl"
```

Fields of interest on the response:
- `state` — `pending`, `issued`, `issuing`, `errored`
- `expires_at` — cert expiration (auto-renewed)
- `domains` — domains covered by the cert

## MCP Coverage

As of `@netlify/mcp` v1.15.1, DNS is NOT covered by MCP tools. All DNS operations go through raw HTTP. The forthcoming `netlify-dns` skill wraps the REST calls above into a consistent interface.

## Common Record Templates

### Apex + www pointing at Netlify (external DNS)

```
example.com.     A      75.2.60.5
www.example.com. CNAME  my-project.netlify.app.
```

### Verification / ownership TXT records

Netlify may ask for a TXT record during domain verification:

```
_netlify.example.com. TXT "<verification-token>"
```

### Common email/SaaS records (don't lose these when migrating)

```
example.com.     MX  10 mail.example.com.
example.com.     TXT "v=spf1 include:_spf.google.com ~all"
_dmarc.example.com. TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
```

When moving DNS to Netlify, enumerate the existing records at the source provider first and re-create them in the Netlify zone before flipping nameservers.

## Propagation

- TTL controls how long resolvers cache old values
- Lower TTL to 300s a day before any migration, raise back to 3600s after
- Use `dig @8.8.8.8 example.com NS` to verify nameserver delegation
- Use `dig @dns1.p01.nsone.net example.com A` to ask Netlify's nameserver directly (bypasses resolver cache)
