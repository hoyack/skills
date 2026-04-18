# Record Object Reference

A **record** is a single DNS RR (resource record) in a zone. IONOS assigns each record a UUID `id` so you can update/delete by ID without needing to re-parse the zone.

## Object Shape

| Field | Type | Mutable via PUT | Description |
|---|---|---|---|
| `id` | UUID | — | Server-assigned, stable across updates |
| `name` | string | no (delete + recreate) | FQDN (`www.example.com`; use the full apex name for apex records, e.g., `example.com`) |
| `rootName` | string | — (derived) | Zone `name` (`example.com`) |
| `type` | string | no (delete + recreate) | DNS record type |
| `content` | string | yes | Record data; format varies by `type` |
| `ttl` | int | yes | Cache time-to-live in seconds (60–86400) |
| `prio` | int | yes | Priority (used by MX, SRV; ignored otherwise) |
| `disabled` | bool | yes | If true, record is stored but not served |
| `changeDate` | ISO 8601 | — | Last modification timestamp |

Note: `name` uses the FQDN form, not the zone-relative form. For the apex of `example.com`, set `name: "example.com"` (not `"@"`).

## Per-Type Content Format

| Type | Content format | Notes |
|---|---|---|
| `A` | IPv4 (`75.2.60.5`) | Multiple A records at the same name = round-robin |
| `AAAA` | IPv6 (`2600:1f18:620b:4700::1`) | — |
| `CNAME` | FQDN target (`mysite.netlify.app`) | Cannot coexist with any other record at the same name (RFC 1034). Disallowed at zone apex. |
| `MX` | mail-server FQDN (`mx00.ionos.com`) | Priority goes in `prio`, NOT `content` |
| `TXT` | raw string (`v=spf1 include:_spf.google.com ~all`) | IONOS handles quote wrapping; do not include wrapping quotes in the payload |
| `NS` | nameserver FQDN (`ns1.ionos.com`) | Rarely modified |
| `SRV` | `weight port target` (`5 5060 sip.example.com`) | Priority goes in `prio`, NOT `content` |
| `CAA` | `flag tag "value"` (`0 issue "letsencrypt.org"`) | Limits which CAs can issue certs for the domain |
| `ALIAS` | FQDN (`mysite.netlify.app`) | IONOS extension; behaves like CNAME but legal at apex |

### Notes on record types

- **CNAME at apex is illegal.** Use `ALIAS` instead if the target is a hostname, or resolve the hostname to an IP and use `A`.
- **Multiple records at the same name+type** are allowed for most types (A, AAAA, TXT, MX, NS). Each is a separate record object with its own `id`.
- **TXT content length** — single-string max is 255 bytes. IONOS handles long SPF/DKIM splitting automatically; supply the full string.

## CRUD

### Create

```bash
curl -X POST -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '[
    {
      "name": "www.example.com",
      "type": "CNAME",
      "content": "mysite.netlify.app",
      "ttl": 3600,
      "prio": 0,
      "disabled": false
    }
  ]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records"
```

Payload is an array — one POST can create many records. Returns `201` with the created records (each now has an `id`).

### Read

One record:
```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

All records (see [zones.md](zones.md)):
```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID"
```

### Update (mutable fields)

```bash
curl -X PUT -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '{"content":"75.2.60.6","ttl":300,"prio":0,"disabled":false}' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

Omitting a field is NOT a "leave alone" signal — it's an explicit `null`/default. When uncertain, GET first and echo the current values.

### Delete

```bash
curl -X DELETE -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

Returns `200`. Calling again on a deleted ID returns `404`.

## Common Patterns

### Find a specific record by name + type

No query-by-ID shortcut exists — GET the zone (optionally with `?recordName=` + `?recordType=`), then filter client-side:

```bash
curl -s -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID?recordName=www.example.com&recordType=CNAME" \
  | python3 -c "import json,sys; recs=json.load(sys.stdin).get('records',[]); [print(r['id'], r['content']) for r in recs]"
```

### Atomic update by delete + recreate

To change a record's `name` or `type` (immutable via PUT), delete the old and create the new. Between those two calls, the record is absent — schedule during low-traffic windows for critical records.

### Conflict-free CNAME creation

```bash
# 1. Check for any existing records at the target name
curl -s -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID?recordName=www.example.com" \
  | python3 -m json.tool

# 2. Delete any conflicting records (CNAME cannot coexist with A/AAAA/MX/TXT at the same name)

# 3. Create the CNAME
curl -X POST -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '[{"name":"www.example.com","type":"CNAME","content":"mysite.netlify.app","ttl":3600,"prio":0,"disabled":false}]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records"
```

### Lowering TTL before a migration

Good practice before any planned record change: lower TTL 24+ hours in advance so rollback is fast.

```bash
# Lower TTL to 300s
curl -X PUT -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '{"content":"75.2.60.5","ttl":300,"prio":0,"disabled":false}' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"

# Wait 24h, make the actual change, then raise TTL back to 3600s
```

## Validation Rules Enforced by IONOS

- `ttl` must be 60–86400
- `prio` required and >0 for MX and SRV; ignored for other types
- `content` must parse as the correct format for `type` (IPv4 for A, FQDN for CNAME, etc.)
- CNAME exclusivity: 409 if another record exists at the same name
- Duplicate detection: 409 if an identical `{name, type, content}` triple already exists (for types where dupes make no sense)

Violations return `409` or `422` with a descriptive `message`. Log the message verbatim when reporting errors to the user.

## `disabled` Field

Setting `disabled: true` keeps the record object but removes it from DNS responses. Useful for:

- Staging a change without going live (flip to `false` when ready)
- Temporary takedown without losing the config

Not a substitute for `DELETE` — disabled records still count against any per-zone quotas.
