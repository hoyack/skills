# Pointing an IONOS Domain at a Netlify Project

End-to-end walkthrough for the primary use case: a domain whose DNS lives at IONOS, being pointed at a site deployed via `netlify-landing-page-deploy`.

This is the concrete, curl-level expansion of Workflow 2 in SKILL.md.

## Assumptions

- Environment: `IONOS_API_PREFIX`, `IONOS_API_SECRET`, and `NETLIFY_PERSONAL_ACCESS_TOKEN` all set
- Netlify project already exists with a known `site_id`
- Domain already exists in IONOS with its own zone (created automatically when the domain was added to the IONOS account)
- Domain's nameservers at the registrar are IONOS nameservers (verify with `dig NS`)

## Step 0 — Sanity Checks

```bash
# IONOS credentials
curl -s -o /dev/null -w "IONOS %{http_code}\n" \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  https://api.hosting.ionos.com/dns/v1/zones

# Netlify credentials
curl -s -o /dev/null -w "Netlify %{http_code}\n" \
  -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  https://api.netlify.com/api/v1/sites

# Current nameservers for the target domain
dig @8.8.8.8 example.com NS +short
# Expected: contains "ionos" — e.g., ns1057.ui-dns.biz., ns1091.ui-dns.com., etc.
```

## Step 1 — Find the Zone ID

```bash
ZONE_ID=$(curl -s \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  "https://api.hosting.ionos.com/dns/v1/zones?suffix=example.com" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")
echo "Zone: $ZONE_ID"
```

If the API returns `[]`, the domain is not in IONOS DNS — stop and clarify where DNS is hosted.

## Step 2 — Snapshot the Zone

```bash
mkdir -p /tmp/dns-backup
curl -s -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID" \
  | python3 -m json.tool \
  > /tmp/dns-backup/example.com-$(date +%Y%m%dT%H%M%S).json
```

Present a table to the user summarizing current A/AAAA/CNAME/MX/TXT records before proposing changes.

## Step 3 — Identify Records to Change

From the snapshot, find:

| Purpose | Name | Action |
|---|---|---|
| Apex → Netlify | `example.com` | Replace existing A/ALIAS or create new |
| `www` → Netlify | `www.example.com` | Replace existing CNAME/A or create new |
| MX / TXT (email, SPF, DKIM, DMARC) | various | **Leave untouched** |

If an A record at `www` exists, delete it before creating the CNAME (CNAME exclusivity).

## Step 4 — Lower TTL (Optional But Recommended)

If the existing A/CNAME records have TTL 3600+, lower to 300s and wait an hour before proceeding. This makes rollback fast if something breaks.

```bash
# For each record you intend to change:
curl -X PUT \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"content":"<existing-content>","ttl":300,"prio":0,"disabled":false}' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$RECORD_ID"
```

Skip this step for small personal sites with no existing traffic.

## Step 5 — Set the Apex Record

IONOS supports `ALIAS`, which is preferred over `A` at the apex because it follows the Netlify load balancer if it ever moves:

```bash
# If an A/ALIAS at apex already exists, PUT on its record ID:
APEX_RECORD_ID=<from snapshot>
curl -X PUT \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"content":"<netlify-project>.netlify.app","ttl":3600,"prio":0,"disabled":false}' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records/$APEX_RECORD_ID"

# If nothing at apex, POST a new ALIAS:
curl -X POST \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '[{"name":"example.com","type":"ALIAS","content":"<netlify-project>.netlify.app","ttl":3600,"prio":0,"disabled":false}]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records"
```

**If IONOS rejects `ALIAS`** (422 on the type), fall back to an `A` record pointing at Netlify's load balancer:

```bash
curl -X POST \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '[{"name":"example.com","type":"A","content":"75.2.60.5","ttl":3600,"prio":0,"disabled":false}]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records"
```

The `75.2.60.5` load-balancer IP may change. If Netlify's dashboard advertises a different apex target, use that. Hard-coded IPs go stale.

## Step 6 — Set the `www` CNAME

```bash
# Delete any A/AAAA records at www.example.com first (CNAME exclusivity).
# Then create the CNAME:
curl -X POST \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '[{"name":"www.example.com","type":"CNAME","content":"<netlify-project>.netlify.app","ttl":3600,"prio":0,"disabled":false}]' \
  "https://api.hosting.ionos.com/dns/v1/zones/$ZONE_ID/records"
```

## Step 7 — Attach the Custom Domain in Netlify

```bash
curl -X PATCH \
  -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain":"example.com","domain_aliases":["www.example.com"]}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

Netlify will now verify DNS and provision SSL. Check status:

```bash
curl -s -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl" | python3 -m json.tool
```

Poll until `state == "issued"` (typically 1–10 minutes after DNS resolves correctly).

## Step 8 — Verify

```bash
# DNS resolves to Netlify
dig @8.8.8.8 example.com +short
dig @8.8.8.8 www.example.com +short

# HTTPS responds with valid cert
curl -I https://example.com
curl -I https://www.example.com
```

Expected: both return 200 (or 301 if you configured a redirect), with a valid Let's Encrypt cert covering both names.

## Rollback

If something breaks after Step 5 or 6:

1. Find the snapshot from Step 2
2. For each changed record, PUT back the original `content`+`ttl`+`prio`
3. Or, if multiple records changed, restore via bulk PUT of the snapshot's `records` array (after confirming it's complete)

If Step 7 succeeded but should be reverted:

```bash
curl -X PATCH \
  -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain":null,"domain_aliases":[]}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---|---|---|
| `dig` still shows old IP | TTL hasn't expired yet | Wait TTL seconds, or flush local resolver |
| SSL stuck `pending` >10min | DNS hasn't propagated globally, or conflicting records exist | `dig @1.1.1.1` and `dig @8.8.8.8` to check multi-resolver; fix records |
| Browser shows cert warning | Netlify hasn't provisioned cert yet OR accessing via IP | Wait; always access via hostname |
| Email stops working | MX records accidentally removed | Restore from snapshot |
| `www` returns 404 | CNAME points to wrong project, or Netlify `domain_aliases` missing | Verify CNAME target and Netlify domain_aliases field |
| 409 on record create | Conflicting record exists (CNAME exclusivity) | GET records at that name; delete the conflicting one first |
