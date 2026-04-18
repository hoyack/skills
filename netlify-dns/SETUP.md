# Netlify DNS Setup

This skill shares credentials and transport with `netlify-landing-page-deploy` — if that skill works, this one works.

## Prerequisites

1. `netlify-landing-page-deploy` is already set up (PAT + MCP registered in `~/.mcp.json`)
2. A Netlify project exists (create one via `netlify-landing-page-deploy` first)
3. A domain under your control (either its registrar is accessible, or its DNS provider is accessible)

## No separate MCP server needed

DNS operations aren't covered by `@netlify/mcp` as of v1.15.1 — this skill uses direct HTTP with the PAT. Export the PAT before running commands:

```bash
export NETLIFY_PERSONAL_ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.mcp.json'))['mcpServers']['netlify']['env']['NETLIFY_PERSONAL_ACCESS_TOKEN'])")
```

Or pull from whichever vault/env you use.

## Verify credentials work

```bash
curl -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  https://api.netlify.com/api/v1/dns_zones
```

Empty array `[]` means no zones yet (expected initially). Non-empty means existing zones — inspect before making changes.

## Sanity-check the target project exists

```bash
curl -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  https://api.netlify.com/api/v1/sites | python3 -m json.tool | grep -E '"(name|site_id|id|custom_domain)":'
```

You'll need the `site_id` (UUID) to attach a custom domain.

## Tools that help

Not required, but handy:

- `dig` — verify DNS propagation (`dig @8.8.8.8 example.com NS +short`)
- `netlify` CLI — `npm install -g netlify-cli`; mainly useful for local dev, but can list DNS zones too
- `jq` or `python3 -m json.tool` — pretty-print JSON responses

## Safety

- Never delete a zone without confirming the user understands DNS will stop resolving immediately
- Before bulk changes, list current records and save a backup: `curl ... > /tmp/zone-backup-$(date +%s).json`
- Lower TTLs (to 300s) at least 24h before migrations so rollback is fast
