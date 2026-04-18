# Deploys Reference

A **deploy** is a single build of a project at a specific commit. Every push to the production branch creates one. Manual triggers, API-initiated deploys, and deploy-previews also each produce a deploy record.

## Deploy States

| State | Meaning |
|---|---|
| `new` | Queued, not yet processing |
| `building` | Build command is running |
| `processing` | Post-build asset processing (minify, image optimize, etc.) |
| `uploading` | Files going to the Netlify CDN |
| `uploaded` | Files on CDN, not yet published |
| `ready` | ✅ Live and serving traffic |
| `error` | ❌ Failed — see `error_message` and deploy logs |
| `rejected` | Blocked (e.g., plan limits) |
| `canceled` | Manually stopped |

Poll for `ready` when waiting on a deploy to go live. Give up on `error` / `rejected` / `canceled`.

## Key Fields

From `GET /api/v1/sites/:site_id/deploys/:deploy_id`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Deploy ID |
| `site_id` | UUID | Parent project |
| `state` | string | See table above |
| `name` | string | Project name slug |
| `branch` | string | Git branch |
| `commit_ref` | string | Git commit SHA |
| `commit_url` | string | GitHub commit URL |
| `deploy_url` | string | `https://<hash>--<project>.netlify.app` (the unique deploy URL) |
| `deploy_ssl_url` | string | HTTPS version |
| `ssl_url` / `url` | string | Primary project URL (only populated if this is the published deploy) |
| `created_at` | ISO 8601 | When queued |
| `updated_at` | ISO 8601 | Most recent state change |
| `error_message` | string | Populated when `state == "error"` |
| `log_access_attributes` | object | Pre-signed URL for log retrieval |
| `context` | string | `production`, `deploy-preview`, `branch-deploy` |
| `framework` | string | Detected framework |
| `title` | string | Last commit message |
| `published_at` | ISO 8601 | When promoted to production |

## Common Operations

### List deploys for a project

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/deploys?per_page=10"
```

Filter by state: `?state=ready`. Filter by branch: `?branch=main`.

### Get a single deploy

MCP: `netlify-deploy-services-reader` → `get-deploy-for-site { siteId, deployId }`.

### Trigger a deploy (via build hook)

```bash
curl -X POST "https://api.netlify.com/build_hooks/<BUILD_HOOK_ID>"
```

See [build-hooks.md](build-hooks.md).

### Trigger a deploy via API

```bash
curl -X POST -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/builds"
```

MCP: `netlify-deploy-services-updater` → `trigger-deploy`.

### Restore / promote an old deploy

```bash
curl -X POST -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/deploys/$DEPLOY_ID/restore"
```

Makes the targeted deploy the live `published_deploy`. Useful for rollbacks.

### Lock / unlock auto-deploys

```bash
curl -X POST -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/deploys/$DEPLOY_ID/lock"
```

When locked, pushes don't auto-promote; they deploy as unpublished.

## Polling Pattern (skill Phase 5)

```bash
DEPLOY_ID=...
SITE_ID=...
for i in $(seq 1 40); do
  state=$(curl -s -H "Authorization: Bearer $TOK" \
    "https://api.netlify.com/api/v1/sites/$SITE_ID/deploys/$DEPLOY_ID" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['state'])")
  echo "$i: $state"
  case "$state" in
    ready)     exit 0 ;;
    error|rejected|canceled) exit 1 ;;
  esac
  sleep 5
done
exit 2  # timed out
```

## Deploy Logs

Logs aren't inline on the deploy object — fetch via:

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/deploys/$DEPLOY_ID/log"
```

Returns plain text. For function-specific logs, see [functions.md](functions.md).

## Deploy Previews

Pushing to a non-production branch, or opening a PR against the production branch, produces a deploy-preview at a per-branch URL:

```
https://deploy-preview-42--project-name.netlify.app
```

Previews share env vars with the `deploy-preview` context (see [projects.md](projects.md) env vars). They do NOT trigger form submissions on the production forms; test submissions must target the production URL (or a preview-scoped form).
