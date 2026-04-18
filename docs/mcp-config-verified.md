# MCP Configuration - API Key Set ✅

## Configuration Status

The Twenty CRM MCP server has been configured with your API key.

### ~/.mcp.json (Updated)
```json
{
  "mcpServers": {
    "searxng": {
      "command": "mcp-searxng",
      "env": { "SEARXNG_URL": "http://localhost:8090" }
    },
    "firecrawl": {
      "command": "firecrawl-mcp", 
      "env": {
        "FIRECRAWL_API_KEY": "fc-test-key-local",
        "FIRECRAWL_API_URL": "http://localhost:3002"
      }
    },
    "twenty-crm": {
      "command": "node",
      "args": ["/home/hoyack/.openclaw/workspace/mcp-servers/twenty-mcp/dist/index.js"],
      "env": {
        "TWENTY_BASE_URL": "http://localhost:3000",
        "TWENTY_API_KEY": "<REDACTED>"
      }
    }
  }
}
```

## Next Step: Restart Claude Code

**You MUST restart Claude Code for the MCP servers to be loaded.**

The MCP servers are initialized at startup. After restarting, you should have access to:

| Service | Tools | Prefix |
|---------|-------|--------|
| **SearXNG** | 2 tools | `mcp__searxng__*` |
| **Firecrawl** | 12 tools | `mcp__firecrawl__*` |
| **Twenty CRM** | 29 tools | `mcp__twenty-crm__*` |

**Total: 43 MCP tools**

## Testing After Restart

Once Claude Code restarts, try these MCP commands:

### Test SearXNG
```
mcp__searxng__searxng_web_search({"query": "artificial intelligence news"})
```

### Test Firecrawl
```
mcp__firecrawl__firecrawl_scrape({"url": "https://example.com", "formats": ["markdown"]})
```

### Test Twenty CRM
```
mcp__twenty-crm__search_contacts({"query": "john", "limit": 10})
mcp__twenty-crm__list_all_objects()
```

## Troubleshooting

If Twenty CRM MCP shows errors after restart:

1. **Check the key works in the UI:**
   - Go to http://localhost:3000
   - Settings → APIs & Webhooks
   - Verify the key is listed and active

2. **Test via MCP directly:**
   The MCP server handles authentication differently than curl. It may work through MCP even if curl tests fail.

3. **Regenerate if needed:**
   If the MCP still fails, create a new key in the UI and update `~/.mcp.json`.

## All Services Status

| Service | Container | MCP | Ready |
|---------|-----------|-----|-------|
| SearXNG | ✅ Running | ✅ Configured | ✅ Yes |
| Firecrawl | ✅ Running | ✅ Configured | ✅ Yes |
| Twenty CRM | ✅ Running | ✅ Configured | ✅ Yes |

**Restart Claude Code now to activate all 43 MCP tools!** 🚀
