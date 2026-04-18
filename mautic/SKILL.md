---
name: mautic
version: 1.0.0
description: >
  Interact with Mautic marketing automation platform. Use the MCP server as the primary
  interface for managing contacts, companies, campaigns, segments, forms, and emails.
  Provides 19 tools via mcp__mautic__* prefixes. Use for marketing automation,
  contact management, email campaigns, and lead tracking.
tags: [mautic, marketing, automation, crm, email, campaigns, contacts, mcp]
metadata:
  clawdbot:
    emoji: 📧
    requires:
      bins: []
env:
  MAUTIC_BASE_URL:
    description: URL of the Mautic API (e.g., http://localhost:8080/api)
    required: true
  MAUTIC_USERNAME:
    description: Mautic username for HTTP Basic Auth
    required: true
  MAUTIC_PASSWORD:
    description: Mautic password for HTTP Basic Auth
    required: true
---

# Mautic Marketing Automation Skill

Interact with Mautic marketing automation platform. **Use the MCP server as the primary interface** — fall back to direct REST API only for operations the MCP tools don't cover.

## MCP Server (Primary Interface)

The Mautic MCP server is registered as `mautic` in `~/.mcp.json` and provides 19 tools accessible via `mcp__mautic__*` prefixes. **Always prefer these tools over raw API calls.**

### MCP Tools — Quick Reference

| Tool | Purpose |
|------|---------|
| `mcp__mautic__search_contacts` | Search contacts by name/email |
| `mcp__mautic__get_contact` | Get contact by ID |
| `mcp__mautic__create_contact` | Create a contact (email required) |
| `mcp__mautic__update_contact` | Update contact by ID |
| `mcp__mautic__delete_contact` | Delete contact by ID |
| `mcp__mautic__list_companies` | List all companies |
| `mcp__mautic__get_company` | Get company by ID |
| `mcp__mautic__create_company` | Create a company (name required) |
| `mcp__mautic__list_campaigns` | List all campaigns |
| `mcp__mautic__get_campaign` | Get campaign details by ID |
| `mcp__mautic__add_contact_to_campaign` | Add contact to campaign |
| `mcp__mautic__list_segments` | List contact segments |
| `mcp__mautic__get_segment_contacts` | Get contacts in a segment |
| `mcp__mautic__add_contact_to_segment` | Add contact to segment |
| `mcp__mautic__list_forms` | List all forms |
| `mcp__mautic__get_form` | Get form details by ID |
| `mcp__mautic__list_emails` | List all emails |
| `mcp__mautic__get_email` | Get email details by ID |
| `mcp__mautic__send_email_to_contact` | Send email to specific contact |

### When to use MCP vs Direct API

| Use MCP tools when... | Use direct API when... |
|----------------------|------------------------|
| CRUD operations on contacts | Advanced campaign management |
| Managing companies | Custom API endpoints |
| Working with segments/forms/emails | Batch operations |
| Sending emails to contacts | Webhook management |

## Direct API (Fallback)

If the MCP server doesn't cover a specific operation, use the Mautic REST API directly.

### Base URL
```
http://192.168.1.68:8080/api
```

### Authentication
Use HTTP Basic Auth with the credentials from `.env`:
- Username: `<username>`
- Password: `<password>`

### Common Endpoints

```bash
# List contacts
curl -u <username>:<password> \
  http://192.168.1.68:8080/api/contacts

# Get single contact
curl -u <username>:<password> \
  http://192.168.1.68:8080/api/contacts/1

# Create contact
curl -X POST -u <username>:<password> \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","firstname":"John","lastname":"Doe"}' \
  http://192.168.1.68:8080/api/contacts/new
```

## Mautic Web Interface

Access the Mautic dashboard at: http://192.168.1.68:8080

Login credentials:
- Username: `<username>`
- Password: `<password>`

## Key Concepts

- **Contacts** — Individual people (leads/prospects)
- **Companies** — Organizations that contacts belong to
- **Campaigns** — Automated marketing workflows
- **Segments** — Dynamic groups of contacts based on filters
- **Forms** — Lead capture forms
- **Emails** — Email templates and broadcasts

## Response Format

Mautic API returns data in this structure:
```json
{
  "contacts": {
    "1": {
      "id": 1,
      "fields": {
        "all": {
          "email": "user@example.com",
          "firstname": "John",
          "lastname": "Doe"
        }
      }
    }
  },
  "total": 1
}
```
