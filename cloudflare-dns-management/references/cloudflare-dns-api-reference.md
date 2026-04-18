# Cloudflare DNS API Reference

Complete endpoint reference for DNS operations via the Cloudflare API v4.

**Base URL:** `https://api.cloudflare.com/client/v4`

**Authentication:** Bearer token in the `Authorization` header:
```
Authorization: Bearer {CLOUDFLARE_API_TOKEN}
```

**Content-Type:** `application/json` for all request bodies.

**Response format:** All responses follow this envelope:
```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": { ... },
  "result_info": { "page": 1, "per_page": 100, "total_count": 50, "total_pages": 1 }
}
```

## Table of Contents

1. [Zones](#zones)
2. [DNS Records](#dns-records)
3. [Batch Operations](#batch-operations)
4. [Record Format Reference](#record-format-reference)
5. [MCP Code Mode Examples](#mcp-code-mode-examples)
6. [Curl Examples](#curl-examples)

---

## Zones

### List Zones

```
GET /zones
```

Returns all zones (domains) on the account. Use query parameters to filter.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Filter by domain name (exact match) |
| `status` | string | Filter by status: `active`, `pending`, `initializing`, `moved`, `deleted` |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Results per page (default: 20, max: 50) |

**Response `result` item:**
```json
{
  "id": "023e105f4ecef8ad9ca31a8372d0c353",
  "name": "example.com",
  "status": "active",
  "paused": false,
  "type": "full",
  "name_servers": [
    "ada.ns.cloudflare.com",
    "bret.ns.cloudflare.com"
  ]
}
```

The `id` field is the zone ID needed for all record operations.

### Get Zone Details

```
GET /zones/{zone_id}
```

Returns details for a single zone.

---

## DNS Records

### List DNS Records

```
GET /zones/{zone_id}/dns_records
```

Returns all DNS records in a zone. Supports filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by record type: `A`, `AAAA`, `CNAME`, `MX`, `TXT`, etc. |
| `name` | string | Filter by record name (FQDN, e.g., `www.example.com`) |
| `content` | string | Filter by record content (IP, hostname, etc.) |
| `proxied` | boolean | Filter by proxy status |
| `page` | integer | Page number |
| `per_page` | integer | Results per page (max: 5000) |
| `order` | string | Sort field: `type`, `name`, `content`, `ttl`, `proxied` |
| `direction` | string | Sort direction: `asc`, `desc` |
| `match` | string | Match mode: `any` (OR) or `all` (AND) for filters |

**Response `result` item:**
```json
{
  "id": "372e67954025e0ba6aaa6d586b9e0b59",
  "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
  "zone_name": "example.com",
  "name": "www.example.com",
  "type": "CNAME",
  "content": "mysite.netlify.app",
  "proxiable": true,
  "proxied": false,
  "ttl": 1,
  "comment": "Pointing to Netlify deployment",
  "tags": [],
  "created_on": "2024-01-01T00:00:00Z",
  "modified_on": "2024-01-01T00:00:00Z"
}
```

### Create DNS Record

```
POST /zones/{zone_id}/dns_records
```

Creates a new DNS record.

**Request Body:**
```json
{
  "type": "CNAME",
  "name": "www.example.com",
  "content": "mysite.netlify.app",
  "ttl": 1,
  "proxied": false,
  "comment": "Netlify deployment"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Record type |
| `name` | string | Yes | Record name (FQDN or relative to zone) |
| `content` | string | Yes | Record value |
| `ttl` | integer | Yes | TTL in seconds. `1` = automatic |
| `proxied` | boolean | No | Whether to proxy through Cloudflare (default: false) |
| `priority` | integer | Conditional | Required for MX and SRV records |
| `comment` | string | No | Comment/note (no effect on DNS) |
| `tags` | array | No | Tags for organization |

**Response (200):** Returns the created record with its assigned `id`.

**Constraints:**
- A/AAAA records cannot coexist with CNAME records at the same name
- NS records cannot coexist with other record types at the same name
- Domain names are represented in Punycode

### Get DNS Record

```
GET /zones/{zone_id}/dns_records/{dns_record_id}
```

Returns a single record by ID.

### Update DNS Record (Full Overwrite)

```
PUT /zones/{zone_id}/dns_records/{dns_record_id}
```

Overwrites an entire record. All fields must be provided.

**Request Body:** Same shape as create. All fields required.

### Update DNS Record (Partial)

```
PATCH /zones/{zone_id}/dns_records/{dns_record_id}
```

Updates only the provided fields. Other fields remain unchanged.

**Request Body:** Include only the fields you want to change:
```json
{
  "content": "new-site.netlify.app",
  "proxied": false
}
```

### Delete DNS Record

```
DELETE /zones/{zone_id}/dns_records/{dns_record_id}
```

Deletes a record permanently. Returns the deleted record's `id`.

---

## Batch Operations

### Batch DNS Record Changes

```
POST /zones/{zone_id}/dns_records/batch
```

Perform multiple create, update, and delete operations in a single atomic request.

**Limits:**
- Free plans: up to 200 changes per batch
- Paid plans: up to 3,500 changes per batch
- Tested up to 100,000 changes internally

**Request Body:**
```json
{
  "posts": [
    {
      "type": "CNAME",
      "name": "www.example.com",
      "content": "mysite.netlify.app",
      "ttl": 1,
      "proxied": false
    }
  ],
  "puts": [
    {
      "id": "existing-record-id",
      "type": "A",
      "name": "example.com",
      "content": "75.2.60.5",
      "ttl": 1,
      "proxied": false
    }
  ],
  "patches": [
    {
      "id": "another-record-id",
      "content": "new-value"
    }
  ],
  "deletes": [
    { "id": "record-to-delete-id" }
  ]
}
```

Batch operations are **atomic** — all changes succeed or all fail. This prevents partial states.

---

## Record Format Reference

### A Record
```json
{ "type": "A", "name": "example.com", "content": "75.2.60.5", "ttl": 1, "proxied": true }
```

### AAAA Record
```json
{ "type": "AAAA", "name": "example.com", "content": "2600:1f18:24e6:b900::1", "ttl": 1, "proxied": true }
```

### CNAME Record
```json
{ "type": "CNAME", "name": "www.example.com", "content": "mysite.netlify.app", "ttl": 1, "proxied": false }
```
At the zone apex, Cloudflare automatically flattens the CNAME:
```json
{ "type": "CNAME", "name": "example.com", "content": "mysite.netlify.app", "ttl": 1, "proxied": false }
```

### MX Record
```json
{ "type": "MX", "name": "example.com", "content": "mail.example.com", "ttl": 1, "priority": 10 }
```
Cannot be proxied. `priority` is required — lower number = higher priority.

### TXT Record
```json
{ "type": "TXT", "name": "example.com", "content": "v=spf1 include:_spf.google.com ~all", "ttl": 1 }
```

### SRV Record
```json
{
  "type": "SRV",
  "name": "_sip._tcp.example.com",
  "data": {
    "priority": 10,
    "weight": 5,
    "port": 5060,
    "target": "sip.example.com"
  },
  "ttl": 1
}
```
SRV records use the `data` object instead of `content`.

### CAA Record
```json
{
  "type": "CAA",
  "name": "example.com",
  "data": {
    "flags": 0,
    "tag": "issue",
    "value": "letsencrypt.org"
  },
  "ttl": 1
}
```

### NS Record
```json
{ "type": "NS", "name": "example.com", "content": "ns1.cloudflare.com", "ttl": 1 }
```
**Warning:** Modifying NS records can break DNS resolution.

---

## MCP Code Mode Examples

When using the Cloudflare MCP server at `mcp.cloudflare.com`, the agent uses `search()` and `execute()` tools. Here are DNS-specific examples.

### Search for DNS endpoints

```javascript
// search() call
async () => {
  const results = [];
  for (const [path, methods] of Object.entries(spec.paths)) {
    for (const [method, op] of Object.entries(methods)) {
      if (path.includes('dns_records') && !path.includes('transfer')) {
        results.push({ method: method.toUpperCase(), path, summary: op.summary });
      }
    }
  }
  return results;
}
```

### List all zones

```javascript
// execute() call
async () => {
  const response = await cloudflare.request({
    method: "GET",
    path: "/zones"
  });
  return response.result.map(z => ({ id: z.id, name: z.name, status: z.status }));
}
```

### List DNS records for a zone

```javascript
// execute() call
async () => {
  const response = await cloudflare.request({
    method: "GET",
    path: `/zones/${zoneId}/dns_records`
  });
  return response.result.map(r => ({
    id: r.id, type: r.type, name: r.name,
    content: r.content, proxied: r.proxied, ttl: r.ttl
  }));
}
```

### Create a CNAME record

```javascript
// execute() call
async () => {
  const response = await cloudflare.request({
    method: "POST",
    path: `/zones/${zoneId}/dns_records`,
    body: {
      type: "CNAME",
      name: "www.example.com",
      content: "mysite.netlify.app",
      ttl: 1,
      proxied: false
    }
  });
  return response.result;
}
```

### Update a record

```javascript
// execute() call
async () => {
  const response = await cloudflare.request({
    method: "PATCH",
    path: `/zones/${zoneId}/dns_records/${recordId}`,
    body: {
      content: "new-target.netlify.app",
      proxied: false
    }
  });
  return response.result;
}
```

### Delete a record

```javascript
// execute() call
async () => {
  const response = await cloudflare.request({
    method: "DELETE",
    path: `/zones/${zoneId}/dns_records/${recordId}`
  });
  return response.result;
}
```

---

## Curl Examples

### List all zones
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json"
```

### Find zone by domain name
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json"
```

### List all DNS records
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json"
```

### List only A records
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=A" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json"
```

### Create a CNAME record for Netlify
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "example.com",
    "content": "mysite.netlify.app",
    "ttl": 1,
    "proxied": false,
    "comment": "Apex CNAME to Netlify (flattened by Cloudflare)"
  }'
```

### Partial update (PATCH) a record
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "new-site.netlify.app"
  }'
```

### Full overwrite (PUT) a record
```bash
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "www.example.com",
    "content": "updated-site.netlify.app",
    "ttl": 1,
    "proxied": false
  }'
```

### Delete a record
```bash
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"
```

### Batch create/update/delete
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/batch" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {
        "type": "CNAME",
        "name": "www.example.com",
        "content": "mysite.netlify.app",
        "ttl": 1,
        "proxied": false
      }
    ],
    "deletes": [
      { "id": "old-record-id-to-remove" }
    ]
  }'
```
