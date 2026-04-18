# Pointing a Cloudflare Domain at a Netlify Project

End-to-end walkthrough for the primary use case: a domain whose DNS lives on Cloudflare, being pointed at a site deployed via `netlify-landing-page-deploy`.

This is the Cloudflare-specific expansion of the cross-skill DNS-to-Netlify pattern (same outcome as `ionos-dns-management/docs/netlify-pointing.md`, different provider).

## Assumptions

- Environment: `CLOUDFLARE_API_TOKEN` and `NETLIFY_PERSONAL_ACCESS_TOKEN` set
- Netlify project already exists with a known `site_id`
- Domain's nameservers point to Cloudflare (confirm with `dig NS`)
- The Cloudflare token has `Zone:DNS:Edit` + `Zone:Zone:Read` on the target zone

## Why Cloudflare Is Easier Than Most Providers

Cloudflare supports **CNAME flattening at the apex**. On IONOS, Netlify, Route 53, and most others, you need A records with hardcoded IPs for the bare domain (or an ALIAS/ANAME extension). On Cloudflare you just CNAME the apex to `<project>.netlify.app` and it works.

Result: both apex and www use the same CNAME target. No hardcoded IPs. No ALIAS workaround. If Netlify ever re-numbers their infrastructure, nothing in your zone needs to change.

## Step 0 — Sanity Checks

```bash
# Cloudflare auth
curl -s -o /dev/null -w "CF %{http_code}\n" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  https://api.cloudflare.com/client/v4/user/tokens/verify

# Netlify auth
curl -s -o /dev/null -w "Netlify %{http_code}\n" \
  -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  https://api.netlify.com/api/v1/sites

# Nameservers for target domain
dig @8.8.8.8 example.com NS +short
# Expected: *.ns.cloudflare.com
```

## Step 1 — Find the Zone ID

```bash
ZONE_ID=$(curl -s \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['result'][0]['id'])")
echo "Zone: $ZONE_ID"
```

If empty, the token isn't scoped to this zone — re-create it.

## Step 2 — Snapshot the Zone

```bash
mkdir -p /tmp/dns-backup
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?per_page=5000" \
  | python3 -m json.tool \
  > /tmp/dns-backup/example.com-cf-$(date +%Y%m%dT%H%M%S).json
```

Present a summary to the user:

```bash
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?per_page=5000" \
  | python3 -c "
import json, sys
recs = json.load(sys.stdin)['result']
for r in recs:
    proxy = '☁️ ' if r.get('proxied') else '🔒'
    print(f\"{proxy} {r['type']:6} {r['name']:40} -> {r.get('content', r.get('data', '-'))}  ttl={r['ttl']}\")"
```

## Step 3 — Identify Records to Change

You need exactly two records:

| Purpose | Name | Target | proxied |
|---|---|---|---|
| Apex | `example.com` | `<project>.netlify.app` | `false` |
| www | `www.example.com` | `<project>.netlify.app` | `false` |

Both as CNAMEs. The apex CNAME is legal because Cloudflare flattens.

Check for conflicts:
- Any existing `A` or `AAAA` at apex → must delete before creating apex CNAME
- Any existing `A`, `AAAA`, `MX`, `TXT` at `www.example.com` → must delete before creating www CNAME
- **Don't touch** MX, SPF TXT, DKIM CNAMEs, DMARC TXT, or any other record

## Step 4 — Apply the Changes (Batch)

This is the ideal batch-operation use case. One atomic call replaces old records with new ones.

```bash
# First, fetch IDs of any conflicting records
APEX_OLD_IDS=$(curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=example.com&type=A" \
  | python3 -c "import json,sys; print(','.join(r['id'] for r in json.load(sys.stdin)['result']))")

WWW_OLD_IDS=$(curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=www.example.com" \
  | python3 -c "import json,sys; print(','.join(r['id'] for r in json.load(sys.stdin)['result']))")

# Build the batch payload (Python, for clarity)
python3 - <<'PY' | tee /tmp/batch-payload.json
import json, os
deletes = []
for ids in (os.environ.get('APEX_OLD_IDS',''), os.environ.get('WWW_OLD_IDS','')):
    for i in ids.split(','):
        if i: deletes.append({'id': i})
print(json.dumps({
  "deletes": deletes,
  "posts": [
    {"type": "CNAME", "name": "example.com",     "content": "NETLIFY_PROJECT.netlify.app", "ttl": 1, "proxied": False, "comment": "Apex → Netlify (CF flattened)"},
    {"type": "CNAME", "name": "www.example.com", "content": "NETLIFY_PROJECT.netlify.app", "ttl": 1, "proxied": False, "comment": "www → Netlify"}
  ]
}, indent=2))
PY

# After reviewing the payload with the user, execute:
curl -X POST \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch-payload.json \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/batch"
```

Replace `NETLIFY_PROJECT` with your actual project name.

**Atomicity note:** the batch processes `deletes` before `posts`, so the old A records are gone before the new CNAMEs are attempted — no CNAME-exclusivity 409.

## Step 5 — Attach the Custom Domain in Netlify

```bash
curl -X PATCH \
  -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain": "example.com", "domain_aliases": ["www.example.com"]}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

Netlify now starts provisioning the SSL cert. Because the CF records are `proxied: false`, the ACME challenge reaches Netlify directly.

Check SSL state:

```bash
curl -s -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl" | python3 -m json.tool
```

Poll until `state == "issued"` — usually 1–5 minutes.

## Step 6 — Verify

```bash
# DNS resolves to Netlify (not Cloudflare IPs, because proxied: false)
dig @8.8.8.8 example.com +short
dig @8.8.8.8 www.example.com +short

# Both should resolve to Netlify load balancer IPs (e.g., 75.2.60.5 or a geo-routed alternate)

# HTTPS with valid cert
curl -I https://example.com
curl -I https://www.example.com
```

Expected: `HTTP/2 200` (or 301 if you've configured www→apex redirect), `server: Netlify`, Let's Encrypt cert.

## Step 7 (Optional) — Enable Proxying Later

Once you've confirmed the site works and Netlify has a valid cert, you can optionally flip `proxied` to `true` to pull traffic through Cloudflare's CDN:

1. In Cloudflare dashboard, set SSL/TLS mode to `Full (strict)` (`SSL/TLS > Overview`)
2. PATCH both records to `proxied: true`:
   ```bash
   for ID in $APEX_CNAME_ID $WWW_CNAME_ID; do
     curl -X PATCH \
       -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"proxied": true}' \
       "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$ID"
   done
   ```
3. Verify the site still loads and cert chain is still valid (should be the Netlify LE cert via CF termination with Universal SSL in front)

For a pure static Netlify site this is usually a net win — CF CDN edge + DDoS protection on top of Netlify's hosting. Don't do this for dynamic/API-heavy sites without a caching strategy.

## Rollback

Snapshot from Step 2 is your safety net. To revert the apex + www to the prior state, either:

1. **Targeted rollback:** delete the new CNAMEs, POST back the original A records from the snapshot
2. **Full batch rollback:** construct a batch that deletes the new records and posts the old ones from the snapshot

```bash
# Example targeted rollback (manual IDs from snapshot)
curl -X POST \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "deletes": [
      {"id": "<new-apex-cname-id>"},
      {"id": "<new-www-cname-id>"}
    ],
    "posts": [
      {"type":"A","name":"example.com","content":"<original-ip>","ttl":3600,"proxied":false},
      {"type":"A","name":"www.example.com","content":"<original-ip>","ttl":3600,"proxied":false}
    ]
  }' \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/batch"
```

Also detach the domain from Netlify if rolling back fully:

```bash
curl -X PATCH \
  -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain": null, "domain_aliases": []}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---|---|---|
| SSL stuck "Waiting for DNS" on Netlify | `proxied: true` on the CF records | PATCH to `proxied: false`, wait a few minutes |
| `curl https://example.com` returns wrong cert | Same as above, or you're hitting the CF edge with no CF cert for the hostname | Flip proxied to false |
| 404 at apex but www works | Apex CNAME didn't get created, or conflicted with old A | Re-run batch; check Cloudflare dashboard for the apex record |
| Cert issued but browser still shows warning | Browser cached old cert / HSTS from prior attempt | Hard reload, or test in incognito |
| Email stops working | MX or TXT records were accidentally deleted in the batch | Restore from snapshot |
| Batch returns 409 | Deletes didn't cover all conflicting records | Re-query name for ALL types, add each to `deletes` |
