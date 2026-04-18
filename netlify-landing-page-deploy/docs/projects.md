# Project (Site) Reference

A **project** (API: `site`) is the deployable unit — a git repo + build settings + a hostname. Everything else (deploys, forms, env vars, DNS) hangs off of it.

## Key Fields

Selected fields from `GET /api/v1/sites/:id` (many more exist; these are the ones the skill cares about):

| Field | Type | Description |
|---|---|---|
| `id` / `site_id` | UUID | Canonical project identifier |
| `name` | string | URL slug (`my-site` → `my-site.netlify.app`) |
| `url` | string | Primary site URL (custom domain if set, else `*.netlify.app`) |
| `admin_url` | string | Netlify dashboard URL |
| `deploy_url` | string | Latest deploy URL (may be a deploy-preview subdomain) |
| `state` | string | `current`, `deleted`, `disabled` |
| `account_id` | string | Owning team ID |
| `custom_domain` | string | User-configured primary domain |
| `domain_aliases` | string[] | Additional connected domains |
| `force_ssl` | bool | HTTPS redirect enforcement |
| `ssl` | bool | SSL certificate provisioned |
| `ssl_url` | string | HTTPS version of primary URL |
| `build_settings` | object | See below |
| `published_deploy` | object | Currently-live deploy |
| `build_image` | string | Ubuntu image used by build bot |
| `processing_settings` | object | Asset optimization toggles |
| `plan` | string | `nf_team_dev` (Free), `nf_team_pro`, `nf_team_business`, etc. |

## `build_settings` Sub-Object

| Field | Type | Description |
|---|---|---|
| `repo_url` | string | GitHub/GitLab URL |
| `repo_branch` | string | Production branch (usually `main`) |
| `cmd` | string | Build command (`npm run build`, `hugo`, `""` for no-build) |
| `dir` | string | Publish directory (`dist`, `public`, `.`) |
| `env` | object | Build-time env vars (see Env Vars section) |
| `allowed_branches` | string[] | Branches that trigger builds |
| `deploy_key_id` | string | Deploy key ID |
| `provider` | string | `github`, `gitlab`, `bitbucket` |

## Common Operations

### List projects

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites?per_page=100"
```

MCP: `netlify-project-services-reader` → `get-projects`.

### Get a project

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

MCP: `netlify-project-services-reader` → `get-project`.

### Create a project linked to a GitHub repo

```bash
curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{
    "name": "my-landing-page",
    "repo": {
      "provider": "github",
      "repo": "owner/repo-name",
      "branch": "main",
      "cmd": "",
      "dir": "."
    }
  }' \
  "https://api.netlify.com/api/v1/sites"
```

MCP: `netlify-project-services-updater` → `create-project`.

### Update build settings

```bash
curl -X PATCH -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"build_settings": {"cmd": "npm run build", "dir": "dist"}}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

### Delete a project

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID"
```

## Environment Variables

Env vars exposed to builds AND serverless functions. Two scopes exist in the modern API:

1. **Project env vars** (preferred) — `/api/v1/accounts/:account_id/env?site_id=:site_id`
2. **Legacy `build_settings.env`** — still works but scoped to builds only

### List env vars

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/accounts/$ACCOUNT_ID/env?site_id=$SITE_ID"
```

### Create / update an env var

```bash
curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '[{
    "key": "WEBHOOK_URL",
    "values": [{"value": "https://example.com/hook", "context": "all"}],
    "scopes": ["builds", "functions", "runtime"]
  }]' \
  "https://api.netlify.com/api/v1/accounts/$ACCOUNT_ID/env?site_id=$SITE_ID"
```

`context` = `production`, `deploy-preview`, `branch-deploy`, `dev`, or `all`.
`scopes` = one or more of `builds`, `functions`, `runtime`, `post_processing`.

## `extraFeatures` (from MCP `get-project`)

The MCP enriches responses with an `extraFeatures` map. Watch these when gating skill behavior:

| Field | Values | Meaning |
|---|---|---|
| `forms` | `enabled`, `not enabled` | Team-level Forms detection toggle |

If a feature reads `not enabled`, the user must toggle it in the Netlify dashboard — the API doesn't expose the toggle directly on the Free plan.

## `netlify.toml` (In-Repo Config)

Lives at the repo root. Overrides API-set build settings for git-driven deploys:

```toml
[build]
  command = ""            # leave empty for no-build static sites
  publish = "."           # or "dist", "public", etc.

[build.environment]
  NODE_VERSION = "20"

[[redirects]]
  from = "/old-path"
  to = "/new-path"
  status = 301

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    Referrer-Policy = "strict-origin-when-cross-origin"
```

For a plain static landing page, `[build] publish = "."` is the minimum.
