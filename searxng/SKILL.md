---
name: searxng
version: 1.0.0
description: >
  Privacy-respecting metasearch engine aggregating results from 96+ search engines.
  Use the MCP server as the primary interface for web searches. Provides 2 tools
  via mcp__searxng__* prefixes including web search and URL content extraction.
tags: [search, searxng, web, privacy, metasearch, mcp]
metadata:
  clawdbot:
    emoji: 🔍
    requires:
      bins: []
env:
  SEARXNG_BASE_URL:
    description: URL of the SearXNG server
    required: true
---

# SearXNG Web Search Skill

Privacy-respecting metasearch engine aggregating results from 96+ search engines. **Use the MCP server as the primary interface** — fall back to direct API for advanced queries.

## MCP Server (Primary Interface)

The SearXNG MCP server is registered as `searxng` in `~/.mcp.json` and provides 2 tools via `mcp__searxng__*` prefixes.

### MCP Tools — Quick Reference

| Tool | Purpose |
|------|---------|
| `mcp__searxng__searxng_web_search` | Search the web (query, pageno, time_range, language, safesearch) |
| `mcp__searxng__web_url_read` | Fetch and extract content from a URL (with pagination/sections) |

### When to use MCP vs Direct API

| Use MCP tools when... | Use direct API when... |
|----------------------|----------------------|
| General web searching | Searching specific categories (images, news, videos) |
| Reading URL content | Using specific engines (e.g., only github, arxiv) |
| Simple paginated results | RSS feed output |
| | CSV export |
| | Accessing suggestions, infoboxes, answers |

### MCP Server Location

- **Binary:** `mcp-searxng` (globally installed via npm, package `mcp-searxng`)
- **Config:** `~/.mcp.json` → `searxng` entry
- **Env vars:** `SEARXNG_URL`

## Configuration

Load environment from `.openclaw/workspace/skills/searxng/.env`:
- `SEARXNG_BASE_URL` — Server URL (default: `http://localhost:8090`)

## Direct API (Fallback)

### Search Endpoint

```
GET http://localhost:8090/search?q={query}&format=json
```

### Query Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `q` | string | any | Search query (required) |
| `format` | string | `json`, `rss`, `csv`, `html` | Response format |
| `categories` | string | comma-separated | Category filter |
| `engines` | string | comma-separated | Specific engines to query |
| `language` | string | ISO code (`en`, `fr`, `all`) | Result language |
| `pageno` | int | 1+ | Page number (default 1) |
| `time_range` | string | `day`, `week`, `month`, `year` | Recency filter |
| `safesearch` | int | `0` (off), `1` (moderate), `2` (strict) | Content filtering |

### Example Queries

```bash
BASE="http://localhost:8090"

# Basic search
curl -s "$BASE/search?q=docker+tutorial&format=json" | python3 -m json.tool

# Search with time range (last week)
curl -s "$BASE/search?q=kubernetes+release&format=json&time_range=week"

# Search specific category
curl -s "$BASE/search?q=cat+photos&format=json&categories=images"

# Search specific engines only
curl -s "$BASE/search?q=python+asyncio&format=json&engines=stackoverflow,github"

# News search
curl -s "$BASE/search?q=AI+regulation&format=json&categories=news&time_range=month"

# Scientific papers
curl -s "$BASE/search?q=transformer+architecture&format=json&categories=science"

# Page 2 of results
curl -s "$BASE/search?q=rust+programming&format=json&pageno=2"

# RSS feed
curl -s "$BASE/search?q=open+source+CRM&format=rss"
```

## JSON Response Structure

```json
{
  "query": "search term",
  "number_of_results": 1234,
  "results": [
    {
      "url": "https://example.com/page",
      "title": "Result Title",
      "content": "Snippet description text...",
      "engine": "google",
      "engines": ["google", "duckduckgo", "bing"],
      "positions": [1, 3, 2],
      "score": 15.5,
      "category": "general",
      "publishedDate": "2026-03-27T12:21:00",
      "thumbnail": "",
      "img_src": ""
    }
  ],
  "answers": [],
  "corrections": [],
  "infoboxes": [],
  "suggestions": ["related term 1", "related term 2"],
  "unresponsive_engines": []
}
```

### Result Fields by Category

**General results:** `url`, `title`, `content`, `engines`, `score`, `publishedDate`

**News results** add: `source`, `metadata` (e.g., "9 days ago | Reuters")

**Image results** add: `thumbnail_src`, `img_src`, `resolution`, `img_format`, `filesize`, `source`

**Video results** add: `thumbnail`, `length` (duration), `author`

## Available Categories

| Category | Description |
|----------|-------------|
| `general` | Web search (default) |
| `images` | Image search |
| `videos` | Video search |
| `news` | News articles |
| `music` | Music and audio |
| `files` | File/torrent search |
| `it` | IT/programming |
| `science` | Scientific papers |
| `social media` | Social platforms |
| `map` | Map/location search |
| `q&a` | Q&A sites |
| `repos` | Code repositories |
| `packages` | Software packages |
| `wikimedia` | Wikimedia content |

## Key Engines

### General/Web
google, bing, duckduckgo, brave, startpage, wikipedia, wikidata

### IT / Development
github, docker hub, pypi, mdn, arch linux wiki, stackoverflow, askubuntu, superuser

### Science
arxiv, google scholar, pubmed, semantic scholar

### News
google news, bing news, reuters, yahoo news, wikinews

### Images
google images, bing images, flickr, pexels, pinterest, unsplash, deviantart

### Videos
youtube, google videos, dailymotion, vimeo

### Social
lemmy, mastodon, tootfinder

## Instance Config

Get full engine/category list:
```bash
curl -s http://localhost:8090/config | python3 -m json.tool
```

## Rate Limiting Notes

- SearXNG itself has no API rate limiting (limiter is disabled on this instance)
- Upstream engines (Google, Bing, etc.) may throttle if queried too aggressively
- Best practice: add client-side delays for bulk queries, use pagination instead of re-searching
- Cache results when possible (SearXNG caches internally via Valkey)

## Web UI

Access the visual search interface at: http://localhost:8090

## MCP Update

```bash
npm install -g mcp-searxng
# Then restart Claude Code
```
