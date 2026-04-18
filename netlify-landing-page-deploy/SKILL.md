---
name: netlify-landing-page-deploy
description: Deploy static landing pages to Netlify via the Netlify MCP server. Use this skill whenever the user wants to deploy a static website, landing page, or simple multi-page HTML site to production. Triggers include any mention of "deploy", "publish", "ship", "go live", "push to production", or "host this site" when the context involves a static HTML/CSS/JS site or landing page. Also triggers when the user mentions Netlify specifically, or when OpenClaw needs to autonomously deploy a web asset. This skill handles pre-deploy validation (form wiring, asset checks, Netlify compatibility), GitHub repo preparation, and deployment via the Netlify MCP. It does NOT handle DNS/domain configuration (use the netlify-dns skill for that) or complex app deployments requiring server-side runtimes (escalate to the digitalocean-management skill for those).
---

# Netlify Landing Page Deploy

Deploy validated, production-ready static landing pages to Netlify using the official Netlify MCP server. This skill covers the full pipeline from receiving a web asset through validation, GitHub push, and Netlify deployment.

## Scope

This skill is for **static landing pages only**. A site qualifies if it meets ALL of these criteria:

- Pure HTML/CSS/JS with no server-side runtime (no Node server, no Python backend, no PHP)
- No build step required OR uses only a simple static-site generator (e.g., `npx tailwindcss`, Hugo, Jekyll)
- Total deploy size under 100MB
- No database dependencies
- No server-side authentication flows

If a site does NOT meet these criteria, **stop and escalate** to the `digitalocean-management` skill. Inform the user why the site exceeds Netlify's static hosting model and what deployment path is recommended instead.

## Prerequisites

The following must be in place before this skill can execute:

1. **Netlify MCP server** is configured and accessible by the agent
2. **GitHub access** — the agent can push to a GitHub repository (the Netlify account is linked to the same GitHub account)
3. **Netlify account** has form detection enabled (required for contact forms)

### MCP Server Configuration

The Netlify MCP server must be configured in the agent's MCP settings:

```json
{
  "mcpServers": {
    "netlify": {
      "command": "netlify-mcp",
      "env": {
        "NETLIFY_PERSONAL_ACCESS_TOKEN": "<stored-securely-in-env>"
      }
    }
  }
}
```

Requires Node.js 22 or higher on the host running the MCP server.

See `SETUP.md` for step-by-step installation and token provisioning.

## MCP Tools — Quick Reference

The `@netlify/mcp` server exposes nine multiplexed tools. Each takes a `selectSchema` object with an `operation` and `params`. **Prefer these over raw HTTP** when the operation is covered.

| Tool | Read operations | Update operations |
|---|---|---|
| `mcp__netlify__netlify-user-services-reader` | `get-user` | — |
| `mcp__netlify__netlify-team-services-reader` | `get-teams`, `get-team` | — |
| `mcp__netlify__netlify-project-services-reader` | `get-projects`, `get-project`, `get-forms-for-project` | — |
| `mcp__netlify__netlify-project-services-updater` | — | create/update project, env vars |
| `mcp__netlify__netlify-deploy-services-reader` | `get-deploy`, `get-deploy-for-site` | — |
| `mcp__netlify__netlify-deploy-services-updater` | — | trigger/restore deploy |
| `mcp__netlify__netlify-extension-services-reader` | list installed extensions | — |
| `mcp__netlify__netlify-extension-services-updater` | — | install/remove extensions |
| `mcp__netlify__netlify-coding-rules` | (informational) | — |

**Not covered by the MCP** (fall back to direct HTTP against `https://api.netlify.com/api/v1/`):
- Form submissions (reading captured data)
- DNS zones and records
- Build hooks
- SSL certificate management

See `docs/mcp-tools.md` for per-operation schemas and examples.

## Deployment Pipeline

Follow these phases in order. Each phase has a gate — do not proceed to the next phase if the current phase fails.

### Phase 1: Receive and Inventory the Web Asset

Accept the web asset (zip file, directory, or individual files). Inventory the contents:

1. List all files and their types
2. Identify the entry point (`index.html` at root)
3. Identify all HTML files
4. Identify all static assets (images, fonts, CSS, JS)
5. Check for any server-side files that would disqualify the site (`.php`, `.py`, `.rb`, `server.js`, `package.json` with a `start` script, `Dockerfile`, etc.)

**Gate:** If server-side files are found, STOP. Report the incompatibility and escalate to `digitalocean-management`.

### Phase 2: Validate HTML for Netlify Compatibility

For every HTML file, run these checks. Read `references/netlify-forms-checklist.md` for detailed form validation rules.

#### 2a. Form Validation (Critical)

Scan all `<form>` elements. For each form found:

1. **Netlify attribute present** — The form tag MUST have either `data-netlify="true"` or a bare `netlify` attribute. If missing, add it.
2. **Name attribute present** — The form tag MUST have a `name` attribute. Each form on the site must have a unique name. If missing, generate a sensible name from context (e.g., `"contact"`, `"newsletter-signup"`).
3. **Method attribute** — Should be `POST`. If missing, add `method="POST"`.
4. **Input name attributes** — Every `<input>`, `<textarea>`, and `<select>` inside the form MUST have a `name` attribute. Inputs without names are invisible to Netlify and data will be lost. If missing, generate names from context (label text, placeholder, id, or type).
5. **Honeypot spam protection** — Recommended. If not present, add a honeypot field:
   - Add `netlify-honeypot="bot-field"` to the `<form>` tag
   - Add a hidden input: `<p class="hidden"><label>Don't fill this out: <input name="bot-field" /></label></p>`
   - Add CSS `.hidden { display: none; }` if not already present
6. **Success page / AJAX handling** — Check if the form has an `action` attribute pointing to a success page, or if JS handles submission via AJAX. If neither exists, add `action="/thank-you"` and create a minimal `thank-you.html` page.

#### 2b. JS-Rendered Form Detection

If the site uses JavaScript to render forms dynamically (React, Vue, etc.), the standard Netlify form detection will NOT work because Netlify parses static HTML at deploy time. In this case:

1. Create a hidden HTML form in the static HTML with matching field names
2. Add `<input type="hidden" name="form-name" value="<form-name>" />` to the JS-rendered form
3. Ensure the JS form submission POSTs URL-encoded data (not JSON)

If the form submission uses `fetch()` or `XMLHttpRequest`, verify the `Content-Type` is `application/x-www-form-urlencoded` and NOT `application/json`. Netlify Forms does not support JSON payloads.

#### 2c. AJAX Form Submission Check

If forms are submitted via AJAX/fetch, verify:

1. The body is URL-encoded (use `new URLSearchParams(new FormData(form)).toString()`)
2. A hidden `form-name` input is included in the POST body
3. The `Content-Type` header is `application/x-www-form-urlencoded` (or omitted for multipart with file uploads)

#### 2d. Asset Integrity

1. All referenced images, CSS, JS, and font files exist at the paths specified in the HTML
2. No absolute filesystem paths (e.g., `C:\Users\...` or `/home/user/...`)
3. External CDN references (Google Fonts, Tailwind CDN, etc.) are acceptable but note them in the deploy report
4. Favicon exists or should be noted as missing

#### 2e. Meta and SEO Baseline

These are warnings, not blockers:

1. `<title>` tag present
2. `<meta name="description">` present
3. `<meta name="viewport">` present (critical for mobile)
4. Open Graph tags present (`og:title`, `og:description`, `og:image`)

### Phase 3: Apply Fixes

If Phase 2 identified issues that can be auto-fixed (missing form attributes, missing honeypot, missing thank-you page), apply them now. Generate a change report listing every modification made.

**Gate:** If any form is missing critical elements that cannot be auto-fixed (e.g., a form rendered entirely in JS with no way to create a static HTML mirror), STOP and report the issue to the user. Offer the Netlify Functions alternative — a serverless function that handles form submission server-side. See `references/netlify-forms-checklist.md` for the function template.

### Phase 4: Push to GitHub

1. Initialize a git repo (or use an existing one) for the site
2. Ensure a `.gitignore` is present (at minimum: `.DS_Store`, `node_modules/`, `.env`)
3. Add a `netlify.toml` at the repo root if one doesn't exist:

```toml
[build]
  publish = "."

# Redirect for SPA-style thank-you page if needed
# [[redirects]]
#   from = "/thank-you"
#   to = "/thank-you.html"
#   status = 200
```

4. Commit all files with a descriptive message: `"Deploy: <site-name> - <timestamp>"`
5. Push to the configured GitHub repository

### Phase 5: Deploy via Netlify MCP

Use the Netlify MCP server to execute the deployment. Note: the current Netlify dashboard and MCP tools use **"projects"** terminology. The underlying API still returns `site_id` — that field is the canonical project identifier.

1. **Check for existing project** — Use `netlify-project-services-reader` (operations `get-projects` or `get-project`) to find the project by name or `siteId`
2. **Create or update the project:**
   - If new: Use `netlify-project-services-updater` to create a new project linked to the GitHub repo
   - If existing: Push to the connected branch; Netlify auto-deploys. Use `netlify-deploy-services-updater` only when triggering an out-of-band deploy
3. **Set environment variables** if the project uses serverless functions (e.g., webhook URLs, API keys for form forwarding)
4. **Verify deployment** — Poll `netlify-deploy-services-reader` `get-deploy-for-site` until `state: "ready"`, then retrieve the live URL
5. **Verify form detection** — After deploy, call `netlify-project-services-reader` `get-forms-for-project` and confirm expected form names are registered. If Forms isn't enabled at the team level, `extraFeatures.forms` on the project will read `"not enabled"` — the user must toggle it in the dashboard first

### Phase 6: Deploy Report

Generate a deployment report with:

- **Project name** and **Netlify dashboard URL** (`https://app.netlify.com/projects/<name>`)
- **Live URL** (primary site URL, e.g., `https://project-name.netlify.app` or the custom domain if connected)
- **Deploy status** (success/failure)
- **Forms detected** (list form names returned by `get-forms-for-project`)
- **Modifications made** (list all changes from Phase 3)
- **Warnings** (missing SEO tags, external CDN dependencies, Forms feature disabled, etc.)
- **Next steps** (suggest connecting a custom domain via the `netlify-dns` skill)

## Error Handling

| Error | Action |
|-------|--------|
| Project exceeds static hosting scope | Escalate to `digitalocean-management` |
| Form uses JSON submission | Rewrite to URL-encoded, report change |
| Form rendered entirely in JS | Warn user, offer Netlify Functions path |
| GitHub push fails | Report auth/permission issue, suggest checking GitHub PAT |
| Netlify MCP auth fails | Report token issue, suggest regenerating PAT |
| Deploy fails | Retrieve deploy logs via MCP, report error details |
| Form detection not enabled | Warn user to enable in Netlify dashboard |

## API Reference (docs/)

Per-topic references for the Netlify API surface this skill touches. Read the relevant doc when the pipeline needs details beyond what's in this file.

- [docs/api-overview.md](docs/api-overview.md) — Base URL, auth, pagination, rate limits, terminology
- [docs/mcp-tools.md](docs/mcp-tools.md) — Full schemas and call patterns for all 9 MCP tools
- [docs/projects.md](docs/projects.md) — Project (site) CRUD, build settings, env vars, `netlify.toml`
- [docs/deploys.md](docs/deploys.md) — Deploy states, triggering, restoring, logs, polling pattern
- [docs/forms.md](docs/forms.md) — Form detection rules, submission API, spam protection, notifications
- [docs/functions.md](docs/functions.md) — Netlify Functions layout, v1/v2 handlers, form-handler patterns, env vars
- [docs/dns.md](docs/dns.md) — DNS zones, records, custom domains, SSL (shared with `netlify-dns` skill)
- [docs/build-hooks.md](docs/build-hooks.md) — Trigger-URL–based deploys

For the pipeline-time form validation checklist (Phase 2), see `references/netlify-forms-checklist.md`.

## What This Skill Does NOT Do

- **DNS / Domain management** — Use `netlify-dns` (separate skill, to be built)
- **SSL certificate configuration** — Netlify handles this automatically once a domain is connected
- **Complex app deployment** (containers, databases, server-side rendering) — Escalate to `digitalocean-management`
- **CI/CD pipeline configuration** — This skill does direct deploys; CI/CD is out of scope
- **Content editing** — This skill deploys what it receives; content changes are upstream
