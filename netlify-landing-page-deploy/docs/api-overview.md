# Netlify API Overview

Base URL and auth conventions shared by every other doc in this folder.

## Base URL

```
https://api.netlify.com/api/v1
```

## Authentication

Personal Access Token (PAT) via `Authorization: Bearer <PAT>`:

```bash
curl -H "Authorization: Bearer $NETLIFY_PERSONAL_ACCESS_TOKEN" \
  https://api.netlify.com/api/v1/sites
```

Tokens are user-scoped; they can do anything the user can do. Store in `~/.mcp.json` or an env var, never commit.

## Terminology: Site vs Project

The Netlify dashboard and MCP tools use **"projects"**. The underlying API still uses `site_id` and `/sites/*` endpoints. Treat them as synonyms.

| UI / MCP | API |
|---|---|
| Project | Site |
| Project ID | `site_id` |
| `/projects/:name` | `/sites/:id` |

When reading API responses, `site_id` is the canonical identifier. When talking to users, call it the project.

## Pagination

List endpoints accept `page` and `per_page` (default 20, max 100). The `Link` response header carries `prev` / `next` URLs.

```
Link: <.../sites?page=2&per_page=20>; rel="next"
```

## Rate Limits

500 requests/minute per user token as of this writing. The MCP server will surface 429 errors if hit. Batch where possible; use `per_page=100` on list calls.

## Common Response Shapes

**Error:**
```json
{
  "code": 404,
  "message": "Not Found"
}
```

**Timestamps:** ISO 8601 UTC (`2026-04-15T14:24:15.855Z`).

**IDs:**
- Site/project: UUID (`ff465d05-bdd6-45ee-850b-39c3dfadc223`)
- Deploy: 24-char hex (`69df9f8ff7e94c0008aaa5e5`)
- Form: 24-char hex (`69df9f955ee3d80009a4ac7e`)
- Submission: 24-char hex (`69df9fad50468131bf76ec28`)

## Preferred Tool Selection

1. **MCP tools** (`mcp__netlify__*`) — preferred for anything they cover. See [mcp-tools.md](mcp-tools.md).
2. **Netlify CLI** (`netlify` / `ntl`) — useful for local dev, deploy previews, function invocation. Not required by the skill.
3. **Raw HTTP** — fallback for operations not covered by the MCP (DNS records, certain form operations, build hooks).
