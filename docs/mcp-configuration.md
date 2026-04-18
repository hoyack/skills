# MCP Server Configuration

All three services now have MCP (Model Context Protocol) servers configured!

## MCP Servers Overview

| Service | MCP Server | Tools | Status |
|---------|-----------|-------|--------|
| **SearXNG** | `mcp-searxng` | 2 tools | ✅ Ready |
| **Firecrawl** | `firecrawl-mcp` | 12 tools | ✅ Ready |
| **Twenty CRM** | `twenty-mcp` | 29 tools | ⚠️ Needs API Key |

---

## Configuration File

**Location:** `~/.mcp.json`

```json
{
  "mcpServers": {
    "searxng": {
      "command": "mcp-searxng",
      "env": {
        "SEARXNG_URL": "http://localhost:8090"
      }
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
        "TWENTY_API_KEY": "PLACEHOLDER_API_KEY"
      }
    }
  }
}
```

---

## SearXNG MCP Server ✅ Ready

**Package:** `mcp-searxng` (installed globally via npm)

### Available Tools

| Tool | Description |
|------|-------------|
| `mcp__searxng__searxng_web_search` | Search the web with query, pagination, time range, language |
| `mcp__searxng__web_url_read` | Fetch and extract content from a URL |

### Usage Examples

```javascript
// Search the web
mcp__searxng__searxng_web_search({
  query: "machine learning tutorials",
  pageno: 1,
  time_range: "month",
  language: "en",
  safesearch: 0
})

// Read URL content
mcp__searxng__web_url_read({
  url: "https://example.com/article",
  section: 0  // pagination section
})
```

### Configuration
- **SEARXNG_URL:** `http://localhost:8090`
- No API key required

---

## Firecrawl MCP Server ✅ Ready

**Package:** `firecrawl-mcp` (installed globally via npm)

### Available Tools

| Tool | Description |
|------|-------------|
| `mcp__firecrawl__firecrawl_scrape` | Scrape a single URL |
| `mcp__firecrawl__firecrawl_crawl` | Crawl an entire site (async) |
| `mcp__firecrawl__firecrawl_check_crawl_status` | Poll crawl job progress |
| `mcp__firecrawl__firecrawl_map` | Discover all URLs on a site |
| `mcp__firecrawl__firecrawl_search` | Web search with optional scraping |
| `mcp__firecrawl__firecrawl_extract` | LLM-powered structured data extraction |
| `mcp__firecrawl__firecrawl_agent` | Autonomous web research agent |
| `mcp__firecrawl__firecrawl_agent_status` | Poll agent job results |

### Usage Examples

```javascript
// Scrape a single page
mcp__firecrawl__firecrawl_scrape({
  url: "https://example.com",
  formats: ["markdown", "links"],
  onlyMainContent: true
})

// Crawl a website
mcp__firecrawl__firecrawl_crawl({
  url: "https://docs.example.com",
  limit: 50,
  maxDepth: 2,
  scrapeOptions: {
    formats: ["markdown"]
  }
})

// Check crawl status
mcp__firecrawl__firecrawl_check_crawl_status({
  jobId: "019d7c63-1237-71cd-94d1-97ee17296e11"
})

// Search the web
mcp__firecrawl__firecrawl_search({
  query: "docker compose tutorial",
  limit: 5
})

// Extract structured data
mcp__firecrawl__firecrawl_extract({
  urls: ["https://example.com/pricing"],
  prompt: "Extract pricing tiers with name, price, and features",
  schema: {
    type: "object",
    properties: {
      plans: {
        type: "array",
        items: {
          type: "object",
          properties: {
            name: { type: "string" },
            price: { type: "string" },
            features: { type: "array", items: { type: "string" } }
          }
        }
      }
    }
  }
})
```

### Configuration
- **FIRECRAWL_API_URL:** `http://localhost:3002`
- **FIRECRAWL_API_KEY:** `fc-test-key-local`

---

## Twenty CRM MCP Server ⚠️ Needs Setup

**Source:** `~/.openclaw/workspace/mcp-servers/twenty-mcp/`

### Available Tools (29 total)

| Category | Tools |
|----------|-------|
| **Contacts** | `search_contacts`, `get_contact`, `create_contact`, `update_contact` |
| **Companies** | `search_companies`, `get_company`, `create_company`, `update_company` |
| **Opportunities** | `search_opportunities`, `get_opportunity`, `create_opportunity`, `update_opportunity`, `list_opportunities_by_stage` |
| **Tasks** | `create_task`, `get_tasks` |
| **Notes** | `create_note`, `create_comment` |
| **Activities** | `get_activities`, `filter_activities`, `get_entity_activities` |
| **Schema** | `list_all_objects`, `get_object_schema`, `get_field_metadata` |
| **Relationships** | `get_company_contacts`, `get_person_opportunities`, `link_opportunity_to_company`, `transfer_contact_to_company`, `get_relationship_summary`, `find_orphaned_records` |

### Setup Required

Twenty CRM requires an API key that must be obtained from the web UI:

1. **Open Twenty CRM:** http://localhost:3000
2. **Create an admin account** (first-time setup)
3. **Navigate to:** Settings → APIs & Webhooks
4. **Create a new API key**
5. **Copy the API key** and update `~/.mcp.json`:

```json
{
  "mcpServers": {
    "twenty-crm": {
      "command": "node",
      "args": ["/home/hoyack/.openclaw/workspace/mcp-servers/twenty-mcp/dist/index.js"],
      "env": {
        "TWENTY_BASE_URL": "http://localhost:3000",
        "TWENTY_API_KEY": "YOUR_ACTUAL_API_KEY_HERE"
      }
    }
  }
}
```

6. **Restart Claude Code** to pick up the new configuration

### Usage Examples (after setup)

```javascript
// Search contacts
mcp__twenty-crm__search_contacts({
  query: "john",
  limit: 10
})

// Create a contact
mcp__twenty-crm__create_contact({
  firstName: "Jane",
  lastName: "Doe",
  email: "jane@example.com",
  jobTitle: "Engineer",
  city: "Austin"
})

// Create a company
mcp__twenty-crm__create_company({
  name: "Acme Corp",
  domainName: "acme.com",
  employees: 100
})

// Create an opportunity
mcp__twenty-crm__create_opportunity({
  name: "Enterprise Deal",
  amount: { value: 50000, currency: "USD" },
  stage: "PROPOSAL",
  companyId: "company-uuid"
})

// List opportunities by stage
mcp__twenty-crm__list_opportunities_by_stage()
```

---

## Installation Details

### SearXNG MCP
```bash
npm install -g mcp-searxng
```

### Firecrawl MCP
```bash
npm install -g firecrawl-mcp
```

### Twenty CRM MCP
```bash
mkdir -p ~/.openclaw/workspace/mcp-servers
cd ~/.openclaw/workspace/mcp-servers
git clone --depth 1 https://github.com/jezweb/twenty-mcp.git
cd twenty-mcp
npm install
npm run build
```

---

## Updating MCP Servers

```bash
# Update SearXNG MCP
npm install -g mcp-searxng

# Update Firecrawl MCP
npm install -g firecrawl-mcp

# Update Twenty CRM MCP
cd ~/.openclaw/workspace/mcp-servers/twenty-mcp
git pull
npm install
npm run build
```

After updating, **restart Claude Code** to pick up changes.

---

## Troubleshooting

### MCP Server Not Found
If you see errors about missing MCP servers:
```bash
# Check if binaries are in PATH
which mcp-searxng
which firecrawl-mcp

# Check if Twenty MCP is built
ls ~/.openclaw/workspace/mcp-servers/twenty-mcp/dist/index.js
```

### Connection Errors
- **SearXNG:** Verify http://localhost:8090 is accessible
- **Firecrawl:** Verify http://localhost:3002 is accessible
- **Twenty CRM:** Verify http://localhost:3000 is accessible and API key is correct

### Permission Errors
Ensure the MCP configuration file has correct permissions:
```bash
chmod 600 ~/.mcp.json
```

---

## Summary

| Service | Status | Action Required |
|---------|--------|-----------------|
| SearXNG | ✅ Ready | None |
| Firecrawl | ✅ Ready | None |
| Twenty CRM | ⚠️ Pending | Create API key in web UI |

**Next Steps:**
1. Open http://localhost:3000 (Twenty CRM)
2. Create admin account
3. Get API key from Settings → APIs & Webhooks
4. Update `~/.mcp.json` with the API key
5. Restart Claude Code
6. All 43 MCP tools (2 + 12 + 29) will be available!
