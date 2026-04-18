# Netlify Functions Reference

Netlify Functions are AWS Lambda-backed serverless endpoints deployed alongside a project. Use them when the skill's form pipeline hits a wall — typically:

- A form submission must be forwarded to a third-party API (CRM, email service, webhook relay)
- The payload has to be enriched server-side (IP geolocation, reCAPTCHA verification, signing)
- The client submits JSON (which Netlify Forms rejects) and a shim is needed to convert to URL-encoded before re-POSTing into the Forms system, or to persist the data itself
- Custom redirect/response logic post-submission

## Directory Layout

Default location, zero-config:

```
<repo-root>/
├── netlify/
│   └── functions/
│       ├── contact.js          → /.netlify/functions/contact
│       ├── webhook.js          → /.netlify/functions/webhook
│       └── subdir/
│           └── handler.js      → /.netlify/functions/handler
├── netlify.toml
└── index.html
```

One file per function, named after the desired endpoint. TypeScript (`.ts`, `.mts`) is supported out of the box.

Override the directory in `netlify.toml`:

```toml
[functions]
  directory = "api"
```

## Runtime Options

Two runtime styles exist:

1. **v1 (handler export)** — the legacy AWS-Lambda-compatible shape. Still fully supported.
2. **v2 (default export)** — newer Netlify-native shape using Web APIs (`Request` / `Response`).

Prefer v2 for new code.

### v2 Handler Shape

```js
// netlify/functions/contact.mjs
export default async (req, context) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }
  const form = await req.formData();
  const data = Object.fromEntries(form);
  // ... do something with data ...
  return Response.redirect(new URL("/thank-you", req.url), 303);
};

export const config = {
  path: "/api/contact"   // custom route; default is /.netlify/functions/<filename>
};
```

### v1 Handler Shape

```js
// netlify/functions/contact.js
exports.handler = async (event, context) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const params = new URLSearchParams(event.body);
  const data = Object.fromEntries(params);

  // honeypot
  if (data["bot-field"]) {
    return { statusCode: 200, body: "OK" };
  }

  // example: forward to webhook
  if (process.env.WEBHOOK_URL) {
    await fetch(process.env.WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  }

  return {
    statusCode: 302,
    headers: { Location: "/thank-you" },
    body: ""
  };
};
```

### v1 `event` Object

| Field | Purpose |
|---|---|
| `httpMethod` | `GET`, `POST`, etc. |
| `headers` | Request headers (lowercased keys) |
| `body` | Raw body (string or base64 if binary) |
| `isBase64Encoded` | Bool — true for binary uploads |
| `queryStringParameters` | Parsed `?a=1&b=2` |
| `path` | Request path (post-redirect) |

### v1 Response Shape

```js
return {
  statusCode: 200,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ ok: true }),
  isBase64Encoded: false
};
```

## Runtime

- Node.js (version pinned via `NODE_VERSION` env var, default matches the team's default)
- Cold start ~300–800ms; warm <50ms
- Max execution time: **10s** (background functions: 15min; see "Background Functions")
- Max response size: **6 MB**
- Memory: 1024 MB (not configurable on consumer plans)

## Environment Variables

Functions inherit the project's env vars with `scopes: ["functions"]` set (see [projects.md](projects.md)). For secrets (API keys, webhook URLs), set via API or dashboard — **do not** commit to `netlify.toml`.

```bash
curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '[{
    "key": "WEBHOOK_URL",
    "values": [{"value": "https://hook.example.com/path", "context": "all"}],
    "scopes": ["functions", "runtime"]
  }]' \
  "https://api.netlify.com/api/v1/accounts/$ACCOUNT_ID/env?site_id=$SITE_ID"
```

## Invocation

- **From browser**: fetch `/.netlify/functions/<name>` (or the custom path defined in `config`)
- **Form `action`**: `<form action="/.netlify/functions/contact" method="POST">`
- **Local dev**: `netlify dev` (via Netlify CLI) serves functions at `localhost:8888`

## Dependencies

`package.json` at the repo root (or at `netlify/functions/`) is installed at build time:

```json
{
  "dependencies": {
    "node-fetch": "^3.3.0",
    "zod": "^3.22.0"
  }
}
```

ESM and CommonJS both work. Native Node `fetch` is available on Node 18+, so `node-fetch` is usually unneeded.

## Background Functions

File suffix: `-background`. Returns immediately to the client with 202, runs up to 15 minutes.

```
netlify/functions/send-newsletter-background.js
```

Invocation is fire-and-forget — the HTTP caller gets a 202 with no body.

## Scheduled Functions

Export a `config` object with `schedule` (cron syntax):

```js
export default async () => {
  // runs on schedule
};

export const config = {
  schedule: "@daily"   // or "0 */6 * * *" for every 6 hours
};
```

## Redirects to Functions

Map a friendly path via `netlify.toml`:

```toml
[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
```

Then `<form action="/api/contact">` hits `/.netlify/functions/contact`.

## Form-Handler Patterns

### A. Forward submissions to a webhook

Submission goes through Netlify Forms (captured + dashboard visible), then a background notification webhook runs. Simpler than a function — configure in dashboard under Forms notifications.

### B. Function as primary handler (bypasses Forms dashboard)

```html
<form action="/.netlify/functions/contact" method="POST">
  ...
</form>
```

Submissions don't appear in the Netlify Forms dashboard — the function owns persistence. Use this when Forms doesn't fit (JSON-native forms, custom validation, third-party-only capture).

### C. Function as pre-processor, then re-POST to Netlify Forms

Client → Function (validate, enrich) → re-POST with URL-encoded body to `/` with `form-name=...` → Netlify Forms captures it.

```js
export default async (req) => {
  const input = await req.json();          // accept JSON
  // ... validate / enrich ...
  const body = new URLSearchParams({
    "form-name": "contact",
    ...input
  });
  await fetch(new URL("/", req.url), {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString()
  });
  return new Response(null, { status: 204 });
};
```

## Logs

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/functions"
```

Per-invocation logs are not in the REST API — view in dashboard under **Project → Logs → Functions**, or stream with `netlify functions:log` via the CLI.

## Limits (Free Plan)

- 125,000 invocations/month
- 100 function-hours/month runtime
- 10s execution timeout (non-background)
- No concurrency limit in practice (spikes are handled by Lambda)

## Troubleshooting

| Symptom | Likely Cause |
|---|---|
| 404 on `/.netlify/functions/name` | File not in `netlify/functions/`, or function failed to build — check deploy logs |
| 502 | Function threw an uncaught error or exceeded timeout |
| Env var `undefined` inside function | Missing `functions` scope when set; re-set env var with correct scopes |
| Works locally, 500 in prod | Missing dependency in `package.json`, or node version mismatch |
| Function code commits fine but doesn't deploy | `netlify.toml` `[functions] directory` path wrong, or file extension unsupported |
