# Droplets Reference

Droplets are Linux VMs. Use them when App Platform's abstractions don't fit — custom daemons, game servers, VPN endpoints, one-off experiments, or self-managed databases.

Rule of thumb: **if App Platform can run it, use App Platform.** Droplets trade managed convenience for full OS control, and that control is usually the liability, not the asset.

## Droplet Object

Key fields from `GET /v2/droplets/{id}`:

| Field | Type | Description |
|---|---|---|
| `id` | int | Droplet ID |
| `name` | string | User-chosen hostname |
| `memory` | int | RAM in MB |
| `vcpus` | int | |
| `disk` | int | GB |
| `region` | object | `{slug, name, ...}` |
| `image` | object | Base image (slug or custom image ID) |
| `size_slug` | string | e.g. `s-1vcpu-2gb` |
| `status` | string | `new`, `active`, `off`, `archive` |
| `networks.v4` | array | IPv4 IPs (public + private) |
| `networks.v6` | array | IPv6 IPs |
| `ssh_keys` | int[] | IDs of injected keys |
| `backup_ids` | int[] | Automatic backups (if enabled) |
| `snapshot_ids` | int[] | Manual snapshots |
| `vpc_uuid` | UUID | VPC membership |
| `tags` | string[] | Free-form labels |

## Sizes

Droplet sizes come in families with growing vCPU/RAM.

### Basic (shared CPU, cheapest)
| Slug | vCPU | RAM | Disk | ~$/mo |
|---|---|---|---|---|
| `s-1vcpu-512mb-10gb` | 1 | 512 MB | 10 GB | $4 |
| `s-1vcpu-1gb` | 1 | 1 GB | 25 GB | $6 |
| `s-1vcpu-2gb` | 1 | 2 GB | 50 GB | $12 |
| `s-2vcpu-2gb` | 2 | 2 GB | 60 GB | $18 |
| `s-2vcpu-4gb` | 2 | 4 GB | 80 GB | $24 |
| `s-4vcpu-8gb` | 4 | 8 GB | 160 GB | $48 |

### Premium (NVMe disks, Intel/AMD CPU choice)
`s-*-premium-intel`, `s-*-premium-amd`. ~20% pricier than Basic, noticeably faster disk I/O.

### General Purpose, CPU-Optimized, Memory-Optimized, Storage-Optimized
For specialized workloads. See DO pricing page.

## Images

### Distribution slugs (latest LTS snapshots)

| Slug | OS |
|---|---|
| `ubuntu-24-04-x64` | Ubuntu 24.04 LTS (Noble) |
| `ubuntu-22-04-x64` | Ubuntu 22.04 LTS (Jammy) |
| `debian-12-x64` | Debian 12 Bookworm |
| `fedora-40-x64` | Fedora 40 |
| `rocky-9-x64` | Rocky Linux 9 |
| `centos-stream-9-x64` | CentOS Stream 9 |

### Marketplace images

One-click apps bundled with stacks (LAMP, LEMP, Docker pre-installed, WordPress, etc.). Use `marketplace` service to browse slugs.

### Custom images

Upload a raw disk image (qcow2 / vmdk / vhdx) via `images` endpoint, then boot Droplets from the resulting image ID.

## Creating a Droplet

Via MCP (`droplet-create`) or API:

```bash
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-01",
    "region": "nyc3",
    "size": "s-1vcpu-2gb",
    "image": "ubuntu-24-04-x64",
    "ssh_keys": [<your-ssh-key-id-or-fingerprint>],
    "backups": false,
    "ipv6": true,
    "monitoring": true,
    "tags": ["prod", "web"],
    "vpc_uuid": "<optional-vpc-id>",
    "user_data": "#cloud-config\nruncmd:\n  - apt-get update\n  - apt-get install -y nginx"
  }' \
  https://api.digitalocean.com/v2/droplets
```

Notes:
- `ssh_keys` — pass IDs or fingerprints. **Required for key-based login**; omit it and the Droplet ships with password auth only, with the password emailed (if that's still supported in your account).
- `monitoring: true` — installs the DO agent for metrics (CPU, memory, disk, bandwidth graphs in dashboard).
- `backups: true` — weekly automatic backups at ~20% of Droplet cost. Worth it for anything with state.
- `user_data` — cloud-init script that runs on first boot. Use for bootstrap.

## Post-Provision: cloud-init

cloud-init is the standard way to automate first-boot setup. Example:

```yaml
#cloud-config
package_update: true
package_upgrade: true
packages:
  - nginx
  - ufw
  - fail2ban
runcmd:
  - ufw allow 22
  - ufw allow 80
  - ufw allow 443
  - ufw --force enable
  - systemctl enable nginx
  - systemctl start nginx
users:
  - name: deploy
    groups: sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
```

Pass as the `user_data` field. cloud-init logs to `/var/log/cloud-init-output.log` — check there if something didn't run.

## SSH Keys

Upload once, reference in every Droplet create:

```bash
# Upload
curl -X POST -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"my-laptop\",\"public_key\":\"$(cat ~/.ssh/id_ed25519.pub)\"}" \
  https://api.digitalocean.com/v2/account/keys

# List
curl -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  https://api.digitalocean.com/v2/account/keys
```

The `fingerprint` field returned is what you pass to `droplet-create`.

## Actions (async)

Power, resize, rebuild, snapshot operations are async. Triggering returns an `action_id`; poll `/v2/actions/{id}` for status.

| Action | Irreversible? | Notes |
|---|---|---|
| `power_off` / `power_on` / `reboot` | No | Graceful by default |
| `shutdown` | No | Sends SIGTERM, waits; harder than `power_off` |
| `resize` | No (but requires power off) | `disk: true` resize is one-way — can't shrink back |
| `rebuild` | **Yes** | Wipes disk, installs image from scratch |
| `snapshot` | No | Creates a reusable image; Droplet powers down briefly unless you allow live snapshots |
| `enable_backups` / `disable_backups` | No | — |
| `enable_ipv6` | No | — |

## Snapshots vs. Backups

- **Backups** — weekly, automatic, up to 4 retained, ~20% Droplet cost
- **Snapshots** — on-demand, priced per GB-month (~$0.06/GB-month), no retention limit

For one-time preservation (pre-upgrade, pre-destructive-change), snapshots. For ongoing insurance, backups.

## Networking

### Public vs. Private IPs

Every Droplet has a public IPv4. Optional private IPv4 (via VPC membership) for internal traffic — no bandwidth charges on private network.

### VPCs

`vpc_uuid` at create time puts the Droplet in a private network. Default VPC per region is created automatically. For multi-tier apps (web → app → db), use custom VPCs and route through firewalls.

### Firewalls

DO-managed cloud firewalls attach to tag(s). All Droplets with the matching tag inherit the rules. Managed separately from OS-level `ufw`/`iptables` — both can exist. The cloud firewall is the first filter (drops at DO's edge).

Template for a standard web Droplet:
```json
{
  "name": "web-firewall",
  "inbound_rules": [
    {"protocol":"tcp","ports":"22","sources":{"addresses":["<your-ip>/32"]}},
    {"protocol":"tcp","ports":"80","sources":{"addresses":["0.0.0.0/0","::/0"]}},
    {"protocol":"tcp","ports":"443","sources":{"addresses":["0.0.0.0/0","::/0"]}}
  ],
  "outbound_rules": [
    {"protocol":"tcp","ports":"all","destinations":{"addresses":["0.0.0.0/0","::/0"]}},
    {"protocol":"udp","ports":"all","destinations":{"addresses":["0.0.0.0/0","::/0"]}},
    {"protocol":"icmp","destinations":{"addresses":["0.0.0.0/0","::/0"]}}
  ],
  "tags": ["web"]
}
```

## Destroying Droplets

`DELETE /v2/droplets/{id}` is immediate and permanent. Data is gone unless you have a snapshot or backup.

**Safety rule from SKILL.md:** always confirm with the user before destroying. The MCP tool should be treated like `rm -rf`.

## Common Patterns

### Pet vs. cattle

- **Pet** — one Droplet, named thoughtfully, hand-maintained. Fine for side projects and dev servers. Restore from backup/snapshot on failure.
- **Cattle** — identical Droplets behind a load balancer, provisioned from a snapshot or cloud-init. Any node can be killed and re-created. Fine for web apps.

Don't build cattle infrastructure for a single-instance personal project; the overhead isn't worth it. Don't run a production multi-user service as a pet; the bus factor is too high.

### Moving from Droplet to App Platform

If you started on a Droplet and the app outgrows hand-maintenance, App Platform is the usual next step. Path: containerize the app → push to DOCR → create App Platform app pointing at the image → update DNS → destroy the Droplet once the new deployment is verified.

## Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| Can't SSH after create | SSH key wasn't included in `ssh_keys`; or root login is disabled and you created a user via cloud-init but SSH'd as root |
| cloud-init didn't run what I expected | Syntax error in user_data; check `/var/log/cloud-init-output.log` |
| Droplet reachable but web server isn't | Cloud firewall blocks the port, or `ufw` blocks, or the app binds to `127.0.0.1` not `0.0.0.0` |
| Resize stuck | Droplet must be powered off for disk resize; CPU/RAM-only resize can be live |
| Billing higher than expected | Snapshots accumulate; enable_backups on all Droplets adds ~20%; bandwidth overage for >4TB egress |
