# DNS Migration Checklist

Use when moving an existing domain to Netlify-authoritative DNS (Scenario A in SKILL.md). The risk is losing email or SaaS records during the cutover.

## Phase 0 — Discover (before touching anything)

Enumerate everything currently published under the domain:

```bash
DOMAIN=example.com
for TYPE in A AAAA CNAME MX TXT NS SRV CAA; do
  echo "=== $TYPE ==="
  dig @8.8.8.8 $DOMAIN $TYPE +short
done
dig @8.8.8.8 _dmarc.$DOMAIN TXT +short
dig @8.8.8.8 mail._domainkey.$DOMAIN TXT +short   # DKIM, common selector
dig @8.8.8.8 www.$DOMAIN +short
```

Common subdomains to check: `www`, `mail`, `autodiscover`, `autoconfig`, `_dmarc`, `_domainkey`, `selector1._domainkey`, `selector2._domainkey`, any CNAME for SaaS (`help`, `status`, `docs`, `app`, `api`).

Save the output: `dig any $DOMAIN > /tmp/pre-migration-$(date +%s).txt`

## Phase 1 — Pre-Migration Prep

1. **Lower TTLs** on all existing records to 300s (5 minutes). Done at the current DNS provider, 24h before the cutover. This means if anything breaks, rollback takes minutes, not hours.
2. **Confirm email provider**. Most common targets: Google Workspace, Microsoft 365, Fastmail, ProtonMail, self-hosted. Record their required MX, SPF (TXT), DKIM (TXT), DMARC (TXT) values.
3. **Confirm any SaaS records**. Domain verification TXTs (Google Search Console, Bing, Atlassian, Slack), CNAMEs for help/docs portals, etc.
4. **Note current nameservers** (for rollback): `dig @8.8.8.8 $DOMAIN NS +short`

## Phase 2 — Create Zone and Records at Netlify

1. Create the DNS zone (`POST /dns_zones`)
2. Re-create every discovered record in the Netlify zone **before** flipping nameservers:
   - MX records (preserve priority)
   - SPF TXT
   - DKIM TXT (one per selector)
   - DMARC TXT at `_dmarc`
   - Any SaaS verification TXTs
   - Any service CNAMEs (`help`, `status`, `docs`, etc.)
3. Verify records resolve against Netlify's nameservers directly (bypasses delegation):
   ```bash
   dig @dns1.p01.nsone.net $DOMAIN MX +short
   dig @dns1.p01.nsone.net $DOMAIN TXT +short
   ```
   Compare to Phase 0 output — everything should match.

## Phase 3 — Flip Nameservers

Update NS records at the registrar to the 4 Netlify nameservers from the zone creation response. Then wait.

```bash
# Poll propagation from public resolvers
while true; do
  ns=$(dig @8.8.8.8 $DOMAIN NS +short | tr '\n' ' ')
  echo "$(date +%H:%M:%S) → $ns"
  [[ "$ns" == *"nsone"* ]] && break
  sleep 60
done
```

Typical propagation: 15 min – 2h. Max 48h. Monitor mail flow and site reachability during this window.

## Phase 4 — Attach Custom Domain to Project

```bash
curl -X PATCH -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"custom_domain": "example.com"}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

Netlify auto-creates the apex record and provisions SSL. Check SSL state:

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/ssl" | python3 -m json.tool
```

Wait for `state: "issued"`.

## Phase 5 — Post-Migration Verification

- [ ] `https://example.com` returns 200 with valid cert
- [ ] `https://www.example.com` returns 200 with valid cert
- [ ] Send a test email **to** an address at the domain — it arrives
- [ ] Send a test email **from** the domain to Gmail/Outlook — it arrives, not in spam
- [ ] Check `mail-tester.com` score (aim for 10/10)
- [ ] Any SaaS integrations (Slack, Atlassian, etc.) still report the domain as verified
- [ ] DMARC reports (if aggregation configured) aren't showing new fails

## Rollback

If anything breaks in Phase 3:

1. Revert registrar NS records to the original nameservers (saved in Phase 1 step 4)
2. Due to low TTL (Phase 1 step 1), resolvers flip back within 5 minutes
3. Diagnose the issue against the Netlify zone before re-attempting

## Common Gotchas

| Symptom | Fix |
|---|---|
| Email stops delivering after nameserver flip | MX records were not copied into the Netlify zone before flip. Add them, wait for propagation. |
| Gmail marks outbound mail as spam | SPF or DKIM TXT record missing or mistyped. Compare Netlify zone to original verbatim. |
| SaaS integration shows "domain unverified" | Verification TXT record was scoped to a subdomain that wasn't copied. Add it. |
| SSL stuck `pending` | DNS hasn't propagated yet, or wildcard conflicts exist. Wait 15 min; if still stuck, POST to `/ssl` to retry. |
| Netlify says "domain already in use" | Domain is attached to another project on the account. Detach from the other project first. |
