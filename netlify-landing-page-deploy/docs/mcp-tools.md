# Netlify MCP Tools Reference

The `@netlify/mcp` server exposes nine tools. Each "services" tool is a multiplexer: pick an `operation` in the `selectSchema.operation` field, pass that operation's `params`. All tools are called as `mcp__netlify__<tool>`.

## Shape of Every Call

```json
{
  "selectSchema": {
    "operation": "<op-name>",
    "params": { ... }
  }
}
```

Optional diagnostic fields (useful but not required): `aiAgentName`, `llmModelName`.

## Tool Catalog

### 1. `netlify-user-services-reader`

| Operation | Params | Purpose |
|---|---|---|
| `get-user` | `{}` | Current authenticated user profile |

### 2. `netlify-team-services-reader`

| Operation | Params | Purpose |
|---|---|---|
| `get-teams` | `{}` | List teams the user belongs to |
| `get-team` | `{ teamId }` | Get a single team by ID |

### 3. `netlify-project-services-reader`

| Operation | Params | Purpose |
|---|---|---|
| `get-projects` | `{ teamSlug?, projectNameSearchValue? }` | List projects (sites); optionally filter by team or name substring |
| `get-project` | `{ siteId }` | Single project detail (includes `extraFeatures`, `currentDeploy`, `urls`) |
| `get-forms-for-project` | `{ siteId, formId? }` | List forms on a project, or a single form |

### 4. `netlify-project-services-updater`

| Operation | Purpose |
|---|---|
| `create-project` | Create a new project linked to a repo |
| `update-project` | Update build settings, env vars, metadata |
| Additional ops vary per MCP version — call with an invalid op to surface the list |

Use this tool when creating a new site or changing build config. Env vars are typically set here.

### 5. `netlify-deploy-services-reader`

| Operation | Params | Purpose |
|---|---|---|
| `get-deploy` | `{ deployId }` | Single deploy by ID |
| `get-deploy-for-site` | `{ siteId, deployId }` | Scoped lookup; equivalent to above but within a project |

### 6. `netlify-deploy-services-updater`

| Operation | Purpose |
|---|---|
| `trigger-deploy` / `restore-deploy` | Fire a new deploy or promote an old one to production |

Only needed for out-of-band deploys. A `git push` to the connected branch normally triggers a deploy automatically.

### 7. `netlify-extension-services-reader` / `-updater`

Manage Netlify extensions (integrations with third-party services — analytics, image optimizers, etc.). Not used by the landing-page pipeline.

### 8. `netlify-coding-rules`

Returns Netlify's recommended coding conventions (framework setup, env var naming, etc.). Informational; not deploy-gating.

## Patterns

### Find a project by name

```json
{
  "selectSchema": {
    "operation": "get-projects",
    "params": { "projectNameSearchValue": "serviceorchard" }
  }
}
```

### Poll a deploy to `ready`

```json
{
  "selectSchema": {
    "operation": "get-deploy-for-site",
    "params": { "siteId": "...", "deployId": "..." }
  }
}
```

Watch for `state`: `new` → `building` → `processing` → `ready` (or `error`).

### Verify forms were detected after a deploy

```json
{
  "selectSchema": {
    "operation": "get-forms-for-project",
    "params": { "siteId": "..." }
  }
}
```

An empty array means either no forms in the HTML, or Forms detection is disabled at the team level (check `extraFeatures.forms` on the project).

## What the MCP Does NOT Cover (as of v1.15.1)

Fall back to raw HTTP for:

- **Form submissions** — reading submitted data (`GET /api/v1/forms/:form_id/submissions`)
- **DNS zones and records** — `/dns_zones`, `/dns_zones/:zone_id/dns_records`
- **Build hooks** — `/sites/:site_id/build_hooks`
- **SSL certificates** — `/sites/:site_id/ssl`
- **Split testing** — `/sites/:site_id/traffic_splits`
- **Deploy keys** — `/deploy_keys`

See the respective doc files for the REST endpoints.
