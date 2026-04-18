# Zone Object Reference

A **zone** is the authoritative DNS container for a domain. On IONOS, one zone == one domain (no sub-zone delegation within a single zone).

## Object Shape

From `GET /zones/{zoneId}`:

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Zone identifier — used in all zone-scoped URLs |
| `name` | string | Domain name (no trailing dot; `example.com`) |
| `type` | string | `NATIVE` (IONOS authoritative) — the only value observed in practice |
| `records` | array | All records in the zone; present on single-zone reads, not on list |

Each record has the shape documented in [records.md](records.md).

## Listing Zones

```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones"
```

Returns an array of `{ id, name, type }` — no records inline (use the per-zone GET to hydrate).

### Filter by suffix

```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones?suffix=example.com"
```

Useful for accounts with many domains; matches suffix on the `name` field.

## Inspecting a Zone

```bash
curl -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID"
```

Optional query filters narrow the returned records but do not change zone identity:
- `?recordName=www.example.com` — exact name match
- `?recordType=A` — filter to a type
- `?suffix=sub.example.com` — all records under a suffix

Use a filtered read when the zone is large and you only care about one subdomain.

## Bulk PUT Semantics ⚠️

`PUT /zones/{zoneId}` accepts a JSON array of records and makes the zone exactly match that array. Critical implications:

- **Omitted records are deleted.** No "partial update" semantics.
- **IDs are ignored** in the payload — records are matched by `name`+`type`+`content` triple. Any record that doesn't match something already in the zone is created with a new ID.
- **There is no dry-run.** The mutation is committed on a successful 200.
- **No automatic backup is taken.** Always snapshot the zone to a file before calling this.

For any non-trivial change set, prefer per-record `POST`/`PUT`/`DELETE` over bulk PUT. Bulk PUT is appropriate for: zone migration from another provider, initial zone population, or complete zone reset.

### Safe pattern for bulk PUT

```bash
# 1. Snapshot
curl -s -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID" \
  > "/tmp/zone-backup-$(date +%Y%m%dT%H%M%S).json"

# 2. Build the new record array externally — include every record that should remain

# 3. Confirm with user (print diff vs. snapshot)

# 4. Apply
curl -X PUT -H "X-API-Key: $TOK" -H "Content-Type: application/json" \
  -d @/tmp/new-records.json \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID"

# 5. Read back and diff against the intended payload
curl -s -H "X-API-Key: $TOK" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID" > /tmp/zone-post.json
```

If step 5 shows discrepancies, restore from the snapshot via another bulk PUT.

## Zone Lifecycle

- Zones are auto-created when a domain is added to the IONOS account
- Zones cannot be deleted via this API — removing a domain (and its zone) requires action in the IONOS dashboard
- The `type` field is always `NATIVE` in practice; IONOS does not expose slave/forwarding zones via this API

## What the API Does NOT Expose

- **DNSSEC signing keys** — enabled/disabled only via the IONOS dashboard
- **Zone transfers (AXFR)** — no IXFR/AXFR endpoint
- **Serial numbers / SOA fields** — hidden; IONOS manages SOA automatically
- **NS delegation changes for the zone apex** — changing a domain's nameservers is a registrar-level operation
