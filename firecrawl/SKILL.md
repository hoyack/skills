---
name: firecrawl
version: 1.0.0
description: >
  Scrape, crawl, and extract structured data from any website. Use the MCP server
  as the primary interface for web scraping, crawling, and LLM-powered data extraction.
  Provides 12 tools via mcp__firecrawl__* prefixes including scraping, crawling,
  site mapping, search, and autonomous web research.
tags: [web, scrape, crawl, firecrawl, extraction, data, research, mcp]
metadata:
  clawdbot:
    emoji: 🔥
    requires:
      bins: []
env:
  FIRECRAWL_API_KEY:
    description: API key for Firecrawl authentication
    required: true
  FIRECRAWL_API_URL:
    description: URL of the Firecrawl server
    required: false
---

# Firecrawl Web Scraping Skill

Scrape, crawl, and extract structured data from any website. **Use the MCP server as the primary interface** — fall back to direct REST only for operations the MCP tools don't cover.

## MCP Server (Primary Interface)

The Firecrawl MCP server is registered as `firecrawl` in `~/.mcp.json` and provides 12 tools via `mcp__firecrawl__*` prefixes.

### MCP Tools — Quick Reference

| Tool | Purpose |
|------|---------|
| `mcp__firecrawl__firecrawl_scrape` | Scrape a single URL to markdown/HTML/links/screenshot |
| `mcp__firecrawl__firecrawl_crawl` | Crawl an entire site (async, returns job ID) |
| `mcp__firecrawl__firecrawl_check_crawl_status` | Poll crawl job progress |
| `mcp__firecrawl__firecrawl_map` | Discover all URLs on a site |
| `mcp__firecrawl__firecrawl_search` | Web search with optional content scraping |
| `mcp__firecrawl__firecrawl_extract` | LLM-powered structured data extraction |
| `mcp__firecrawl__firecrawl_agent` | Autonomous web research agent (async) |
| `mcp__firecrawl__firecrawl_agent_status` | Poll agent job results |
| `mcp__firecrawl__firecrawl_browser_create` | Create browser session (cloud only) |
| `mcp__firecrawl__firecrawl_browser_execute` | Execute in browser session (cloud only) |
| `mcp__firecrawl__firecrawl_browser_list` | List browser sessions (cloud only) |
| `mcp__firecrawl__firecrawl_browser_delete` | Delete browser session (cloud only) |

### When to use MCP vs Direct API

| Use MCP tools when... | Use direct API when... |
|----------------------|----------------------|
| Scraping single pages | Batch scraping multiple URLs |
| Crawling sites and checking status | Browser actions (click, fill, scroll) |
| Mapping site URLs | Custom headers or proxy settings |
| Web search | Change tracking / branding extraction |
| LLM extraction | Deep research endpoint |
| Agent research tasks | Queue/credit monitoring |

### MCP Server Location

- **Binary:** `firecrawl-mcp` (globally installed via npm)
- **Config:** `~/.mcp.json` → `firecrawl` entry
- **Env vars:** `FIRECRAWL_API_KEY`, `FIRECRAWL_API_URL`

## Configuration

Load environment from `.openclaw/workspace/skills/firecrawl/.env`:
- `FIRECRAWL_BASE_URL` — Server URL (default: `http://localhost:3002`)
- `FIRECRAWL_API_KEY` — API key for authentication

## Authentication

All direct API requests require:
```
Authorization: Bearer $FIRECRAWL_API_KEY
```

## Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/scrape` | POST | Scrape single URL |
| `/v1/crawl` | POST | Start async crawl |
| `/v1/crawl/{id}` | GET | Check crawl status |
| `/v1/map` | POST | Discover URLs on a site |
| `/v1/search` | POST | Web search |
| `/v1/extract` | POST | Structured extraction |
| `/v1/batch/scrape` | POST | Batch scrape URLs |

## Scrape — Single URL

```bash
curl -X POST http://localhost:3002/v1/scrape \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown", "links"]
  }'
```

### Scrape Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to scrape |
| `formats` | string[] | `["markdown"]` | Output formats (see below) |
| `onlyMainContent` | boolean | `true` | Extract main content only |
| `includeTags` | string[] | — | CSS selectors to include |
| `excludeTags` | string[] | — | CSS selectors to exclude |
| `timeout` | int (ms) | 30000 | Request timeout |
| `waitFor` | int (ms) | 0 | Wait before scraping (max 60000) |
| `mobile` | boolean | false | Use mobile viewport |
| `headers` | object | — | Custom HTTP headers |
| `parsePDF` | boolean | true | Parse PDF content |
| `removeBase64Images` | boolean | true | Strip base64 images |
| `blockAds` | boolean | true | Block advertisements |
| `actions` | array | — | Browser actions (see docs/actions.md) |

### Output Formats

| Format | Description |
|--------|-------------|
| `markdown` | Cleaned markdown (default) |
| `html` | Cleaned HTML |
| `rawHtml` | Raw unprocessed HTML |
| `links` | Array of all links found |
| `screenshot` | Viewport screenshot (base64) |
| `screenshot@fullPage` | Full page screenshot (base64) |
| `extract` | LLM-extracted data (requires `extract` options) |
| `json` | JSON extraction (alias for extract) |
| `summary` | LLM-generated summary |
| `branding` | Brand identity (colors, fonts, logo) |

### Scrape Response

```json
{
  "success": true,
  "data": {
    "markdown": "# Page Title\n\nContent...",
    "links": ["https://example.com/page1", "..."],
    "metadata": {
      "title": "Page Title",
      "statusCode": 200,
      "sourceURL": "https://example.com",
      "url": "https://example.com"
    }
  }
}
```

## Crawl — Entire Site

```bash
# Start crawl
curl -X POST http://localhost:3002/v1/crawl \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com",
    "limit": 50,
    "maxDepth": 3,
    "scrapeOptions": {"formats": ["markdown"]}
  }'
# Returns: {"success": true, "id": "job-uuid"}

# Check status
curl http://localhost:3002/v1/crawl/JOB_ID \
  -H "Authorization: Bearer fc-test-key-local"

# Cancel crawl
curl -X DELETE http://localhost:3002/v1/crawl/JOB_ID \
  -H "Authorization: Bearer fc-test-key-local"
```

### Crawl Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | Starting URL |
| `limit` | int | 10000 | Max pages to crawl |
| `maxDepth` | int | 10 | Max link depth |
| `includePaths` | string[] | — | URL path patterns to include |
| `excludePaths` | string[] | — | URL path patterns to exclude |
| `allowExternalLinks` | boolean | false | Follow external links |
| `allowSubdomains` | boolean | false | Follow subdomains |
| `ignoreSitemap` | boolean | false | Skip sitemap discovery |
| `ignoreRobotsTxt` | boolean | false | Ignore robots.txt |
| `scrapeOptions` | object | — | Scrape settings per page |

## Map — Discover URLs

```bash
curl -X POST http://localhost:3002/v1/map \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "limit": 100}'
# Returns: {"success": true, "links": ["url1", "url2", ...]}
```

### Map Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | Base URL |
| `limit` | int | 5000 | Max URLs to discover (max 100000) |
| `search` | string | — | Filter URLs by search term |
| `includeSubdomains` | boolean | true | Include subdomains |
| `ignoreSitemap` | boolean | false | Skip sitemap |
| `sitemapOnly` | boolean | false | Only use sitemap |

## Search — Web Search

Firecrawl integrates with SearXNG for web search, optionally scraping each result.

```bash
curl -X POST http://localhost:3002/v1/search \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "docker compose tutorial",
    "limit": 5,
    "scrapeOptions": {"formats": ["markdown"]}
  }'
```

### Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query |
| `limit` | int | 5 | Max results (max 100) |
| `lang` | string | `"en"` | Language |
| `country` | string | `"us"` | Country code |
| `scrapeOptions` | object | — | Optionally scrape each result page |

## Extract — Structured Data

Requires an LLM API key (OpenAI or Ollama) configured in the Firecrawl `.env`.

```bash
curl -X POST http://localhost:3002/v1/extract \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/pricing"],
    "prompt": "Extract pricing tiers with name, price, and features",
    "schema": {
      "type": "object",
      "properties": {
        "plans": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "price": {"type": "string"},
              "features": {"type": "array", "items": {"type": "string"}}
            }
          }
        }
      }
    }
  }'
```

## Batch Scrape — Multiple URLs

```bash
curl -X POST http://localhost:3002/v1/batch/scrape \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/page1", "https://example.com/page2"],
    "formats": ["markdown"]
  }'
# Returns job ID, poll with GET /v1/batch/scrape/{id}
```

## Browser Actions

Pass `actions` array in scrape requests to interact with pages before extracting content.

| Action | Parameters | Example |
|--------|-----------|---------|
| `wait` | `milliseconds` or `selector` | `{"type":"wait","milliseconds":2000}` |
| `click` | `selector` | `{"type":"click","selector":"#login-btn"}` |
| `write` | `text` | `{"type":"write","text":"hello"}` |
| `press` | `key` | `{"type":"press","key":"Enter"}` |
| `scroll` | `direction` | `{"type":"scroll","direction":"down"}` |
| `screenshot` | `fullPage` | `{"type":"screenshot","fullPage":true}` |
| `scrape` | — | `{"type":"scrape"}` |

```bash
curl -X POST http://localhost:3002/v1/scrape \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown"],
    "actions": [
      {"type": "wait", "milliseconds": 2000},
      {"type": "click", "selector": ".load-more"},
      {"type": "wait", "milliseconds": 1000},
      {"type": "scrape"}
    ]
  }'
```

## Self-Hosted Limitations

- `/v1/extract` requires OpenAI or Ollama configured
- `firecrawl_agent` requires LLM backend
- Browser session tools (`browser_create/execute/delete/list`) are cloud-only
- No Fire-engine access (advanced bot detection bypass)

## Detailed References

- [docs/actions.md](docs/actions.md) — Browser action types and examples
- [docs/crawl-patterns.md](docs/crawl-patterns.md) — Crawl strategies and patterns

## Queue Admin Panel

Access at: `http://localhost:3002/admin/firecrawl-admin-2026/queues`

## MCP Update

```bash
npm install -g firecrawl-mcp
# Then restart Claude Code
```
