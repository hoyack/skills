# Batch Record Operations

`POST /zones/{zone_id}/dns_records/batch` applies multiple creates/updates/deletes atomically. Use this for anything touching more than a couple of records, or when partial success would leave the zone in a broken state.

## Endpoint

```
POST /zones/{zone_id}/dns_records/batch
```

## Request Body

```json
{
  "posts":   [ ... ],  // new records to create
  "puts":    [ ... ],  // full-overwrite updates (each item needs "id")
  "patches": [ ... ],  // partial updates (each item needs "id" + fields to change)
  "deletes": [ { "id": "..." }, ... ]
}
```

All four arrays are optional. Any array omitted means "no operations of that type."

### Order of execution

Cloudflare applies operations in this order:
1. `deletes`
2. `patches`
3. `puts`
4. `posts`

This matters: if you're replacing a CNAME with an A record at the same name, put the delete first and the post after — within a single batch request, the delete runs first, so the post won't hit the CNAME-exclusivity 409.

## Atomicity

Either every operation succeeds or none do. There's no partial-apply state. On failure the response includes which specific item in the batch failed and why; the zone is untouched.

This makes batches the safest way to perform multi-record changes — you don't need a rollback plan because failure means nothing changed.

## Plan Limits

| Plan | Max changes per batch |
|---|---|
| Free | 200 |
| Pro | 3,500 |
| Business | 3,500 |
| Enterprise | 3,500 (soft; contact CF for more) |

For the rare huge-migration case, chain multiple batches sequentially. Each batch is independent, so failure of batch N doesn't affect batches 1..N-1.

## Examples

### Swap apex A → CNAME (common when moving to Netlify)

```json
{
  "deletes": [
    { "id": "<apex-A-record-id>" }
  ],
  "posts": [
    {
      "type": "CNAME",
      "name": "example.com",
      "content": "mysite.netlify.app",
      "ttl": 1,
      "proxied": false,
      "comment": "Apex to Netlify (flattened)"
    }
  ]
}
```

One atomic call: old A goes away, new CNAME appears. No window where the apex is undefined.

### Apex + www together

```json
{
  "deletes": [
    { "id": "<apex-A-record-id>" },
    { "id": "<www-A-record-id>" }
  ],
  "posts": [
    {
      "type": "CNAME",
      "name": "example.com",
      "content": "mysite.netlify.app",
      "ttl": 1,
      "proxied": false
    },
    {
      "type": "CNAME",
      "name": "www.example.com",
      "content": "mysite.netlify.app",
      "ttl": 1,
      "proxied": false
    }
  ]
}
```

### Toggle proxy on many records in one go

```json
{
  "patches": [
    { "id": "<record-1-id>", "proxied": true },
    { "id": "<record-2-id>", "proxied": true },
    { "id": "<record-3-id>", "proxied": true }
  ]
}
```

### Zone migration from another provider

Load an exported zone file, map to Cloudflare's record shape, batch POST:

```json
{
  "posts": [
    { "type": "A",     "name": "example.com",     "content": "1.2.3.4",             "ttl": 3600, "proxied": false },
    { "type": "CNAME", "name": "www.example.com", "content": "example.com",         "ttl": 3600, "proxied": false },
    { "type": "MX",    "name": "example.com",     "content": "mail.example.com",    "ttl": 3600, "priority": 10 },
    { "type": "TXT",   "name": "example.com",     "content": "v=spf1 -all",         "ttl": 3600 }
  ]
}
```

For zones with more than 200 records on Free, split into multiple batches.

## Safe Pattern (with user confirmation)

1. GET the current zone records → snapshot to a file
2. Build the proposed batch (all 4 arrays as needed)
3. **Show the user the diff:** for each operation, print what's being added/changed/deleted
4. Wait for explicit "yes, proceed"
5. POST `/batch`
6. On success: GET zone again, diff against snapshot to confirm
7. On error: the zone is unchanged; parse the error array and report which item failed and why

## Error Handling

A batch failure response looks like:

```json
{
  "success": false,
  "errors": [
    {
      "code": 81053,
      "message": "A, AAAA, or CNAME record with that host already exists.",
      "source": { "pointer": "/posts/0" }
    }
  ],
  "result": null
}
```

The `source.pointer` tells you which operation failed. Common batch errors:

| Error code | Cause | Fix |
|---|---|---|
| `81053` | CNAME exclusivity | Ensure a delete for the conflicting record is in the same batch |
| `81057` | Identical record exists | The record you're creating already exists; skip or delete first |
| `9005` | Duplicate operations in one batch | Deduplicate your input |
| `1004` | Invalid record data | Check `content`/`data` format per `docs/records.md` |
| `7003`/`7000` | Missing required path parameter or body field | Verify zone ID, operation item shape |

## When NOT to Use Batch

- Single record change — direct CRUD is simpler and the atomicity doesn't matter
- Very unrelated operations on the same zone — splitting them into separate requests means partial-apply on failure, which is sometimes what you want (e.g., don't fail adding SPF just because a CAA creation failed)
- Cross-zone operations — each batch is zone-scoped; multiple zones need multiple batches

## Non-Obvious Details

- **Record IDs in `puts`/`patches`/`deletes` must exist in the zone.** Referring to an ID from a different zone returns `404`, and the whole batch fails.
- **`posts` don't have IDs.** The API assigns them. The response includes assigned IDs in the same order as the request.
- **The order of the response arrays matches the order of the request arrays**, so you can correlate results to inputs by index.
- **`data` (for SRV/CAA/etc.) is supported** in batch payloads exactly as in single-record operations.
