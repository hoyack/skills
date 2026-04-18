# Proxy Mode: Orange Cloud vs Grey Cloud

The `proxied` boolean on a DNS record is Cloudflare's single most distinctive feature. Getting it right is the difference between a site that works and one that returns cryptic SSL errors.

## What `proxied` Actually Does

### `proxied: true` (orange cloud ☁️)

- DNS responses return **Cloudflare's IPs**, not the origin's IP
- All HTTP/HTTPS traffic to the hostname flows through Cloudflare's edge
- Cloudflare applies its CDN, WAF, rate limiting, firewall rules, caching, analytics, etc.
- Origin's real IP is hidden from the public
- TLS: Cloudflare terminates TLS at the edge using its own cert (Universal SSL), then re-connects to the origin per the zone's SSL/TLS mode (`Flexible`, `Full`, `Full (strict)`, `Strict`)

### `proxied: false` (grey cloud 🔒)

- DNS responses return the **origin's actual IP/target**
- Traffic goes directly to the origin — Cloudflare isn't in the path
- No CDN, no WAF, no Cloudflare features
- TLS is handled entirely by the origin

## Why It Matters for Hosted PaaS

Most PaaS providers (Netlify, Vercel, Render, DigitalOcean App Platform, Fly.io) handle TLS themselves using Let's Encrypt — they provision a cert for your custom domain automatically.

For that provisioning to work, **the PaaS needs the domain's DNS to resolve to them, not to Cloudflare.** The LE challenge (HTTP-01 or TLS-ALPN-01) goes to wherever DNS says the site lives. If DNS returns Cloudflare's IPs (`proxied: true`), the PaaS never gets the challenge and can't issue a cert.

Result: `proxied: true` on a Netlify-targeted record causes Netlify to sit in "provisioning SSL" forever, and visitors get cert errors.

**Rule: when pointing at a PaaS that handles its own TLS, use `proxied: false`.**

## Decision Matrix by Destination

| Destination | Recommended `proxied` | Why |
|---|---|---|
| Netlify | `false` | Netlify handles SSL; proxying breaks LE provisioning |
| Vercel | `false` | Same |
| DigitalOcean App Platform | `false` (at first) | Same; can enable later if you don't mind Cloudflare terminating TLS |
| Render | `false` | Same |
| Fly.io | `false` | Same |
| Netlify Forms endpoint | `false` | Post-to-/ handling relies on Netlify seeing the true Host header |
| Raw DigitalOcean Droplet running nginx + LE | `false` (at first) | Your origin needs the real HTTP-01 challenge |
| Raw Droplet where YOU want Cloudflare CDN/WAF | `true` with `Full (strict)` | Set zone SSL mode to `Full (strict)`, use a real cert on origin |
| S3 static website | `true` | No TLS on origin; Cloudflare does it. Set SSL mode to `Flexible` |
| Managed DB (Postgres, Mongo, etc.) | `false` | Non-HTTP traffic; proxy only works for HTTP/HTTPS |
| MX record target | N/A (not proxiable) | MX is never proxied |
| SSH, SFTP, IRC, raw TCP/UDP | `false` | Cloudflare proxy only handles HTTP/S on standard ports (80/443/plus a few alternates on paid plans) |

## When You CAN Enable Proxying

After a Netlify/Vercel/etc. site is fully provisioned and running happily, you CAN switch to `proxied: true` IF:

1. You set the zone's SSL/TLS mode to `Full (strict)` in the Cloudflare dashboard
2. The PaaS's certificate is valid and trusted (Let's Encrypt is trusted by Cloudflare)
3. You understand that now Cloudflare caches and rewrites responses — some dynamic-API calls may need Page Rules to bypass cache

For a pure marketing site, enabling proxy afterwards gives CDN acceleration and basic DDoS protection for free. For an API-heavy app, the caching gotchas aren't worth it unless you're ready to tune it.

## What Breaks When You Get It Wrong

**`proxied: true` but PaaS needs to provision SSL:**
- Netlify dashboard shows SSL stuck in "Waiting for DNS"
- `curl https://example.com` returns `curl: (60) SSL certificate problem`
- Or Cloudflare returns a self-signed "Cloudflare Universal SSL" cert that doesn't cover your hostname (the `:443` on CF edge IPs serves whatever Universal SSL cert matches, which is just the naked IP, not your hostname)

**Fix:** flip to `proxied: false`, wait TTL seconds, retry PaaS provisioning.

**`proxied: false` when you meant true:**
- No practical break — site works, just skips CDN/WAF
- You'll notice because traffic analytics at Cloudflare stay at zero for that hostname

**`proxied: true` on an MX record:**
- API silently ignores the flag (MX isn't proxiable)
- No actual break; just confusing if you expected CDN-like behavior

**`proxied: true` on an A record for SSH:**
- SSH traffic fails entirely — Cloudflare proxy doesn't forward port 22
- Attempt connection times out or resets

## Zone-Wide SSL/TLS Mode Interaction

The zone-level SSL/TLS mode (set in dashboard at `SSL/TLS > Overview`) dictates how Cloudflare talks to your origin for proxied records:

| Mode | CF→Origin | When to Use |
|---|---|---|
| `Off` | No TLS | Never (insecure) |
| `Flexible` | HTTP | Origin has no HTTPS (e.g., plain S3) — visitors see HTTPS via CF, CF talks to origin over HTTP. Mixed-content risk. |
| `Full` | HTTPS, any cert | Origin has HTTPS but with a self-signed or expired cert. CF doesn't verify. |
| `Full (strict)` | HTTPS, valid cert | Origin has a real cert from a trusted CA. Recommended for prod. |
| `Strict (SSL-only origin pull)` | HTTPS with mutual auth | Requires Cloudflare Origin Certificates. Enterprise-y. |

When using `proxied: false`, the zone SSL/TLS mode doesn't matter for that record — CF isn't in the path.

## Mixed Proxy State Within a Zone

Different records in the same zone can have different `proxied` values. This is normal and often necessary:

```
example.com           CNAME  mysite.netlify.app   proxied: false   (PaaS, needs real host)
static.example.com    CNAME  my-bucket.cdn.com    proxied: true    (behind CF CDN)
mail.example.com      A      192.0.2.1            proxied: false   (mail server, non-HTTP)
ssh.example.com       A      192.0.2.2            proxied: false   (SSH, non-HTTP)
```

The MCP `execute()` doesn't enforce consistency — each record gets its own setting.

## How to Check the Current Setting

```bash
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?proxied=true" \
  | python3 -c "import json,sys; [print(r['name'], r['type'], r['content']) for r in json.load(sys.stdin)['result']]"
```

Or for the zone-wide SSL/TLS mode:
```bash
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
  | python3 -m json.tool
```
