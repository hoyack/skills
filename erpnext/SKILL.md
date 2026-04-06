---
name: erpnext
version: 1.0.0
description: >
  Interact with ERPNext (Frappe Framework) for accounting, inventory, manufacturing,
  CRM, HR, and more. Use the MCP server as the primary interface for CRUD operations
  across any DocType. Provides 6 generic tools via mcp__erpnext__* prefixes.
tags: [erp, erpnext, frappe, accounting, inventory, crm, manufacturing, mcp]
metadata:
  clawdbot:
    emoji: 📦
    requires:
      bins: []
env:
  ERPNEXT_BASE_URL:
    description: URL of the ERPNext server
    required: true
  ERPNEXT_API_KEY:
    description: API key for ERPNext authentication
    required: true
  ERPNEXT_API_SECRET:
    description: API secret for ERPNext authentication
    required: true
---

# ERPNext API Skill

Interact with ERPNext (Frappe Framework) for accounting, inventory, manufacturing, CRM, HR, and more. **Use the MCP server as the primary interface** — fall back to direct REST only for operations the MCP tools don't cover.

## MCP Server (Primary Interface)

The ERPNext MCP server is registered as `erpnext` in `~/.mcp.json` and provides 6 generic tools accessible via `mcp__erpnext__*` prefixes. These tools work across **every DocType** in the system. **Always prefer these tools over raw API calls.**

### MCP Tools — Quick Reference

| Tool | Purpose | Example |
|------|---------|---------|
| `mcp__erpnext__get_doctypes` | List all available DocTypes | Discover what's in the system |
| `mcp__erpnext__get_doctype_fields` | Get field schema for a DocType | `{"doctype": "Customer"}` → all fields, types, options |
| `mcp__erpnext__get_documents` | List/filter documents | `{"doctype": "Item", "fields": ["name","item_name"], "limit": 10}` |
| `mcp__erpnext__create_document` | Create any document | `{"doctype": "Customer", "data": {"customer_name": "Acme"}}` |
| `mcp__erpnext__update_document` | Update any document | `{"doctype": "Customer", "name": "Acme", "data": {"territory": "US"}}` |
| `mcp__erpnext__run_report` | Execute built-in reports | `{"report_name": "General Ledger", "filters": {"company": "Hoyack"}}` |

### When to use MCP vs Direct API

| Use MCP tools when... | Use direct API when... |
|----------------------|----------------------|
| CRUD on any DocType | Document submission/cancellation (docstatus workflow) |
| Listing with filters and field selection | RPC methods (get_count, get_value, rename_doc) |
| Getting DocType schemas | File uploads |
| Running reports | Search link / autocomplete |
| Creating and updating documents | Complex or_filters, group_by queries |
| | Child table operations with parent/parenttype |

### MCP Server Location

- **Source:** `~/.openclaw/workspace/mcp-servers/erpnext-mcp-server/`
- **Config:** `~/.mcp.json` → `erpnext` entry
- **Env vars:** `ERPNEXT_URL`, `ERPNEXT_API_KEY`, `ERPNEXT_API_SECRET` (set in mcp.json)

## Configuration

Load environment from `.openclaw/workspace/skills/erpnext/.env`:
- `ERPNEXT_BASE_URL` — Server base URL (default: `http://localhost:8888`)
- `ERPNEXT_API_KEY` — API key
- `ERPNEXT_API_SECRET` — API secret
- `ERPNEXT_AUTH_TOKEN` — Pre-formatted `token key:secret`

## Authentication

**Token auth (preferred):**
```
Authorization: token <api_key>:<api_secret>
```

**Basic auth (alternative):**
```
Authorization: Basic <base64(api_key:api_secret)>
```

## Direct API Architecture (Fallback)

ERPNext's API is built on the Frappe Framework. Everything is a **DocType** (document type). The API has two main patterns:

| Pattern | Endpoint | Purpose |
|---------|----------|---------|
| **Resource API** | `GET/POST/PUT/DELETE /api/resource/{DocType}` | CRUD on any DocType |
| **RPC API** | `POST /api/method/{dotted.path}` | Call server-side methods |

## Resource API

The resource API provides uniform CRUD for every DocType in the system.

### List records
```bash
GET /api/resource/{DocType}?fields=[...]&filters=[...]&limit_page_length=20&limit_start=0&order_by=creation desc
```

### Get single record
```bash
GET /api/resource/{DocType}/{name}
```

### Create record
```bash
POST /api/resource/{DocType}
Content-Type: application/json
{"field1": "value1", "field2": "value2"}
```

### Update record
```bash
PUT /api/resource/{DocType}/{name}
Content-Type: application/json
{"field_to_update": "new_value"}
```

### Delete record
```bash
DELETE /api/resource/{DocType}/{name}
```

## Query Parameters

### fields
JSON array of field names to return:
```
fields=["name","customer_name","territory"]
```

Use `["*"]` to get all fields. Default returns only `name`.

### filters
JSON array of filter conditions `[fieldname, operator, value]`:
```
filters=[["status","=","Open"],["creation",">","2024-01-01"]]
```

**Operators:** `=`, `!=`, `>`, `<`, `>=`, `<=`, `like`, `not like`, `in`, `not in`, `is`, `is not`, `between`

```
# Single filter shorthand
filters=[["customer_type","=","Company"]]

# Multiple filters (AND)
filters=[["status","=","Open"],["grand_total",">",1000]]

# IN operator
filters=[["status","in",["Open","Overdue"]]]

# LIKE pattern
filters=[["customer_name","like","%Plastics%"]]

# Between dates
filters=[["posting_date","between",["2025-01-01","2025-12-31"]]]

# IS NULL
filters=[["territory","is","not set"]]
```

### order_by
Sort field and direction:
```
order_by=creation desc
order_by=modified asc
order_by=grand_total desc
```

### limit_page_length
Number of records to return (default: 20, max: no hard limit, use 0 for all):
```
limit_page_length=100
```

### limit_start
Offset for pagination:
```
limit_start=20&limit_page_length=20   # Page 2
```

### or_filters
Same format as filters but conditions are OR'd:
```
or_filters=[["status","=","Open"],["status","=","Overdue"]]
```

### group_by
Group results:
```
group_by=customer
```

### parent / parenttype
For child table records:
```
filters=[["parent","=","SO-00001"]]&parenttype=Sales Order
```

## RPC Methods

Frappe exposes server-side Python functions as HTTP endpoints.

### Core RPC Methods

```bash
# Get logged-in user
GET /api/method/frappe.auth.get_logged_user

# Get list (alternative to resource API, supports more options)
POST /api/method/frappe.client.get_list
{"doctype":"Customer","fields":["name","customer_name"],"limit_page_length":10}

# Get count
POST /api/method/frappe.client.get_count
{"doctype":"Sales Invoice","filters":[["status","=","Paid"]]}

# Get single value
POST /api/method/frappe.client.get_value
{"doctype":"Customer","filters":{"name":"Grant Plastics Ltd."},"fieldname":"customer_name"}

# Get document (full)
POST /api/method/frappe.client.get
{"doctype":"Sales Invoice","name":"ACC-SINV-2026-00001"}

# Insert (create)
POST /api/method/frappe.client.insert
{"doc":{"doctype":"Customer","customer_name":"New Corp","customer_type":"Company","customer_group":"Commercial"}}

# Rename
POST /api/method/frappe.client.rename_doc
{"doctype":"Customer","old":"Old Name","new":"New Name"}

# Get versions (app info)
GET /api/method/frappe.utils.change_log.get_versions

# Run report
POST /api/method/frappe.desk.query_report.run
{"report_name":"General Ledger","filters":{"company":"Hoyack","from_date":"2025-01-01","to_date":"2025-12-31"}}

# Search link (autocomplete)
GET /api/method/frappe.desk.search.search_link?doctype=Customer&txt=Grant

# Get metadata (DocType schema)
GET /api/method/frappe.client.get_list
{"doctype":"DocField","filters":{"parent":"Customer"},"fields":["fieldname","fieldtype","label","options"],"limit_page_length":0}
```

## Document Workflow (docstatus)

ERPNext documents follow a submission workflow:

| docstatus | State | Description |
|-----------|-------|-------------|
| 0 | Draft | Can be edited or deleted |
| 1 | Submitted | Locked, can only be amended or cancelled |
| 2 | Cancelled | Cancelled, preserved for audit |

**Submit a document:**
```bash
POST /api/method/frappe.client.submit
{"doc":{"doctype":"Sales Invoice","name":"ACC-SINV-2026-00001"}}
```

**Cancel a document:**
```bash
POST /api/method/frappe.client.cancel
{"doctype":"Sales Invoice","name":"ACC-SINV-2026-00001"}
```

**Amend (creates copy of cancelled doc):**
```bash
POST /api/method/frappe.client.amend
{"doctype":"Sales Invoice","name":"ACC-SINV-2026-00001"}
```

## Response Format

**List response:**
```json
{ "data": [{"name": "CUST-001"}, {"name": "CUST-002"}] }
```

**Single record response:**
```json
{ "data": { "name": "CUST-001", "customer_name": "Acme Corp", ... } }
```

**RPC response:**
```json
{ "message": <return_value> }
```

**Error response:**
```json
{
  "exc_type": "ValidationError",
  "exception": "...",
  "_server_messages": "[\"...\"]"
}
```

## Core DocTypes by Module

See `docs/` for detailed field references per module:

| Module | Key DocTypes | Doc Reference |
|--------|-------------|---------------|
| Selling | Customer, Sales Order, Quotation | [docs/selling.md](docs/selling.md) |
| Buying | Supplier, Purchase Order, Material Request | [docs/buying.md](docs/buying.md) |
| Accounts | Sales Invoice, Purchase Invoice, Payment Entry, Journal Entry | [docs/accounts.md](docs/accounts.md) |
| Stock | Item, Warehouse, Stock Entry, Delivery Note, Purchase Receipt | [docs/stock.md](docs/stock.md) |
| Manufacturing | BOM, Work Order, Job Card | [docs/manufacturing.md](docs/manufacturing.md) |
| CRM | Lead, Opportunity, Campaign | [docs/crm.md](docs/crm.md) |
| Projects | Project, Task, Timesheet | [docs/projects.md](docs/projects.md) |
| HR | Employee, Leave Application, Payroll | [docs/hr.md](docs/hr.md) |
| Support | Issue, Warranty Claim | [docs/support.md](docs/support.md) |
| Assets | Asset, Asset Movement | [docs/assets.md](docs/assets.md) |

## File Uploads

```bash
# Upload file
POST /api/method/upload_file
Content-Type: multipart/form-data
file=@document.pdf
doctype=Sales Invoice
docname=ACC-SINV-2026-00001
```

## Pagination Pattern

```bash
# Page 1
GET /api/resource/Item?limit_page_length=20&limit_start=0

# Page 2
GET /api/resource/Item?limit_page_length=20&limit_start=20

# Page 3
GET /api/resource/Item?limit_page_length=20&limit_start=40

# All records (no pagination)
GET /api/resource/Item?limit_page_length=0
```

## Rate Limits

ERPNext does not enforce per-endpoint rate limits by default, but:
- Large queries with `limit_page_length=0` can be slow
- Batch operations should be throttled client-side
- The `frappe.rate_limiter` can be configured server-side

## Current Instance Info

- **Frappe**: 16.13.0
- **ERPNext**: 16.12.0
- **Companies**: Hoyack, Hoyack (Demo)
- **Demo data**: 3 Customers, 3 Suppliers, 10 Items, 5 Sales Orders, 5 Sales Invoices, 10 Purchase Orders, 6 Purchase Invoices

## MCP Server Setup & Maintenance

The MCP server source lives at `~/.openclaw/workspace/mcp-servers/erpnext-mcp-server/`. If you need to rebuild after updates:

```bash
cd ~/.openclaw/workspace/mcp-servers/erpnext-mcp-server
git pull
npm install
npm run build
```

Restart Claude Code after rebuilding to pick up changes. The server runs as a stdio child process — no separate daemon to manage.

### MCP + Direct API Example Workflow

A typical workflow combining MCP tools and direct API for a full sales cycle:

```
1. mcp__erpnext__create_document  → Create Customer
2. mcp__erpnext__create_document  → Create Sales Order with items
3. curl POST /api/method/frappe.client.submit  → Submit the Sales Order (MCP can't submit)
4. mcp__erpnext__get_documents    → Check Sales Invoice status
5. mcp__erpnext__run_report       → Run Accounts Receivable report
```
