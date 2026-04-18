---
name: ionos-dns-management
description: Manage DNS records on IONOS via the IONOS Hosting DNS API. Use this skill whenever the user wants to view, create, update, or delete DNS records for a domain hosted on IONOS, or when redirecting a domain to a new hosting provider (such as Netlify, Vercel, Cloudflare, or DigitalOcean). Triggers include any mention of "DNS", "domain records", "point domain to", "redirect domain", "CNAME", "A record", "MX record", "nameservers", or "IONOS" in the context of domain or DNS management. Also triggers when another skill (like netlify-landing-page-deploy) needs DNS records updated as a downstream step. This skill handles listing zones, reading existing records, creating/updating/deleting individual records, and performing bulk record replacement. It does NOT handle domain registration, domain transfer, or SSL certificate provisioning — those are separate concerns.
---

# IONOS DNS Management

Manage DNS zones and records on IONOS-hosted domains via the IONOS Hosting DNS REST API. This skill provides the agent with the ability to read, create, update, and delete DNS records programmatically — the critical bridge between deploying a site (e.g., on Netlify) and making it reachable at a custom domain.

## Scope

This skill covers DNS record management for domains whose DNS is hosted on IONOS. Specifically:

- **In scope:** Listing zones, reading records, creating records, updating records, deleting records, bulk record replacement, and validating DNS propagation
- **Out of scope:** Domain registration, domain transfers between registrars, SSL/TLS certificate management, email hosting configuration beyond MX records, and DNSSEC key management

## Prerequisites

1. **IONOS API credentials** — A Public Prefix and Secret, generated at `https://developer.hosting.ionos.com/keys`
2. **Environment variables** configured on the agent host:
   - `IONOS_API_PREFIX` — The public prefix portion of the API key
   - `IONOS_API_SECRET` — The secret portion of the API key
3. **The domain's DNS must be managed by IONOS** — If the domain uses external nameservers, IONOS API calls will succeed but changes won't be visible on the internet

See `SETUP.md` for step-by-step credential provisioning.

## API Reference

The IONOS Hosting DNS API lives at `https://api.hosting.ionos.com/dns/v1`. Read `references/ionos-api-reference.md` for the complete endpoint reference, request/response formats, and curl examples.

### Authentication

Every request requires the `X-API-Key` header with the prefix and secret joined by a dot:

```
X-API-Key: <prefix>.<secret>
```

The prefix and secret should be read from environment variables at runtime, never hardcoded.

```bash
curl -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  https://api.hosting.ionos.com/dns/v1/zones
```

## Operational Workflows

### Workflow 1: Inventory Existing Records

Before making any changes, always snapshot the current state. This protects against accidental data loss.

1. **List all zones** — `GET /zones` to find the zone ID for the target domain
2. **Get zone details** — `GET /zones/{zoneId}` to retrieve all records
3. **Present the snapshot** — Show the user a table of current records (name, type, content, TTL, priority) before proposing changes
4. **Save a backup** — Store the full record set as JSON so it can be restored if something goes wrong

### Workflow 2: Point Domain to Netlify

This is the primary workflow for connecting a Netlify-deployed site to a custom domain. Use this after a successful `netlify-landing-page-deploy`.

1. **Inventory existing records** (Workflow 1)
2. **Identify records to change:**
   - The apex domain (`@` or `example.com`) needs an `A` record or `ALIAS` record pointing to Netlify's load balancer IP: `75.2.60.5`
   - The `www` subdomain needs a `CNAME` record pointing to the Netlify site: `<site-name>.netlify.app`
3. **Check for conflicting records:**
   - If an existing `A` record exists for the apex, it must be updated (not duplicated)
   - If an existing `CNAME` exists for `www`, it must be updated
   - CNAME records cannot coexist with other record types at the same name — if there's an `A` record at `www`, delete it before adding the CNAME
4. **Apply changes** — Update or create the necessary records
5. **Preserve non-deployment records** — Do NOT touch MX records, TXT records (SPF, DKIM, DMARC), or any records unrelated to the web deployment. This is critical — accidentally deleting MX records will break email.
6. **Verify** — After changes, use `dig` or `nslookup` to confirm records resolve correctly (note: propagation can take up to 48 hours, but typically 5-30 minutes)
7. **Configure custom domain on Netlify** — After DNS records are set, use the Netlify MCP to add the custom domain to the Netlify site so it can provision the SSL certificate

See `docs/netlify-pointing.md` for the complete end-to-end sequence with concrete curl commands.

### Workflow 3: Create or Update Individual Records

For targeted record changes (adding a TXT record for verification, updating an MX record, etc.):

1. **Inventory existing records** (Workflow 1)
2. **Check for conflicts** — Particularly CNAME exclusivity rules
3. **Apply the change** — Use `POST` to create or `PUT` to update
4. **Confirm** — Read back the record to verify it was applied

### Workflow 4: Bulk Record Replacement

Use with extreme caution. This replaces ALL records in a zone.

1. **Inventory existing records** (Workflow 1)
2. **Present the complete proposed record set** to the user for confirmation
3. **Require explicit user confirmation** before executing — this is a destructive operation
4. **Apply** — `PUT /zones/{zoneId}` with the full record set
5. **Verify** — Read back the zone to confirm all records are correct

**Warning:** If this operation omits records (like MX or TXT), those records will be deleted. Always include every record that should exist in the zone.

## Safety Rules

These rules are non-negotiable. The agent must follow them for every DNS operation.

1. **Always snapshot before modifying.** Before any create/update/delete, retrieve and store the full current record set. Present it to the user.

2. **Never delete MX records without explicit user instruction.** MX records control email delivery. Accidentally removing them will cause email to bounce. If a workflow would affect MX records, stop and ask.

3. **Never use bulk PUT without user confirmation.** The `PUT /zones/{zoneId}` endpoint replaces ALL records. One missing record in the payload means that record is deleted from DNS. Always present the full proposed set and require a "yes, proceed" from the user.

4. **Respect CNAME exclusivity.** A CNAME record at a given name cannot coexist with any other record type at that same name (RFC 1034). Before creating a CNAME, check for and remove conflicting records at that name. Before creating a non-CNAME record, check that no CNAME exists at that name.

5. **Preserve TTL unless instructed otherwise.** Default TTL is 3600 (1 hour). When updating records, carry forward the existing TTL unless the user specifies a different value.

6. **Never expose API credentials.** The prefix and secret must be read from environment variables. Never log them, display them, or include them in output.

## Record Types Quick Reference

| Type | Purpose | Example Content | Notes |
|------|---------|----------------|-------|
| A | IPv4 address | `75.2.60.5` | Use for apex domain pointing to Netlify |
| AAAA | IPv6 address | `2600:1f18:...` | IPv6 equivalent of A |
| CNAME | Alias to another hostname | `mysite.netlify.app` | Cannot exist at apex alongside other records |
| MX | Mail server | `10 mail.example.com` | Has priority field; do not delete without explicit instruction |
| TXT | Arbitrary text | `v=spf1 include:...` | Used for SPF, DKIM, DMARC, domain verification |
| NS | Nameserver delegation | `ns1.ionos.com` | Rarely modified; changing breaks DNS |
| SRV | Service location | `0 5 5060 sip.example.com` | Has priority, weight, port |
| CAA | Certificate authority auth | `0 issue "letsencrypt.org"` | Controls which CAs can issue certs |
| ALIAS | Apex alias (IONOS-specific) | `mysite.netlify.app` | Like CNAME but works at apex; preferred for Netlify apex |

## Netlify-Specific DNS Patterns

When pointing a domain to Netlify, use these patterns:

**Apex domain (`example.com`):**
- Preferred: `ALIAS` record → `<site-name>.netlify.app` (if IONOS supports ALIAS; check first)
- Fallback: `A` record → `75.2.60.5` (Netlify's load balancer)

**WWW subdomain (`www.example.com`):**
- `CNAME` record → `<site-name>.netlify.app`

**After DNS is configured:**
- Add the custom domain in Netlify (via MCP or dashboard)
- Netlify will automatically provision a Let's Encrypt SSL certificate once DNS propagates

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `401 Unauthorized` | Invalid or expired API key | Check `IONOS_API_PREFIX` and `IONOS_API_SECRET` env vars |
| `404 Not Found` | Zone or record ID doesn't exist | Re-list zones to get correct IDs |
| `409 Conflict` | Record conflicts with existing record | Check for CNAME exclusivity violations or duplicate records |
| `422 Unprocessable` | Malformed record data | Validate record type, content format, and TTL |
| DNS not propagating | Nameservers not pointing to IONOS | Verify domain's NS records at registrar level |

## Integration with Other Skills

- **`netlify-landing-page-deploy`** — After deploying a site, this skill configures DNS to point the custom domain to Netlify
- **`netlify-dns`** — Sibling skill for when DNS is hosted *on Netlify* instead of IONOS
- **`digitalocean-management`** (future) — Same pattern but with DigitalOcean IP addresses and CNAME targets
- Other DNS provider skills (Cloudflare, Route 53, etc.) will share the same workflow patterns but use different APIs; this skill is IONOS-specific

## API Reference (docs/)

Per-topic references for the IONOS DNS API this skill touches.

- [docs/zones.md](docs/zones.md) — Zone object, listing, inspection, bulk PUT semantics
- [docs/records.md](docs/records.md) — Record object, CRUD endpoints, per-type content format
- [docs/netlify-pointing.md](docs/netlify-pointing.md) — Full end-to-end walkthrough for pointing a domain at Netlify

Pipeline-time detailed endpoint reference lives at `references/ionos-api-reference.md`.

## What This Skill Does NOT Do

- **Domain registration or transfer** — Out of scope; handle through IONOS dashboard
- **SSL certificate management** — Netlify handles this automatically; other providers may need separate skills
- **Email hosting configuration** — Beyond setting MX records, email setup is out of scope
- **DNSSEC management** — The IONOS Hosting API does not expose DNSSEC operations
- **Nameserver changes** — Changing which nameservers a domain uses is done at the registrar level, not via DNS API
