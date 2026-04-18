# Forms Reference

Netlify Forms captures HTML form submissions without any backend code. Enablement is team-level; registration happens at deploy time when the build bot parses static HTML.

## Prerequisite: Team-Level Feature Flag

Forms detection must be toggled on per team, in the dashboard:

1. https://app.netlify.com → team → **Team settings** → **Forms**
2. Enable "Active forms detection"

The MCP `get-project` response includes `extraFeatures.forms` = `"enabled"` or `"not enabled"`. Use this as a gate before attempting form validation.

## Form Detection Rules (Build-Time)

At deploy time, the Netlify build bot scans all deployed HTML files for `<form>` tags. To be registered, a form must have:

- `data-netlify="true"` (or bare `netlify` attribute), AND
- A `name` attribute

The form name must be unique within the project. The bot records the form name and the `name`-attributed inputs as the schema.

## Submission Requirements (Runtime)

To submit into a registered form:

- POST to `/` on the live site (any path also works, but `/` is conventional)
- `Content-Type: application/x-www-form-urlencoded` (or `multipart/form-data` for file uploads)
- Body must include `form-name=<registered-form-name>` alongside the other fields

**JSON bodies are rejected.** This is the most common integration bug.

## Form Object

From `GET /api/v1/sites/:site_id/forms`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Form ID (24-char hex) |
| `site_id` | UUID | Parent project |
| `name` | string | Form name (from HTML `name` attribute) |
| `paths` | string[] / null | Paths where the form was discovered (null if discovered in multiple) |
| `fields` | array | `[{ name, type }]` — inputs Netlify extracted from the form |
| `submission_count` | int | Total submissions received |
| `created_at` | ISO 8601 | First detection |
| `last_submission_at` | ISO 8601 / null | Most recent submission |
| `honeypot` | bool | Whether honeypot is configured |
| `recaptcha` | bool | Whether reCAPTCHA is configured |

## Submission Object

From `GET /api/v1/forms/:form_id/submissions`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Submission ID |
| `form_id` | string | Parent form |
| `site_url` | string | Project URL at submission time |
| `created_at` | ISO 8601 | Submission timestamp |
| `name` | string | Extracted from `name` field if present |
| `email` | string | Extracted from `email` field if present |
| `number` | int | Sequential submission number (1, 2, 3...) |
| `data` | object | All submitted fields, keyed by input `name` |
| `human_fields` | object | Same data but keys capitalized/humanized |
| `ordered_human_fields` | array | Preserves form field order |
| `body` | string | Raw POST body (reserved; not always populated) |

## Common Operations

### List forms on a project

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/forms"
```

MCP: `netlify-project-services-reader` → `get-forms-for-project`.

### List submissions for a form

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/forms/$FORM_ID/submissions"
```

Supports `?page`, `?per_page`. MCP does not cover submission reads — use curl.

### Read a single submission

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/submissions/$SUBMISSION_ID"
```

### Delete a submission

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/submissions/$SUBMISSION_ID"
```

### Read spam-flagged submissions

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/submissions?state=spam"
```

Normal submissions list via the form-scoped endpoint; spam lives under a state filter on the site endpoint.

### Delete a form (including all submissions)

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/forms/$FORM_ID"
```

## Spam Protection Options

### 1. Honeypot (recommended, no UX cost)

Add to `<form>`:
```html
<form ... netlify-honeypot="bot-field">
  <p class="hidden" aria-hidden="true" style="position:absolute;left:-9999px">
    <label>Don't fill this out: <input name="bot-field"></label>
  </p>
  ...
</form>
```

Submissions where `bot-field` is non-empty are silently discarded by Netlify (not even counted in the dashboard).

### 2. reCAPTCHA v2 (adds a checkbox)

```html
<form ... data-netlify-recaptcha="true">
  ...
  <div data-netlify-recaptcha="true"></div>
  <button type="submit">Submit</button>
</form>
```

Requires a Google reCAPTCHA site key set on the Netlify dashboard (or via env var).

### 3. Akismet (paid; content analysis)

Enabled at the team level; no markup changes needed.

## Notifications

Configure in the dashboard: **Project → Forms → Form notifications**.

- **Email**: Deliver each submission to an email address
- **Webhook**: POST each submission (as JSON) to a URL of your choice — use this to forward into a CRM
- **Slack**: Native integration

Webhook payload shape:
```json
{
  "form_id": "...",
  "site_id": "...",
  "site_url": "https://project.netlify.app",
  "form_name": "contact",
  "created_at": "2026-04-15T14:24:45.920Z",
  "data": { "name": "...", "email": "...", ... }
}
```

## JS-Rendered Forms (SPA)

Netlify's build bot only sees static HTML. For React/Vue/etc. where forms are JS-rendered:

1. Add a **hidden static mirror form** to the root HTML (e.g., `public/index.html`) so the bot registers the form
2. In the JS form, include `<input type="hidden" name="form-name" value="contact" />`
3. Submit via `fetch()` with URL-encoded body (see [netlify-forms-checklist.md](../references/netlify-forms-checklist.md) for snippet)

See the `references/netlify-forms-checklist.md` checklist for the full validation flow used by the deploy skill.

## Limits (Free Plan)

- 100 submissions/month
- 10 MB/month file upload storage
- Submissions beyond the cap are blocked until next billing period or plan upgrade

Paid plans raise both limits substantially. Reading the team `plan` field in the project response shows which tier.

## Troubleshooting Matrix

| Symptom | Likely Cause |
|---|---|
| Form submitted but not in dashboard | Missing `data-netlify="true"` or JS-rendered without static mirror |
| Submission returns 404 | `form-name` hidden field missing, or form name doesn't match a registered form |
| Submission returns 400 | `Content-Type: application/json` — Netlify requires URL-encoded or multipart |
| Some fields missing from submission | Those inputs lack a `name` attribute |
| Flood of spam submissions | Honeypot not configured; consider adding reCAPTCHA |
| `extraFeatures.forms == "not enabled"` | Team-level feature flag off — user must toggle in dashboard |
