# Zone Object Reference

A **zone** in Cloudflare is a DNS zone == one domain. Each zone has a UUID-style ID used to scope all record operations.

## Object Shape

From `GET /zones/{zone_id}`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Zone UUID — used in every record URL |
| `name` | string | Domain (`example.com`, no trailing dot) |
| `status` | string | `active`, `pending`, `initializing`, `moved`, `deleted` |
| `paused` | bool | If true, all Cloudflare features suspended (records still resolve) |
| `type` | string | `full` (authoritative) or `partial` (CNAME-setup zone; rare) |
| `name_servers` | string[] | The two Cloudflare nameservers the domain is delegated to |
| `original_name_servers` | string[] | Nameservers seen at the time of zone creation |
| `original_registrar` | string | Where the domain was registered when added |
| `activated_on` | ISO 8601 | When the zone went active |
| `plan` | object | `{ id, name, price, ... }` — Free/Pro/Business/Enterprise |
| `account` | object | Owning account |

## Listing Zones

```bash
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?per_page=50"
```

### Filters

- `?name=example.com` — exact domain match (fastest way to find a specific zone's ID)
- `?status=active` — operational zones only
- `?account.id=<account-uuid>` — for multi-account tokens

### Pagination

- `per_page` max is 50 for zones
- Response includes `result_info.total_pages`; loop through pages when necessary

## Zone Status Meanings

| Status | Meaning |
|---|---|
| `active` | Fully operational — nameservers confirmed, serving traffic |
| `pending` | Zone added but nameservers not yet pointed to Cloudflare |
| `initializing` | Transient state during zone setup |
| `moved` | Domain's nameservers were moved away from Cloudflare — zone is effectively inactive |
| `deleted` | Scheduled for removal; usually invisible in list |

**If `status == "pending"`, DNS record writes succeed against the API but nothing resolves publicly** — because recursive resolvers still ask the old nameservers. The fix is at the registrar, not the Cloudflare API.

## Nameserver Verification

Check that a zone's advertised nameservers match what the registrar is publishing:

```bash
# What Cloudflare expects:
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  | python3 -c "import json,sys; z=json.load(sys.stdin)['result'][0]; print('cf expects:', z['name_servers'])"

# What the internet actually sees:
dig @8.8.8.8 example.com NS +short
```

When the two match, Cloudflare flips the zone to `active` (may take up to ~24 hours after NS change).

## Zone Creation (out of scope for this skill)

Zones are typically added via the Cloudflare dashboard onboarding flow, which also guides the registrar nameserver change. The API can create zones (`POST /zones`) but the delegation step still has to happen externally, so it's rarely worth automating.

## CNAME Flattening Support

`GET /zones/{zone_id}` includes a `cname_flattening` field:
- `flatten_at_root` — only the apex is flattened (default on Free)
- `flatten_all` — every CNAME is flattened (available on paid plans)

The feature is what makes `example.com CNAME example.netlify.app` legal. See `docs/records.md` and `docs/netlify-pointing.md` for how this shapes the point-to-Netlify pattern.

## Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| `GET /zones` returns empty | Token scoped to specific zones that don't exist, or token lacks `Zone:Read` |
| Zone stuck in `pending` | Registrar nameservers not updated yet; dig NS to confirm |
| Zone shows `moved` | Registrar pointed nameservers away from Cloudflare; records will survive in the zone but not resolve |
| Zone exists but record writes 403 | Token has `Zone:Read` but not `Zone:DNS:Edit` |
