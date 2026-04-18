---
name: netlify-dns
description: Manage DNS zones and records on Netlify — create and delete zones, add/update/delete A/AAAA/CNAME/MX/TXT/SRV/CAA records, attach custom domains to Netlify projects, and verify propagation. Triggers when the user wants to "point a domain at Netlify", "set up DNS", "add a DNS record", "connect a custom domain", "move DNS to Netlify", or mentions a Netlify-hosted project + a domain. Use this skill AFTER `netlify-landing-page-deploy` has deployed the project. Does NOT manage DNS at IONOS, Cloudflare, or other providers (those get their own skills). Does NOT provision SSL certificates explicitly (Netlify auto-provisions via Let's Encrypt once DNS resolves).
---

# Netlify DNS

Manage DNS for projects deployed to Netlify. Covers both Netlify-managed zones (delegated nameservers) and attaching custom domains whose DNS lives at an external provider.

**Status:** Skill is scaffolded but **unverified** — no real DNS zones exist on the current Netlify account as of authoring. First real use should run read-side operations first and sanity-check outputs against the dashboard before making destructive changes.

## Scope

This skill handles:

- Listing, creating, and deleting DNS zones on Netlify's nameservers
- CRUD on DNS records within a Netlify-managed zone (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS)
- Attaching a custom domain or domain alias to a Netlify project
- Verifying SSL certificate state on a project
- Diagnosing propagation issues (`dig` against Netlify's authoritative nameservers and public resolvers)

Out of scope (see respective skills):
- **IONOS DNS** — `ionos-dns` (to be built)
- **Cloudflare DNS** — `cloudflare-dns` (to be built)
- **Domain registration / transfers** — Netlify offers this but the API surface is separate; handle manually
- **Static site deploys** — `netlify-landing-page-deploy`

## Prerequisites

1. **Netlify PAT** with account access (same token as `netlify-landing-page-deploy`)
2. **Target domain is resolvable** — you either control the registrar (for nameserver delegation) OR the domain already has Netlify-compatible records at an external DNS provider
3. **A Netlify project exists** that the domain will be attached to (create via `netlify-landing-page-deploy` first)

## MCP Coverage

As of `@netlify/mcp` v1.15.1, **DNS is NOT in the MCP**. Every operation below uses direct HTTP against `https://api.netlify.com/api/v1/`. The PAT from `~/.mcp.json` (or the same env var) is the only credential needed.

```bash
export NETLIFY_PERSONAL_ACCESS_TOKEN=<from ~/.mcp.json>
curl -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" ...
```

## Decision Tree

When a user says "connect `example.com` to my Netlify project":

```
Does Netlify already have a DNS zone for example.com?
├── Yes → Scenario A: Netlify-managed DNS
│         Skip to "Attach Custom Domain to Project"
│
└── No → Ask: should Netlify be authoritative for DNS,
             or will DNS stay at the current provider?
    ├── Netlify authoritative → Scenario A (create zone, delegate nameservers)
    └── External DNS          → Scenario B (add A/CNAME at current provider)
```

## Scenario A — Netlify-Managed DNS

Best when the user has no strong preference, or wants the simplest path and is okay delegating nameservers.

### Step 1: Create the zone

```bash
curl -X POST \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"name": "example.com", "account_slug": "<team-slug>"}' \
  "https://api.netlify.com/api/v1/dns_zones"
```

Response includes `dns_servers` — typically 4 hostnames like `dns1.p01.nsone.net`, `dns2.p02.nsone.net`, etc.

### Step 2: Delegate nameservers at the registrar

Report the 4 nameservers to the user. **They must update these at their domain registrar** (GoDaddy, Namecheap, IONOS, etc.). This is the one step the skill can't automate.

After the user confirms delegation is set, verify:

```bash
dig @8.8.8.8 example.com NS +short
# Should list the Netlify nameservers
```

Propagation: typically under 1 hour; up to 48h worst case.

### Step 3: Create records

For the common apex + www case attached to a Netlify project:

```bash
# Apex: Netlify will auto-create an ALIAS/A record when you attach the custom domain.
# www CNAME:
curl -X POST \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"type": "CNAME", "hostname": "www.example.com", "value": "<project>.netlify.app", "ttl": 3600}' \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records"
```

Preserve any existing email / SaaS records (MX, SPF, DKIM, DMARC) — see `docs/migration-checklist.md`.

### Step 4: Attach the custom domain to the project

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain": "example.com"}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

Netlify auto-provisions SSL within 1–10 minutes once DNS resolves.

## Scenario B — External DNS (IONOS / Cloudflare / etc.)

Best when the user has existing DNS at a provider they want to keep, or when Netlify-authoritative would complicate other services (enterprise email, complex SaaS wiring).

### Step 1: Add records at the external provider

Two records, at the external DNS provider (not Netlify):

```
example.com.       A      75.2.60.5
www.example.com.   CNAME  <project>.netlify.app.
```

The apex IP may vary — check **Netlify dashboard → Project → Domain management → Set up Netlify DNS → Use external DNS** for the current recommended target. Hard-coded IPs go stale.

If the provider supports ALIAS/ANAME/CNAME-at-apex, prefer that pointing at `<project>.netlify.app` over a hardcoded IP.

This step is done at IONOS/Cloudflare/wherever — the future `ionos-dns` / `cloudflare-dns` skills will automate it.

### Step 2: Attach the custom domain to the project

Same PATCH as Scenario A step 4.

### Step 3: Verify

```bash
dig @8.8.8.8 example.com A +short           # expect 75.2.60.5 (or Netlify's load balancer)
dig @8.8.8.8 www.example.com CNAME +short   # expect <project>.netlify.app
curl -I https://example.com                 # expect 200/301, valid cert
```

## Common Operations

### List zones on the account

```bash
curl -H "Authorization: Bearer $TOK" "https://api.netlify.com/api/v1/dns_zones"
```

### Get a zone + records

```bash
curl -H "Authorization: Bearer $TOK" "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID"
curl -H "Authorization: Bearer $TOK" "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records"
```

### Create a record

```bash
curl -X POST \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"type":"TXT","hostname":"example.com","value":"v=spf1 include:_spf.google.com ~all","ttl":3600}' \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records"
```

### Update a record

Netlify's API does not have a direct PATCH for records — **delete then recreate**:

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID/dns_records/$RECORD_ID"
# then POST the new value
```

### Delete a zone

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/dns_zones/$ZONE_ID"
```

⚠️ Deleting a zone orphans DNS for the domain immediately. Confirm with user before running.

### Attach a domain alias (additional domains)

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"domain_aliases": ["www.example.com", "example.net"]}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

### Detach a custom domain

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain": null}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

## SSL

Automatic once DNS resolves. Check status:

```bash
curl -H "Authorization: Bearer $TOK" "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl"
```

Force re-provisioning:

```bash
curl -X POST -H "Authorization: Bearer $TOK" "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl"
```

## Error Handling

| Error | Cause | Action |
|---|---|---|
| `422 Unprocessable Entity` on zone create | Zone already exists for this domain | GET zones, use existing zone ID |
| `409 Conflict` on record create | Duplicate hostname+type combination | Delete existing record first |
| `404` on zone/record delete | Already deleted, or wrong ID | Re-list to get fresh IDs |
| `SSL state: errored` | DNS not yet pointing at Netlify | Wait for propagation; verify with `dig` |
| `SSL state: pending` for >30 min | Likely mixed-content or wrong apex target | Check dashboard for specific error message |
| Site returns 404 after domain attached | Custom domain PATCH not yet applied OR domain not in `domain_aliases` | Re-GET the site and inspect `custom_domain` + `domain_aliases` |

## What This Skill Does NOT Do

- **Register or transfer domains** — use the Netlify dashboard or a registrar
- **Manage DNS at non-Netlify providers** — use the provider-specific DNS skill
- **Issue SSL for domains Netlify doesn't own** — Netlify only provisions for attached custom domains
- **Email hosting** — Netlify is not an MX target; keep or configure a separate mail provider

## See Also

- Shared reference: [../netlify-landing-page-deploy/docs/dns.md](../netlify-landing-page-deploy/docs/dns.md)
- Shared reference: [../netlify-landing-page-deploy/docs/projects.md](../netlify-landing-page-deploy/docs/projects.md) (for `custom_domain` / `domain_aliases` on the project object)
- Prerequisite skill: `netlify-landing-page-deploy` — deploy a project before connecting a domain to it
