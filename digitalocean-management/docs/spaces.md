# Spaces Storage Reference

S3-compatible object storage. Use for: user uploads, static assets served to browsers, backups, data lakes, any blob that doesn't need a filesystem.

Pricing (as of this writing): $5/mo base for 250 GB storage + 1 TB outbound transfer, then $0.02/GB storage / $0.01/GB transfer. Cheaper than S3 for small-to-medium workloads; lacks some niche AWS features (versioning with retention policies, Glacier-tier archival).

## Regions

| Region | Slug |
|---|---|
| New York | `nyc3` |
| San Francisco | `sfo3` |
| Amsterdam | `ams3` |
| Singapore | `sgp1` |
| Frankfurt | `fra1` |
| Sydney | `syd1` |

Pick close to your app. Spaces in a different region from your App Platform app will work but add latency and egress.

## Endpoint

Each region has its own endpoint:
```
https://<region>.digitaloceanspaces.com
```

For a specific Space, the virtual-hosted URL is:
```
https://<space-name>.<region>.digitaloceanspaces.com/<object-key>
```

## Credentials

Spaces uses separate credentials from the main DO API token — a **Spaces Key** (access key + secret):

1. DO dashboard → **API** → **Spaces Keys** → **Generate New Key**
2. Copy both parts immediately

Drop these into your `.env`:
```
DO_SPACES_KEY=<access-key>
DO_SPACES_SECRET=<secret>
DO_SPACES_REGION=nyc3
DO_SPACES_BUCKET=my-space
```

## Creating a Space

### Via MCP (`space-create`)

```json
{
  "name": "thunderstaff-assets",
  "region": "nyc3",
  "acl": "private"
}
```

`acl`: `private` (default; access via signed URLs or authenticated requests) or `public-read` (anyone can GET objects — use for public static assets only).

### Via S3-compatible CLI

```bash
# aws-cli works directly
aws --endpoint-url https://nyc3.digitaloceanspaces.com s3 mb s3://thunderstaff-assets
```

## S3 Compatibility

Supports most S3 API operations:

- `PutObject` / `GetObject` / `DeleteObject`
- `ListObjects` / `ListObjectsV2`
- Multipart uploads
- Presigned URLs
- Bucket ACLs (limited — `private` or `public-read` only)
- CORS configuration

Doesn't fully support:
- **Versioning with retention** — basic versioning yes, but Object Lock / Retention policies limited
- **Bucket notifications** — no SNS/SQS/Lambda-like integration; for events, poll or use webhooks in your app
- **Server-side encryption with customer-provided keys** — server-side encryption is always on (DO-managed), but SSE-C isn't exposed
- **Intelligent tiering / Glacier** — single storage class only
- **Replication** — no cross-region replication out of the box

For most web-app workloads (uploads, static assets, backups), these gaps don't matter.

## CORS

Essential for browser-facing Spaces (user uploads via presigned URL, SPA consuming assets):

```xml
<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>https://app.example.com</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedMethod>POST</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
    <MaxAgeSeconds>3000</MaxAgeSeconds>
  </CORSRule>
</CORSConfiguration>
```

Apply via `PutBucketCORS` (`aws-cli` or SDK).

## CDN

Enable on any Space to serve from DO's CDN edge nodes. Essentially required for public-read Spaces facing end users:

1. Dashboard or MCP → toggle CDN on the Space
2. Optional: attach a custom domain (requires certificate)
3. CDN URL becomes `<space>.nyc3.cdn.digitaloceanspaces.com` (or the custom domain)

### Cache invalidation

Edge nodes cache for the object's `Cache-Control` TTL. For explicit flushing:

```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"files": ["/path/to/obj", "/wildcard/*"]}' \
  https://api.digitalocean.com/v2/cdn/endpoints/<endpoint-id>/cache
```

Propagation: usually seconds, sometimes a couple of minutes.

## Lifecycle Rules (Basic)

For automatic deletion of old objects (e.g., temporary uploads, log archives):

```xml
<LifecycleConfiguration>
  <Rule>
    <ID>expire-old-uploads</ID>
    <Prefix>tmp/</Prefix>
    <Status>Enabled</Status>
    <Expiration>
      <Days>7</Days>
    </Expiration>
  </Rule>
</LifecycleConfiguration>
```

Apply via `PutBucketLifecycle`.

## Presigned URLs

For direct client-to-Spaces uploads without exposing credentials:

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{region}.digitaloceanspaces.com",
    aws_access_key_id=os.environ["DO_SPACES_KEY"],
    aws_secret_access_key=os.environ["DO_SPACES_SECRET"],
    config=Config(signature_version="s3v4"),
)

url = s3.generate_presigned_url(
    "put_object",
    Params={"Bucket": "thunderstaff-assets", "Key": "uploads/user-123/file.pdf", "ContentType": "application/pdf"},
    ExpiresIn=3600,
)
```

Client then:
```js
fetch(url, { method: "PUT", body: file, headers: { "Content-Type": "application/pdf" } })
```

## Common Patterns

### Direct browser upload

Client requests a presigned URL from your backend → backend mints it with a narrow `Key` prefix (e.g., `uploads/<user_id>/`) → client PUTs the file directly to Spaces → backend stores just the key in DB.

### Static asset CDN for an SPA

Spaces with CDN + custom domain is a reasonable Netlify alternative for pure static hosting. Build the SPA, `aws s3 sync dist/ s3://space --delete --cache-control "public,max-age=31536000"`, then flush CDN for the HTML entry point.

### Backup destination

```bash
aws --endpoint-url https://nyc3.digitaloceanspaces.com s3 cp /backup/db-2026-04-15.sql.gz s3://backups/
```

Combine with a lifecycle rule to delete anything older than 90 days.

## Pitfalls

| Symptom | Likely Cause |
|---|---|
| Browser CORS error on presigned PUT | CORS rule missing or doesn't include `PUT` |
| Presigned URL returns 403 after a few minutes | Clock skew on the signing machine; sync NTP |
| Object is public but 403s on GET | Space ACL is `private`; public-read is per-object or per-bucket |
| CDN returns stale files after upload | `Cache-Control: max-age=N` too high; flush or shorten |
| "SignatureDoesNotMatch" errors | Wrong region endpoint; using path-style instead of virtual-hosted; using AWS signature v2 (Spaces requires v4) |
| Bill surprise | Lots of egress (CDN misses), or forgotten Space with lots of data |
