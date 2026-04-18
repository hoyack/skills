# DNS Record Reference

A record is an individual RR inside a Cloudflare zone. Each record has a UUID `id` you use to update or delete it directly.

## Object Shape

| Field | Type | Mutable via PATCH | Description |
|---|---|---|---|
| `id` | string | — | Server-assigned UUID |
| `zone_id` | string | — | Parent zone |
| `zone_name` | string | — | Parent zone name |
| `name` | string | yes | FQDN (`www.example.com`). Can be submitted relative (`www`) on create; stored as FQDN |
| `type` | string | yes | `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`, `SRV`, `CAA`, `PTR`, `TLSA`, `SMIMEA`, etc. |
| `content` | string | yes (most types) | Record value — format depends on `type` |
| `data` | object | yes (SRV/CAA/certain types) | Structured value used instead of `content` for some types |
| `priority` | int | yes | Required for MX and (via `data`) SRV |
| `proxied` | bool | yes | Orange vs grey cloud; see `docs/proxy-mode.md` |
| `proxiable` | bool | — | Whether this type is eligible to be proxied |
| `ttl` | int | yes | 1 = automatic; else 60–86400 (30–86400 on Enterprise) |
| `comment` | string | yes | Free-form note; no DNS effect |
| `tags` | string[] | yes | Free-form labels |
| `created_on` | ISO 8601 | — | |
| `modified_on` | ISO 8601 | — | |

### `content` vs `data`

Most record types (A, AAAA, CNAME, MX, TXT, NS, PTR) use the flat `content` field. A few types pack multi-field values into a `data` object:

- **SRV**: `data: { priority, weight, port, target }`
- **CAA**: `data: { flags, tag, value }`
- **TLSA**, **SMIMEA**, **DS**, **NAPTR**, **LOC** — also use `data` with per-type sub-fields

When reading records via `GET`, Cloudflare populates BOTH — `content` gets a pretty-printed string, `data` holds the structured fields. When writing, use `data` for the types above and `content` for the rest.

## Per-Type `content`/`data` Format

| Type | Field | Format | Example |
|---|---|---|---|
| `A` | `content` | IPv4 dotted-quad | `75.2.60.5` |
| `AAAA` | `content` | IPv6 | `2600:1f18:24e6:b900::1` |
| `CNAME` | `content` | FQDN | `mysite.netlify.app` |
| `MX` | `content` + `priority` | target FQDN + priority | `mail.example.com`, `priority: 10` |
| `TXT` | `content` | raw string | `v=spf1 include:_spf.google.com ~all` |
| `NS` | `content` | nameserver FQDN | `ns1.cloudflare.com` |
| `SRV` | `data` | `{priority, weight, port, target}` | see below |
| `CAA` | `data` | `{flags, tag, value}` | `{flags:0, tag:"issue", value:"letsencrypt.org"}` |
| `PTR` | `content` | FQDN | `host.example.com` |

## CNAME Exclusivity

RFC 1034 rule: a CNAME at a given name cannot coexist with other records at that name. Cloudflare enforces this EXCEPT at the zone apex, where CNAME flattening is allowed.

Practical consequences:

- Before creating a `CNAME` at `www.example.com`, delete any `A`/`AAAA`/`MX`/`TXT` at `www.example.com`
- Before creating any `A`/`AAAA`/`MX` at a name, delete the `CNAME` at that name
- At the apex (`example.com`), CNAME IS allowed — but it still blocks `A`/`AAAA` at apex. You can't have a CNAME AND an A at the apex simultaneously.

Cloudflare returns `1004` or `409 Conflict` with `code: 81053` or similar when violated.

## TTL Semantics

- `ttl: 1` means "automatic" — Cloudflare decides. Roughly 300s for DNS-only, opaque for proxied.
- Proxied records ignore any explicit TTL — always served with Cloudflare's own edge TTL.
- DNS-only records honor the value you set (60–86400 seconds, 30 on Enterprise).
- Changing TTL is online — no downtime, but resolvers obey the OLD TTL until it expires.

Good practice: before a planned record change, lower TTL to 300s at least an hour in advance so rollback propagates quickly.

## CRUD

### Create

```bash
curl -X POST \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "www.example.com",
    "content": "mysite.netlify.app",
    "ttl": 1,
    "proxied": false,
    "comment": "Netlify deployment"
  }' \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records"
```

Returns `201` with the new record (including its assigned `id`). Idempotency is NOT automatic — POSTing the same record twice creates two records. Dedupe client-side (GET first, or use PATCH if an ID is known).

### Read

One:
```bash
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID"
```

All / filtered:
```bash
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=CNAME&name=www.example.com"
```

Record list supports `per_page=5000` — in practice, one page is plenty for any zone.

### Update — PATCH (partial)

Change only the fields you name; everything else stays:
```bash
curl -X PATCH \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "newsite.netlify.app"}' \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID"
```

**Prefer PATCH over PUT** for most record edits — it's forgiving and won't accidentally clear fields you didn't mean to touch.

### Update — PUT (full overwrite)

Every field must be provided; anything omitted is reset to default:
```bash
curl -X PUT \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "www.example.com",
    "content": "newsite.netlify.app",
    "ttl": 1,
    "proxied": false
  }' \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID"
```

Use PUT when you want to guarantee a specific end-state for the record (e.g., reverting to defaults).

### Delete

```bash
curl -X DELETE \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID"
```

Idempotent — second delete returns `404` but the end state is the same.

## Patterns

### Find a record by name + type

```bash
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=www.example.com&type=CNAME" \
  | python3 -c "import json,sys; recs=json.load(sys.stdin)['result']; [print(r['id'], r['content']) for r in recs]"
```

### Conflict-free CNAME creation

1. GET records at the target name
2. Delete any non-CNAME records there (A/AAAA/MX/TXT)
3. POST the new CNAME

Or, atomically, use a batch operation (see `docs/batch-operations.md`):
```json
{
  "deletes": [{"id": "<old-A-record-id>"}],
  "posts": [{"type": "CNAME", "name": "www.example.com", "content": "new.netlify.app", "ttl": 1, "proxied": false}]
}
```

### Change a record's `name` or `type`

Both are mutable via PATCH — you don't need delete-and-recreate like on IONOS. But be wary of CNAME exclusivity: moving a CNAME to a name with existing records, or changing an A to a CNAME at a name with other records, will 409.

## Validation Rules Enforced by Cloudflare

- `content` must parse correctly for `type` (IPv4 for A, FQDN for CNAME, etc.)
- `ttl: 1` or 60–86400 (30 on Enterprise)
- `priority` required and ≥0 for MX and SRV
- `data` fields required for SRV/CAA/etc.
- CNAME exclusivity (except at apex)
- NS records can only exist at apex or at names explicitly delegated
- Punycode for IDN names (Cloudflare converts automatically on input)

Violations return `400` or `409` with an error `code` and `message` in the `errors` array. Log the verbatim `message` when reporting to the user.

## The `comment` and `tags` Fields

- `comment` is free-form text stored with the record. Use for "why does this record exist" notes — especially helpful in larger zones. Not served in DNS responses.
- `tags` are an array of strings for grouping. You can filter records by tag using the API, but there's no UI for tags.

Both are safe metadata — add generously.
