# DigitalOcean MCP Services Reference

Complete reference for all DigitalOcean MCP services, their remote endpoints, tool patterns, and configuration details.

## Table of Contents

1. [Remote MCP Endpoints](#remote-mcp-endpoints)
2. [App Platform (apps)](#app-platform-apps)
3. [Droplets (droplets)](#droplets-droplets)
4. [Databases (databases)](#databases-databases)
5. [Kubernetes — DOKS (doks)](#kubernetes--doks-doks)
6. [Networking (networking)](#networking-networking)
7. [Spaces Storage (spaces)](#spaces-storage-spaces)
8. [Container Registry (container-registry)](#container-registry-container-registry)
9. [Accounts (accounts)](#accounts-accounts)
10. [Insights (insights)](#insights-insights)
11. [Marketplace (marketplace)](#marketplace-marketplace)
12. [Region Reference](#region-reference)
13. [Sizing Reference](#sizing-reference)

---

## Remote MCP Endpoints

Each DigitalOcean service runs as a standalone remote MCP server. Use these URLs if connecting via remote MCP instead of local npx.

| Service | Remote URL | Service Key |
|---------|-----------|-------------|
| App Platform | `https://apps.mcp.digitalocean.com/mcp` | `apps` |
| Droplets | `https://droplets.mcp.digitalocean.com/mcp` | `droplets` |
| Databases | `https://databases.mcp.digitalocean.com/mcp` | `databases` |
| Kubernetes | `https://doks.mcp.digitalocean.com/mcp` | `doks` |
| Networking | `https://networking.mcp.digitalocean.com/mcp` | `networking` |
| Spaces | `https://spaces.mcp.digitalocean.com/mcp` | `spaces` |
| Accounts | `https://accounts.mcp.digitalocean.com/mcp` | `accounts` |
| Insights | `https://insights.mcp.digitalocean.com/mcp` | `insights` |
| Marketplace | `https://marketplace.mcp.digitalocean.com/mcp` | `marketplace` |

Remote endpoints use Bearer token auth:
```
Authorization: Bearer <DIGITALOCEAN_API_TOKEN>
```

---

## App Platform (apps)

The primary deployment service. Handles full-stack applications from Git repos or container registries.

### Key Concepts

- **App** — A collection of components (services, workers, jobs, static sites, databases)
- **Service** — A long-running web process (HTTP server)
- **Worker** — A long-running background process (no HTTP)
- **Job** — A one-off or scheduled task (runs and exits)
- **Static Site** — HTML/CSS/JS served from CDN (similar to Netlify, but within an App Platform app)
- **Database** — A dev database component (limited; use managed databases for production)

### Common Tools

| Tool | Purpose |
|------|---------|
| `app-create` | Create a new app from a Git repo or container image |
| `app-list` | List all apps on the account |
| `app-get` | Get details of a specific app |
| `app-update` | Update app configuration |
| `app-delete` | Delete an app |
| `app-deploy` | Trigger a new deployment |
| `app-logs` | Fetch deployment or runtime logs |
| `app-rollback` | Roll back to a previous deployment |

### App Spec Structure

App Platform uses an "app spec" to define what to deploy. The MCP tools abstract this, but understanding the structure helps:

```yaml
name: my-app
region: nyc
services:
  - name: web
    github:
      repo: owner/repo
      branch: main
    build_command: npm run build
    run_command: npm start
    http_port: 8080
    instance_size_slug: basic-xxs
    instance_count: 1
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
        scope: RUN_TIME
databases:
  - name: db
    engine: PG
    version: "16"
```

### Deployment Sources

App Platform supports deploying from:
- **GitHub** — Public or private repos (requires GitHub app integration)
- **GitLab** — Public or private repos
- **Bitbucket** — Public or private repos
- **Container Registry** — DigitalOcean Container Registry (DOCR), GitHub Container Registry (GHCR), Docker Hub

### Instance Sizes (App Platform)

| Slug | vCPU | RAM | Monthly Cost |
|------|------|-----|-------------|
| `basic-xxs` | Shared | 256 MB | ~$5 |
| `basic-xs` | Shared | 512 MB | ~$10 |
| `basic-s` | Shared | 1 GB | ~$15 |
| `basic-m` | Shared | 2 GB | ~$25 |
| `professional-xs` | 1 | 1 GB | ~$12 |
| `professional-s` | 1 | 2 GB | ~$25 |
| `professional-m` | 2 | 4 GB | ~$50 |
| `professional-l` | 4 | 8 GB | ~$100 |

*Prices approximate; check DigitalOcean pricing page for current rates.*

---

## Droplets (droplets)

Virtual machines (VPS instances). Use when you need full OS control.

### Common Tools

| Tool | Purpose |
|------|---------|
| `droplet-create` | Create a new Droplet |
| `droplet-list` | List all Droplets |
| `droplet-get` | Get details of a specific Droplet |
| `droplet-delete` | Destroy a Droplet |
| `droplet-resize` | Change Droplet size |
| `droplet-action` | Power on/off, reboot, snapshot, rebuild |

### Popular Images

| Image Slug | OS |
|------------|------|
| `ubuntu-24-04-x64` | Ubuntu 24.04 LTS |
| `ubuntu-22-04-x64` | Ubuntu 22.04 LTS |
| `debian-12-x64` | Debian 12 |
| `fedora-40-x64` | Fedora 40 |
| `rocky-9-x64` | Rocky Linux 9 |
| `centos-stream-9-x64` | CentOS Stream 9 |

---

## Databases (databases)

Managed database clusters with automatic backups, failover, and scaling.

### Common Tools

| Tool | Purpose |
|------|---------|
| `database-create` | Provision a new database cluster |
| `database-list` | List all database clusters |
| `database-get` | Get cluster details and connection info |
| `database-delete` | Destroy a cluster |
| `database-resize` | Change cluster size or node count |

### Supported Engines

| Engine | Versions | Slug |
|--------|----------|------|
| PostgreSQL | 14, 15, 16 | `pg` |
| MySQL | 8 | `mysql` |
| Redis | 7 | `redis` |
| MongoDB | 6, 7 | `mongodb` |
| Kafka | 3.5, 3.6, 3.7 | `kafka` |

### Database Sizes

Start small for development:
- `db-s-1vcpu-1gb` — 1 vCPU, 1 GB RAM (~$15/mo)
- `db-s-1vcpu-2gb` — 1 vCPU, 2 GB RAM (~$30/mo)
- `db-s-2vcpu-4gb` — 2 vCPU, 4 GB RAM (~$60/mo)

---

## Kubernetes — DOKS (doks)

Managed Kubernetes clusters.

### Common Tools

| Tool | Purpose |
|------|---------|
| `cluster-create` | Create a Kubernetes cluster |
| `cluster-list` | List all clusters |
| `cluster-get` | Get cluster details |
| `cluster-delete` | Destroy a cluster |
| `nodepool-add` | Add a node pool |
| `nodepool-resize` | Scale a node pool |

---

## Networking (networking)

Domains, DNS records, load balancers, firewalls, VPCs, floating IPs, and CDN.

### Common Tools

| Tool | Purpose |
|------|---------|
| `domain-create` | Register a domain with DO DNS |
| `domain-list` | List all domains |
| `domain-record-create` | Add a DNS record |
| `domain-record-list` | List DNS records for a domain |
| `domain-record-update` | Update a DNS record |
| `domain-record-delete` | Delete a DNS record |
| `load-balancer-create` | Create a load balancer |
| `firewall-create` | Create a firewall |
| `cdn-flush-cache` | Purge CDN cache for a Spaces endpoint |

### DNS Record Types Supported

A, AAAA, CNAME, MX, TXT, NS, SRV, CAA

### Important Note on DNS Scope

DigitalOcean's networking DNS tools only manage domains using DigitalOcean's nameservers:
- `ns1.digitalocean.com`
- `ns2.digitalocean.com`
- `ns3.digitalocean.com`

For domains hosted on IONOS, Cloudflare, Route 53, etc., use the appropriate provider-specific skill.

---

## Spaces Storage (spaces)

S3-compatible object storage with optional CDN.

### Common Tools

| Tool | Purpose |
|------|---------|
| `space-create` | Create a new Space |
| `space-list` | List all Spaces |
| `object-upload` | Upload a file to a Space |
| `object-list` | List objects in a Space |
| `object-delete` | Delete an object |

### Spaces Regions

| Region | Slug |
|--------|------|
| New York | `nyc3` |
| San Francisco | `sfo3` |
| Amsterdam | `ams3` |
| Singapore | `sgp1` |
| Frankfurt | `fra1` |
| Sydney | `syd1` |

---

## Container Registry (container-registry)

DigitalOcean Container Registry (DOCR) for storing Docker images.

### Common Tools

| Tool | Purpose |
|------|---------|
| `registry-get` | Get registry info |
| `repository-list` | List image repositories |
| `repository-tags` | List tags for a repository |
| `gc-start` | Start garbage collection |

---

## Accounts (accounts)

Account management, billing, and SSH keys.

### Common Tools

| Tool | Purpose |
|------|---------|
| `account-get` | Get account info |
| `balance-get` | Check current balance |
| `invoice-list` | List invoices |
| `key-create` | Add an SSH key |
| `key-list` | List SSH keys |

---

## Insights (insights)

Monitoring and alerting.

### Common Tools

| Tool | Purpose |
|------|---------|
| `uptime-check-create` | Create an uptime monitor |
| `uptime-check-list` | List uptime checks |
| `alert-list` | List active alerts |

---

## Marketplace (marketplace)

Pre-configured application images and one-click installs.

### Common Tools

| Tool | Purpose |
|------|---------|
| `marketplace-list` | Browse available marketplace apps |

---

## Region Reference

| Region | Slug | Location |
|--------|------|----------|
| New York 1 | `nyc1` | New York, USA |
| New York 3 | `nyc3` | New York, USA |
| San Francisco 3 | `sfo3` | San Francisco, USA |
| Toronto 1 | `tor1` | Toronto, Canada |
| Amsterdam 3 | `ams3` | Amsterdam, Netherlands |
| Frankfurt 1 | `fra1` | Frankfurt, Germany |
| London 1 | `lon1` | London, UK |
| Bangalore 1 | `blr1` | Bangalore, India |
| Singapore 1 | `sgp1` | Singapore |
| Sydney 1 | `syd1` | Sydney, Australia |

Not all services are available in all regions. App Platform uses shortened slugs (`nyc`, `sfo`, `ams`, etc.).

---

## Sizing Reference

### Droplet Sizes (Common)

| Slug | vCPU | RAM | Disk | Monthly |
|------|------|-----|------|---------|
| `s-1vcpu-512mb-10gb` | 1 | 512 MB | 10 GB | $4 |
| `s-1vcpu-1gb` | 1 | 1 GB | 25 GB | $6 |
| `s-1vcpu-2gb` | 1 | 2 GB | 50 GB | $12 |
| `s-2vcpu-2gb` | 2 | 2 GB | 60 GB | $18 |
| `s-2vcpu-4gb` | 2 | 4 GB | 80 GB | $24 |
| `s-4vcpu-8gb` | 4 | 8 GB | 160 GB | $48 |

*Prices are approximate. Use `accounts` service to check current billing rates.*
