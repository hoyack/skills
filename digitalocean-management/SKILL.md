---
name: digitalocean-management
description: Manage DigitalOcean cloud infrastructure via the official DigitalOcean MCP server. Use this skill whenever the user wants to deploy an application that exceeds static site hosting (requires a server runtime, database, containers, or background workers), manage Droplets, provision databases, configure networking/domains/DNS, manage Kubernetes clusters, work with Spaces object storage, or check account billing/insights. Triggers include any mention of "DigitalOcean", "DO", "Droplet", "App Platform", "Spaces", "DOKS", or when another skill (like netlify-landing-page-deploy) escalates because the deployment exceeds static hosting capabilities. Also triggers for "deploy app", "spin up a server", "provision a database", "container deployment", or "managed Kubernetes" when DigitalOcean is the target platform. This skill covers all 9 DigitalOcean MCP services. It does NOT handle DNS for domains hosted on external registrars like IONOS (use ionos-dns-management for that) — it handles domains and DNS only within DigitalOcean's own networking service.
---

# DigitalOcean Management

Manage DigitalOcean cloud infrastructure through the official DigitalOcean MCP server. This skill covers the full spectrum of DigitalOcean services — from deploying applications on App Platform to provisioning Droplets, databases, Kubernetes clusters, object storage, and networking resources.

## When to Use This Skill

This skill is the escalation target when a deployment exceeds what static hosting (Netlify, Vercel, Cloudflare Pages) can handle. Use it when the project requires:

- A server-side runtime (Node.js, Python, Ruby, Go, PHP, etc.)
- A database (PostgreSQL, MySQL, Redis, MongoDB)
- Background workers or scheduled jobs
- Container-based deployment (Docker)
- WebSocket connections or persistent processes
- More than 100MB deploy size or complex build pipelines
- Kubernetes orchestration
- Object storage (S3-compatible)

Also use this skill for general DigitalOcean infrastructure management regardless of deployment context.

## Prerequisites

1. **DigitalOcean API Token** — Generated at `https://cloud.digitalocean.com/account/api/tokens` with appropriate scopes
2. **Environment variable** configured: `DIGITALOCEAN_API_TOKEN`
3. **Node.js 18+** on the agent host (for local MCP server via npx)

See `SETUP.md` for step-by-step credential provisioning and MCP registration.

## MCP Server Configuration

The DigitalOcean MCP server supports two modes: **local** (via npx) and **remote** (hosted endpoints). Use local for OpenClaw and agent deployments; remote is available for lightweight integrations.

### Local MCP Server (Recommended for Agents)

Use the `--services` flag to enable only the services needed. This reduces context size and improves accuracy.

```json
{
  "mcpServers": {
    "digitalocean": {
      "command": "npx",
      "args": ["-y", "@digitalocean/mcp", "--services", "apps,droplets,databases,networking"],
      "env": {
        "DIGITALOCEAN_API_TOKEN": "<stored-securely-in-env>"
      }
    }
  }
}
```

Scope the `--services` flag to what the task requires. Available service keys:

| Service Key | What It Manages |
|-------------|-----------------|
| `apps` | App Platform — deploy and manage applications |
| `droplets` | Virtual machines (VPS) |
| `databases` | Managed PostgreSQL, MySQL, Redis, MongoDB, Kafka |
| `doks` | Managed Kubernetes clusters |
| `networking` | Domains, DNS records, load balancers, firewalls, VPCs, CDN, floating IPs |
| `spaces` | S3-compatible object storage |
| `accounts` | Billing, balance, invoices, SSH keys |
| `insights` | Uptime monitoring, SSL certificate checks, alerts |
| `marketplace` | One-click apps and marketplace images |
| `container-registry` | Container image registry (DOCR) |

### Remote MCP Endpoints (Alternative)

Each service also has a hosted remote endpoint. Useful when you don't want to run npx locally:

```json
{
  "mcpServers": {
    "do-apps": {
      "url": "https://apps.mcp.digitalocean.com/mcp",
      "headers": {
        "Authorization": "Bearer <DIGITALOCEAN_API_TOKEN>"
      }
    },
    "do-databases": {
      "url": "https://databases.mcp.digitalocean.com/mcp",
      "headers": {
        "Authorization": "Bearer <DIGITALOCEAN_API_TOKEN>"
      }
    }
  }
}
```

Full list of remote endpoints is in `references/do-services-reference.md`.

## Service Workflows

### App Platform — Application Deployment

This is the primary escalation path from `netlify-landing-page-deploy` and `netlify-spa-deploy`. App Platform handles full-stack applications with server-side runtimes.

Read `docs/app-platform.md` for the complete deployment playbook and `references/do-services-reference.md` for the tool catalog.

#### Deploy from GitHub Repo

1. **Assess the project** — Identify the runtime, build command, and publish directory
2. **Create the app** — Use the `app-create` tool, providing:
   - GitHub repo URL (format: `owner/repo`)
   - Branch (default: `main`)
   - Region (default: `nyc`, options include `sfo`, `ams`, `sgp`, `lon`, `fra`, `blr`, `syd`, `tor`)
   - Instance size (basic, professional, etc.)
   - Environment variables
3. **Monitor deployment** — Use `app-list` and app detail tools to track deploy status
4. **Verify** — Confirm the app is live and accessible at its `.ondigitalocean.app` URL
5. **Configure domain** (if needed) — Use the `networking` service to add a custom domain, or use `ionos-dns-management` if DNS is on IONOS

#### Update/Redeploy an Existing App

1. **List apps** — Use `app-list` to find the app
2. **Trigger redeploy** — The MCP server exposes redeploy tools that pull the latest commit
3. **Monitor** — Watch for successful deployment
4. **Rollback** — If deployment fails, use rollback tools to revert to the previous working version

#### Environment Variables

App Platform supports encrypted environment variables. Set them via the MCP server when creating or updating an app. These are stored server-side and never exposed in logs or client code — use this for API keys, database credentials, webhook secrets, etc.

### Droplets — Virtual Machines

For workloads that need a full Linux server (custom daemons, game servers, VPN endpoints, etc.):

1. **Create Droplet** — Specify region, size, image (Ubuntu, Debian, Fedora, etc.), SSH key
2. **Manage** — Resize, snapshot, rebuild, power cycle
3. **Monitor** — Check status, bandwidth, CPU metrics via `insights` service
4. **Destroy** — Clean up when no longer needed

**Safety:** Always confirm with the user before destroying Droplets. Data loss is permanent unless snapshots exist.

See `docs/droplets.md` for sizing strategy, SSH key management, and common post-provision tasks.

### Databases — Managed Database Clusters

1. **Provision** — Create PostgreSQL, MySQL, Redis, MongoDB, or Kafka clusters
2. **Manage** — Resize, add read replicas, manage connection pools, configure trusted sources
3. **Connect** — Retrieve connection strings and credentials for use in app environment variables
4. **Backup/Restore** — Managed databases include automatic daily backups

See `docs/databases.md` for engine-specific notes and connection patterns.

### Networking — Domains, DNS, Load Balancers, Firewalls

The networking service manages domains registered or pointed to DigitalOcean:

- **Domains** — Add/remove domains, manage DNS records (A, AAAA, CNAME, MX, TXT, NS, SRV)
- **Load Balancers** — Create and configure load balancers for multi-Droplet setups
- **Firewalls** — Manage inbound/outbound rules for Droplets
- **Floating IPs** — Reserve and assign static IPs
- **VPCs** — Manage private networking between resources
- **CDN** — Manage CDN endpoints for Spaces, including cache flushing

**Note:** For domains whose DNS is hosted on IONOS (or other external registrars), use the appropriate DNS management skill (e.g., `ionos-dns-management`). The DigitalOcean networking service only manages DNS for domains using DigitalOcean's own nameservers (`ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com`).

See `docs/networking.md` for load balancer patterns, firewall templates, and CDN setup.

### Kubernetes (DOKS)

For container orchestration workloads:

1. **Create cluster** — Specify region, node pool size, Kubernetes version
2. **Manage node pools** — Scale up/down, add/remove pools
3. **Monitor** — Check cluster and node status

### Spaces — Object Storage

S3-compatible storage for static assets, backups, media files:

1. **Create Space** — Choose region, set access (public/private)
2. **Upload/download files** — Manage objects in Spaces
3. **CDN** — Enable CDN for a Space, manage custom domains, flush cache
4. **CORS** — Configure cross-origin access for web applications

See `docs/spaces.md` for S3-compatibility notes and CDN patterns.

### Accounts & Insights

- **Accounts** — Check billing, balance, invoices, manage SSH keys
- **Insights** — Set up uptime monitors, SSL certificate expiry alerts, check resource health

## Common MCP Tool Names

The DigitalOcean MCP server exposes tools with descriptive names. Common patterns:

| Tool | Description |
|------|-------------|
| `app-create` | Deploy a new app to App Platform |
| `app-list` | List all apps on the account |
| `app-delete` | Remove an app |
| `droplet-create` | Spin up a new Droplet |
| `droplet-resize` | Change Droplet size |
| `domain-create` | Add a domain to DigitalOcean DNS |
| `key-create` | Add an SSH key |
| `cdn-flush-cache` | Purge CDN cache for a Space |

The full tool list is discovered dynamically by the MCP client. Use the service-specific READMEs linked from the GitHub repo for exhaustive documentation.

## Safety Rules

1. **Never destroy resources without user confirmation.** Droplets, databases, apps, and Spaces contain data that cannot be recovered once deleted (unless snapshots/backups exist).

2. **Scope MCP services to what's needed.** Don't enable all 9 services for a simple app deploy. Use `--services apps` for App Platform work, add others only when required. This prevents the model from being overwhelmed with irrelevant tools.

3. **Never expose API tokens.** The `DIGITALOCEAN_API_TOKEN` must be stored in environment variables. Never log it, display it, or include it in MCP config files that could be committed to Git.

4. **Confirm region before provisioning.** DigitalOcean charges by the hour. Spinning up resources in the wrong region creates latency and costs. Always confirm region with the user if not specified.

5. **Check existing resources before creating new ones.** Use `app-list`, droplet list, etc., to verify the resource doesn't already exist before creating a duplicate.

6. **Monitor costs.** Use the `accounts` service to check current billing before provisioning expensive resources (large Droplets, database clusters, multi-node Kubernetes).

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `401 Unauthorized` | Invalid or revoked API token | Verify `DIGITALOCEAN_API_TOKEN` and token scopes |
| `403 Forbidden` | Token lacks required scope | Regenerate token with correct scopes |
| `404 Not Found` | Resource doesn't exist | Re-list resources to get correct IDs |
| `422 Unprocessable` | Invalid configuration | Check region, size, image availability |
| `429 Rate Limited` | Too many API requests | Back off and retry after delay |
| Resource stuck in `deploying` | Build or deploy failure | Fetch logs via MCP, diagnose, and fix |

## Integration with Other Skills

- **`netlify-landing-page-deploy`** — Escalates to this skill when a site exceeds static hosting capacity. This skill handles the App Platform deployment.
- **`netlify-spa-deploy`** (planned) — Handles SPA frontends on Netlify; pairs with this skill when the backend lives on DigitalOcean.
- **`ionos-dns-management`** — After deploying on DigitalOcean, use the IONOS skill to point domains hosted on IONOS to the DigitalOcean app/Droplet IP.
- **`netlify-dns`** — Only relevant when DNS is on Netlify; this skill handles DNS when it's on DigitalOcean.
- **Future skills** — Database provisioning workflows, CI/CD pipeline configuration, and Kubernetes deployment patterns will extend this skill's capabilities.

## API Reference (docs/)

Per-topic references for the DigitalOcean services this skill touches. Read the relevant doc when a workflow needs details beyond what's in this file.

- [docs/api-overview.md](docs/api-overview.md) — Base URL, auth, rate limits, regions, pagination
- [docs/app-platform.md](docs/app-platform.md) — App spec, deploy sources, instance sizes, env vars, logs, rollback
- [docs/droplets.md](docs/droplets.md) — Droplet sizing, images, SSH keys, snapshots, post-provision automation
- [docs/databases.md](docs/databases.md) — Engine-specific provisioning, connection strings, trusted sources, backups
- [docs/networking.md](docs/networking.md) — Domains, DNS records, load balancers, firewalls, VPCs, floating IPs, CDN
- [docs/spaces.md](docs/spaces.md) — S3-compatible object storage, CDN, CORS, lifecycle rules

Pipeline-wide endpoint reference: `references/do-services-reference.md`.

## What This Skill Does NOT Do

- **DNS management for external registrars** — Use `ionos-dns-management` or other provider-specific skills
- **CI/CD pipeline configuration** — App Platform has built-in CI/CD from Git; complex pipelines need separate tooling
- **Application code development** — This skill deploys and manages infrastructure, not application code
- **Cost optimization analysis** — Can retrieve billing data via `accounts` but does not make spending recommendations
- **Bare metal or GPU instances** — These are separate DigitalOcean products not yet exposed via MCP
