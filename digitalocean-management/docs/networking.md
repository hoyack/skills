# Networking Reference

Covers domains, DNS records, load balancers, firewalls, VPCs, floating IPs, and CDN — everything under the `networking` MCP service.

**Scope reminder:** DO's DNS management only applies to domains using DO nameservers. For domains hosted on IONOS, use `ionos-dns-management`; for Netlify-hosted DNS, `netlify-dns`.

## Domains and DNS

### Delegating a domain to DO

1. Create the domain in DO:
   ```bash
   curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "example.com", "ip_address": "192.0.2.1"}' \
     https://api.digitalocean.com/v2/domains
   ```
   (`ip_address` is optional — just auto-creates an A record at apex.)

2. Update nameservers at the registrar to:
   - `ns1.digitalocean.com`
   - `ns2.digitalocean.com`
   - `ns3.digitalocean.com`

3. Propagation: usually under 1 hour.

### Domain Record Object

| Field | Type | Description |
|---|---|---|
| `id` | int | Record ID |
| `type` | string | `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`, `SRV`, `CAA` |
| `name` | string | Subdomain (`www`, `@` for apex, `*` for wildcard) |
| `data` | string | Record value |
| `priority` | int | MX/SRV only |
| `port` | int | SRV only |
| `ttl` | int | Default 1800 |
| `weight` | int | SRV only |
| `flags` | int | CAA only |
| `tag` | string | CAA only |

Note: DO's `name` is **subdomain-relative** (`www` not `www.example.com`). This is opposite to IONOS's API which uses FQDN.

### Record CRUD

**Create:**
```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"www","data":"192.0.2.1","ttl":3600}' \
  https://api.digitalocean.com/v2/domains/example.com/records
```

**List:**
```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  https://api.digitalocean.com/v2/domains/example.com/records
```

**Update:**
```bash
curl -X PUT -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data":"192.0.2.2"}' \
  https://api.digitalocean.com/v2/domains/example.com/records/<record-id>
```

**Delete:**
```bash
curl -X DELETE -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  https://api.digitalocean.com/v2/domains/example.com/records/<record-id>
```

### Pointing a domain at an App Platform app

Preferred pattern:

1. Add the domain to the app spec's `domains` array with `type: PRIMARY`
2. DO exposes the correct CNAME target (or auto-creates A records if the domain is in DO DNS)
3. SSL provisions automatically

If the app's domain is hosted elsewhere (e.g., IONOS), skip step 2 on DO and use the DNS provider skill to add the CNAME to `<app-name>-<hash>.ondigitalocean.app`.

### Apex domain (CNAME-like at root)

DO doesn't have an explicit `ALIAS` type. For the apex → App Platform, either:
- Put the domain on DO DNS (which auto-supports apex CNAME behind the scenes), or
- Use A records at a DO Droplet's floating IP

## Load Balancers

DO Load Balancers distribute traffic across Droplets or App Platform components.

### When to use

- Multiple Droplets serving the same app (cattle pattern)
- Canary / blue-green deployments
- Mixing HTTP and TCP workloads behind one endpoint

### Object Shape (selected fields)

| Field | Description |
|---|---|
| `id` | UUID |
| `name` | |
| `ip` | Public IPv4 |
| `algorithm` | `round_robin`, `least_connections` |
| `status` | `new`, `active`, `errored` |
| `forwarding_rules` | array — per-protocol inbound→target mappings |
| `health_check` | HTTP/HTTPS/TCP probe settings |
| `droplet_ids` | Attached Droplets |
| `tag` | Tag-based membership |
| `redirect_http_to_https` | bool |
| `enable_proxy_protocol` | bool |

### Minimal HTTPS LB spec

```json
{
  "name": "web-lb",
  "region": "nyc3",
  "forwarding_rules": [
    {
      "entry_protocol": "https",
      "entry_port": 443,
      "target_protocol": "http",
      "target_port": 80,
      "certificate_id": "<cert-uuid>"
    }
  ],
  "health_check": {
    "protocol": "http",
    "port": 80,
    "path": "/health",
    "check_interval_seconds": 10,
    "response_timeout_seconds": 5,
    "unhealthy_threshold": 3,
    "healthy_threshold": 2
  },
  "tag": "web",
  "redirect_http_to_https": true
}
```

Tag-based targeting auto-adds/removes Droplets as you spin them up/down with the `web` tag.

### Certificates

LBs terminate TLS. Supply a certificate via:
- **Let's Encrypt** — DO auto-provisions if the LB has a DO-managed domain attached
- **Uploaded** — bring your own via `/v2/certificates` endpoint

## Firewalls

Applied at DO's edge, **before** the Droplet's OS firewall. Managed by tag, so you manage rules once and all tagged Droplets inherit them.

### Object Shape

```json
{
  "name": "web-firewall",
  "inbound_rules": [
    {"protocol": "tcp", "ports": "22", "sources": {"addresses": ["203.0.113.5/32"]}},
    {"protocol": "tcp", "ports": "443", "sources": {"addresses": ["0.0.0.0/0", "::/0"]}}
  ],
  "outbound_rules": [
    {"protocol": "tcp", "ports": "all", "destinations": {"addresses": ["0.0.0.0/0", "::/0"]}}
  ],
  "droplet_ids": [],
  "tags": ["web"]
}
```

`sources` / `destinations` can also reference `droplet_ids`, `load_balancer_uids`, `kubernetes_ids`, `tags`. Inter-resource rules are better than raw CIDRs — they follow resources as they're replaced.

## VPCs

Private networks for DO resources. Every region has a default VPC; custom VPCs let you segment multi-tier apps.

### Creating a VPC

```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"prod-vpc","region":"nyc3","ip_range":"10.10.0.0/16"}' \
  https://api.digitalocean.com/v2/vpcs
```

Droplets in the same VPC get private IPs in the VPC range; private traffic doesn't count toward bandwidth billing.

## Floating IPs / Reserved IPs

Static IPv4 addresses you can attach to a Droplet. Useful for:
- Fast failover (move the IP to a replacement Droplet during incidents)
- Stable public IP across Droplet rebuilds
- Whitelisting: give a third party a stable IP that represents your infrastructure

```bash
# Reserve
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"region":"nyc3"}' \
  https://api.digitalocean.com/v2/floating_ips

# Assign to a Droplet
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"assign","droplet_id":<id>}' \
  https://api.digitalocean.com/v2/floating_ips/<ip>/actions
```

Unassigned floating IPs accrue a small charge (~$4/mo) — don't hoard them.

## CDN

DO CDN is a wrapper around Spaces (object storage) — you can't CDN arbitrary origins. For pure static asset delivery:

1. Create a Space
2. Enable CDN on the Space
3. Optional: attach a custom domain (requires uploading/provisioning a cert)
4. Use `cdn-flush-cache` after deploying new assets

```bash
# Create endpoint (auto-created when you toggle CDN on a Space)
# Flush cache:
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"files": ["/images/hero.jpg", "/js/app.*.js"]}' \
  https://api.digitalocean.com/v2/cdn/endpoints/<endpoint-id>/cache
```

For HTML/SPA CDN-ing an arbitrary origin, use Netlify or Cloudflare; DO CDN isn't the right tool.

## Patterns

### Standard web app stack

1. **VPC** (custom, for isolation) — `10.20.0.0/16`
2. **Firewall** tagged `web` — inbound 443 from internet, 22 from ops IP
3. **Load balancer** in front of tagged Droplets — terminates TLS
4. **N Droplets** with tag `web` — app behind the LB
5. **Database** (managed) — trusted source: `type: "tag", value: "web"`
6. **Floating IP** on the LB (optional; helps with registrar-facing DNS migrations)
7. **DNS record** at your DNS provider → LB's public IP

### Multi-service app with single public face

Use a single LB fronting multiple apps on different paths using `sticky_sessions` and path-based forwarding rules (LBs support basic HTTP routing via the dashboard; API config is spec-heavy).

## Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| DNS change not propagating | Domain not on DO nameservers — check `dig NS` |
| LB shows all Droplets unhealthy | Health-check path returns non-2xx, or Droplets bind to `127.0.0.1` |
| Firewall change doesn't apply | Firewall attached to tag; Droplet missing the tag |
| SSL cert stuck | LB's domain not in DO DNS, or cert provisioning delayed; check LB status |
| Floating IP bill surprise | Unassigned floating IP left lying around |
| `www` subdomain works, apex doesn't | Registered A record at `@` but points to an App Platform domain (which needs CNAME); add the domain inside the app spec instead |
