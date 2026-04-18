# IONOS Hosting DNS API — Endpoint Reference

Complete reference for the endpoints the skill uses. Base URL: `https://api.hosting.ionos.com/dns/v1`. Authentication on every request: `X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET`.

## Common Assumptions

Throughout this reference:
- `$TOK` = `"$IONOS_API_PREFIX.$IONOS_API_SECRET"`
- `$ZONE_ID` = a zone UUID obtained from `GET /zones`
- `$RECORD_ID` = a record UUID obtained from `GET /zones/{zoneId}`
- All bodies and responses use `Content-Type: application/json`
- Timestamps are ISO 8601 UTC
- IDs are UUIDs

## Zones

### `GET /zones` — List all zones on the account

```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones"
```

**Response** (array):
```json
[
  {
    "id": "11af3414-ebba-11e9-8df5-...",
    "name": "example.com",
    "type": "NATIVE"
  }
]
```

Pagination: the API supports `?suffix=` to filter by domain suffix. For large account inventories, filter rather than paginating.

### `GET /zones/{zoneId}` — Get zone with records

```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID"
```

Optional query params:
- `?suffix=sub.example.com` — filter records to a specific name suffix
- `?recordName=www.example.com` — filter to records matching a name
- `?recordType=A` — filter by record type

**Response:**
```json
{
  "id": "11af3414-ebba-11e9-8df5-...",
  "name": "example.com",
  "type": "NATIVE",
  "records": [
    {
      "id": "22b1...",
      "name": "example.com",
      "rootName": "example.com",
      "type": "A",
      "content": "75.2.60.5",
      "changeDate": "2026-04-15T10:30:00Z",
      "ttl": 3600,
      "disabled": false
    }
  ]
}
```

### `PUT /zones/{zoneId}` — Bulk replace records ⚠️

**DESTRUCTIVE.** Replaces every record in the zone with the payload. Records omitted from the payload are deleted.

```bash
curl -X PUT -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '[
    {"name":"example.com","type":"A","content":"75.2.60.5","ttl":3600,"prio":0,"disabled":false},
    {"name":"www.example.com","type":"CNAME","content":"mysite.netlify.app","ttl":3600,"prio":0,"disabled":false},
    {"name":"example.com","type":"MX","content":"mx00.ionos.com","ttl":3600,"prio":10,"disabled":false}
  ]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID"
```

Never call this without user confirmation and a complete record set (including MX, TXT, etc.). See `SKILL.md` Safety Rule #3.

## Records

### `POST /zones/{zoneId}/records` — Create records

Accepts an array, creates one or more in a single call.

```bash
curl -X POST -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '[
    {"name":"www.example.com","type":"CNAME","content":"mysite.netlify.app","ttl":3600,"prio":0,"disabled":false}
  ]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records"
```

**Response:** `201 Created` with an array of the created records (each now has an `id`).

**Conflict:** Returns `409` if a conflicting record exists (same name+type+content, or CNAME exclusivity violation).

### `GET /zones/{zoneId}/records/{recordId}` — Read a single record

```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

### `PUT /zones/{zoneId}/records/{recordId}` — Update a single record

Replaces the record's mutable fields. The record's `id`, `name`, and `type` cannot be changed — to change those, delete and re-create.

```bash
curl -X PUT -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d '{"content":"75.2.60.6","ttl":300,"prio":0,"disabled":false}' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

### `DELETE /zones/{zoneId}/records/{recordId}` — Delete a single record

```bash
curl -X DELETE -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

**Response:** `200 OK` (no body).

## Record Object — Field Reference

| Field | Type | Required on create | Description |
|---|---|---|---|
| `id` | UUID | — (auto) | Server-assigned record ID |
| `name` | string | yes | FQDN (`www.example.com`, or `example.com` for apex) |
| `rootName` | string | — (derived) | Zone name (`example.com`) |
| `type` | string | yes | `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`, `SRV`, `CAA`, `ALIAS`, etc. |
| `content` | string | yes | Record value; format depends on `type` (see below) |
| `ttl` | int | no (default 3600) | Cache TTL in seconds; min 60, max 86400 |
| `prio` | int | yes for MX/SRV, else 0 | Priority |
| `disabled` | bool | no (default false) | If true, record exists but isn't served |
| `changeDate` | ISO 8601 | — (auto) | Last modification timestamp |

### Per-Type `content` Format

| Type | Format | Example |
|---|---|---|
| `A` | IPv4 dotted-quad | `75.2.60.5` |
| `AAAA` | IPv6 | `2600:1f18:620b:4700::1` |
| `CNAME` | FQDN (trailing dot optional) | `mysite.netlify.app` |
| `MX` | mail server FQDN; set priority via `prio` | `mx00.ionos.com` (with `prio: 10`) |
| `TXT` | quoted string (quotes usually added by server) | `v=spf1 include:_spf.google.com ~all` |
| `NS` | nameserver FQDN | `ns1.ionos.com` |
| `SRV` | `weight port target` (`prio` separate) | `5 5060 sip.example.com` (with `prio: 0`) |
| `CAA` | `flag tag "value"` | `0 issue "letsencrypt.org"` |
| `ALIAS` | FQDN (IONOS extension for apex) | `mysite.netlify.app` |

## Error Responses

Errors return a JSON body with `code` and `message`:

```json
{
  "code": "CONFLICT",
  "message": "A CNAME record cannot coexist with other records at www.example.com"
}
```

| HTTP | Typical cause |
|---|---|
| `400` | Malformed JSON or missing required field |
| `401` | Invalid `X-API-Key` header |
| `403` | Key valid but lacks permission for this zone |
| `404` | Zone or record ID doesn't exist |
| `409` | Conflict — CNAME exclusivity, duplicate, etc. |
| `422` | Unprocessable — invalid content format for the record type |
| `429` | Rate limited |
| `500+` | IONOS-side; retry with backoff |

## Rate Limits

IONOS does not publish exact rate limits. Observed in practice: a few hundred requests/minute per key before 429s. For bulk operations, prefer the array-accepting `POST /records` endpoint over many single-record calls.

## Idempotency

- `GET` is safe/idempotent
- `PUT /zones/{zoneId}/records/{recordId}` is idempotent (re-applying the same body yields the same state)
- `POST /zones/{zoneId}/records` is NOT idempotent — repeated calls create duplicates. Check with a GET first.
- `DELETE` is idempotent (second call returns 404 but the effect is the same)
- `PUT /zones/{zoneId}` (bulk) is idempotent for a given payload

## Related Endpoints (not used by this skill)

The IONOS Hosting API also exposes, at different base paths:

- Dynamic DNS: `/dns/v1/dyndns` — for homeserver-style dynamic updates
- SSL certificates: `/sslmanagement/v1/certificates` — separate skill if needed
- Packages: different API surface entirely

These are out of scope for the DNS-record-management skill.
