---
name: twenty-crm
version: 1.0.0
description: >
  Interact with the Twenty CRM open-source CRM. Use the MCP server as the primary
  interface for managing contacts, companies, opportunities, tasks, and activities.
  Provides 29 tools via mcp__twenty-crm__* prefixes. Use for CRM operations,
  pipeline management, contact tracking, and deal flow automation.
tags: [crm, twenty, contacts, companies, opportunities, sales, pipeline, mcp]
metadata:
  clawdbot:
    emoji: 📊
    requires:
      bins: []
env:
  TWENTY_CRM_BASE_URL:
    description: URL of the Twenty CRM server
    required: true
  TWENTY_CRM_API_KEY:
    description: API key for Twenty CRM authentication
    required: true
---

# Twenty CRM API Skill

Interact with the Twenty CRM open-source CRM. **Use the MCP server as the primary interface** — fall back to direct GraphQL/REST only for operations the MCP tools don't cover.

## MCP Server (Primary Interface)

The Twenty CRM MCP server is registered as `twenty-crm` in `~/.mcp.json` and provides 29 tools accessible via `mcp__twenty-crm__*` prefixes. **Always prefer these tools over raw API calls.**

### MCP Tools — Quick Reference

| Tool | Purpose |
|------|---------|
| `mcp__twenty-crm__search_contacts` | Search people by name/email |
| `mcp__twenty-crm__get_contact` | Get contact by ID |
| `mcp__twenty-crm__create_contact` | Create a person (firstName, lastName required) |
| `mcp__twenty-crm__update_contact` | Update person fields by ID |
| `mcp__twenty-crm__search_companies` | Search companies by name/domain |
| `mcp__twenty-crm__get_company` | Get company by ID |
| `mcp__twenty-crm__create_company` | Create a company (name required) |
| `mcp__twenty-crm__update_company` | Update company fields by ID |
| `mcp__twenty-crm__search_opportunities` | Search/filter deals (by stage, amount, date, company) |
| `mcp__twenty-crm__get_opportunity` | Get opportunity by ID |
| `mcp__twenty-crm__create_opportunity` | Create deal (name required; amount as `{value, currency}`) |
| `mcp__twenty-crm__update_opportunity` | Update deal fields by ID |
| `mcp__twenty-crm__list_opportunities_by_stage` | Pipeline view grouped by stage |
| `mcp__twenty-crm__create_task` | Create task (title required; status: TODO/IN_PROGRESS/DONE) |
| `mcp__twenty-crm__get_tasks` | List tasks with pagination |
| `mcp__twenty-crm__create_note` | Create a note (body required) |
| `mcp__twenty-crm__create_comment` | Comment on any record |
| `mcp__twenty-crm__get_activities` | Unified activity timeline |
| `mcp__twenty-crm__filter_activities` | Filter activities by type/date/status |
| `mcp__twenty-crm__get_entity_activities` | Activities for a specific person/company/opportunity |
| `mcp__twenty-crm__list_all_objects` | Discover all objects (standard + custom) |
| `mcp__twenty-crm__get_object_schema` | Full field schema for any object |
| `mcp__twenty-crm__get_field_metadata` | Field details across objects |
| `mcp__twenty-crm__get_company_contacts` | All people at a company |
| `mcp__twenty-crm__get_person_opportunities` | Deals where person is POC |
| `mcp__twenty-crm__link_opportunity_to_company` | Link deal to company/contact |
| `mcp__twenty-crm__transfer_contact_to_company` | Move person between companies |
| `mcp__twenty-crm__get_relationship_summary` | All relationships for an entity |
| `mcp__twenty-crm__find_orphaned_records` | Find records missing relationships |

### When to use MCP vs Direct API

| Use MCP tools when... | Use direct API when... |
|----------------------|----------------------|
| CRUD on contacts, companies, opportunities | Batch create (createMany mutations) |
| Searching and filtering records | Complex GraphQL queries with nested relations |
| Activity timeline and comments | Workflow automation mutations |
| Schema discovery and metadata | Calendar/messaging object queries |
| Relationship management | Merge/restore/destroy operations |
| Pipeline views | Custom filters with advanced comparators |

### MCP Server Location

- **Source:** `~/.openclaw/workspace/mcp-servers/twenty-mcp/`
- **Config:** `~/.mcp.json` → `twenty-crm` entry
- **Env vars:** `TWENTY_API_KEY`, `TWENTY_BASE_URL` (set in mcp.json)

## Configuration

Load environment from `.openclaw/workspace/skills/twenty-crm/.env`:
- `TWENTY_CRM_BASE_URL` — Server base URL (default: `http://localhost:3000`)
- `TWENTY_CRM_API_KEY` — Bearer token for authentication
- `TWENTY_CRM_WORKSPACE_ID` — Current workspace UUID

## Direct API Endpoints (Fallback)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `{base}/graphql` | POST | Core GraphQL API (records CRUD) |
| `{base}/metadata` | POST | Metadata GraphQL API (schema/config) |
| `{base}/rest/{objects}` | GET/POST/PATCH/DELETE | Core REST API |
| `{base}/rest/metadata/objects` | GET/POST/PATCH/DELETE | Metadata REST API |
| `{base}/rest/open-api/core` | GET | OpenAPI spec (Core) |
| `{base}/rest/open-api/metadata` | GET | OpenAPI spec (Metadata) |

## Authentication

All direct API requests require:
```
Authorization: Bearer $TWENTY_CRM_API_KEY
```

## Core Objects

| Object | List Query | Singular Query | Key Fields |
|--------|------------|----------------|------------|
| Person | `people` | `person` | name, emails, phones, jobTitle, city, companyId |
| Company | `companies` | `company` | name, domainName, address, employees, annualRecurringRevenue |
| Opportunity | `opportunities` | `opportunity` | name, amount, closeDate, stage, companyId, pointOfContactId |
| Note | `notes` | `note` | title, bodyV2 |
| Task | `tasks` | `task` | title, bodyV2, dueAt, status, assigneeId |
| WorkspaceMember | `workspaceMembers` | `workspaceMember` | name, userEmail, locale, timeZone |

Additional objects: Attachment, Blocklist, CalendarEvent, CalendarChannel, ConnectedAccount, Dashboard, Favorite, FavoriteFolder, Message, MessageChannel, MessageThread, MessageParticipant, MessageFolder, NoteTarget, TaskTarget, TimelineActivity, Workflow, WorkflowVersion, WorkflowRun, WorkflowAutomatedTrigger.

See `docs/` for detailed field references per object.

## GraphQL Patterns

### Query — List with pagination
```graphql
query {
  people(first: 10, after: "cursor", filter: { city: { eq: "SF" } }, orderBy: [{ createdAt: { direction: AscNullsFirst } }]) {
    edges {
      node { id name { firstName lastName } emails { primaryEmail } }
      cursor
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

### Query — Single record
```graphql
query {
  person(filter: { id: { eq: "uuid-here" } }) {
    id name { firstName lastName } emails { primaryEmail } company { name }
  }
}
```

### Query — Search across objects
```graphql
query {
  search(searchInput: "Dario", limit: 10) {
    people { edges { node { id name { firstName lastName } } } }
    companies { edges { node { id name } } }
  }
}
```

### Mutation — Create
```graphql
mutation {
  createPerson(data: {
    name: { firstName: "Jane", lastName: "Doe" }
    emails: { primaryEmail: "jane@example.com" }
    jobTitle: "Engineer"
    city: "Austin"
  }) {
    id name { firstName lastName }
  }
}
```

### Mutation — Create many
```graphql
mutation {
  createPeople(data: [
    { name: { firstName: "A", lastName: "B" } }
    { name: { firstName: "C", lastName: "D" } }
  ]) {
    edges { node { id } }
  }
}
```

### Mutation — Update
```graphql
mutation {
  updatePerson(id: "uuid", data: { jobTitle: "Sr. Engineer" }) {
    id jobTitle
  }
}
```

### Mutation — Delete (soft)
```graphql
mutation { deletePerson(id: "uuid") { id deletedAt } }
```

### Mutation — Destroy (permanent)
```graphql
mutation { destroyPerson(id: "uuid") { id } }
```

### Mutation — Restore
```graphql
mutation { restorePerson(id: "uuid") { id } }
```

### Mutation — Merge duplicates
```graphql
mutation {
  mergePeople(ids: ["uuid1", "uuid2"], conflictPriorityIndex: 0) {
    id name { firstName lastName }
  }
}
```

## REST Patterns

### List
```bash
curl "$BASE/rest/people?limit=10&order_by=createdAt[DescNullsLast]" \
  -H "Authorization: Bearer $KEY"
```

### Filter
```bash
# Equality
curl "$BASE/rest/people?filter=city[eq]:\"Austin\"" -H "Authorization: Bearer $KEY"

# Greater than (dates)
curl "$BASE/rest/companies?filter=createdAt[gte]:\"2024-01-01\"" -H "Authorization: Bearer $KEY"

# IN list
curl "$BASE/rest/tasks?filter=status[in]:[\"TODO\",\"IN_PROGRESS\"]" -H "Authorization: Bearer $KEY"

# OR logic
curl "$BASE/rest/people?filter=or(city[eq]:\"Austin\",city[eq]:\"NYC\")" -H "Authorization: Bearer $KEY"

# Nested field
curl "$BASE/rest/people?filter=emails.primaryEmail[eq]:jane@example.com" -H "Authorization: Bearer $KEY"
```

### Create
```bash
curl -X POST "$BASE/rest/people" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":{"firstName":"Jane","lastName":"Doe"},"emails":{"primaryEmail":"jane@example.com"}}'
```

### Update
```bash
curl -X PATCH "$BASE/rest/people/{id}" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"jobTitle":"Director"}'
```

### Batch create
```bash
curl -X POST "$BASE/rest/batch/people" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '[{"name":{"firstName":"A","lastName":"B"}},{"name":{"firstName":"C","lastName":"D"}}]'
```

### Pagination
```bash
# First page
curl "$BASE/rest/people?limit=20" -H "Authorization: Bearer $KEY"
# Next page (use endCursor from pageInfo)
curl "$BASE/rest/people?limit=20&starting_after=CURSOR" -H "Authorization: Bearer $KEY"
```

## Filter Comparators

| Comparator | Meaning | Example |
|------------|---------|---------|
| `eq` | Equals | `name[eq]:"Acme"` |
| `neq` | Not equals | `status[neq]:"DONE"` |
| `in` | In list | `stage[in]:["NEW","MEETING"]` |
| `containsAny` | Contains any | `tags[containsAny]:["vip"]` |
| `is` | Is null check | `deletedAt[is]:NULL` |
| `gt` | Greater than | `employees[gt]:100` |
| `gte` | Greater or equal | `createdAt[gte]:"2024-01-01"` |
| `lt` | Less than | `amount[lt]:50000` |
| `lte` | Less or equal | `closeDate[lte]:"2024-12-31"` |
| `startsWith` | Starts with | `name[startsWith]:"A"` |
| `like` | Pattern match (case-sensitive) | `name[like]:"%Corp%"` |
| `ilike` | Pattern match (case-insensitive) | `name[ilike]:"%corp%"` |

Logical: `and(...)`, `or(...)`, `not(...)`. Root comma-separated filters are AND.

## Enums

| Enum | Values |
|------|--------|
| TaskStatus | `TODO`, `IN_PROGRESS`, `DONE` |
| OpportunityStage | `NEW`, `SCREENING`, `MEETING`, `PROPOSAL`, `CUSTOMER` |

## Composite Field Types

| Type | Sub-fields | Used by |
|------|------------|---------|
| FullName | `firstName`, `lastName` | Person.name, WorkspaceMember.name |
| Emails | `primaryEmail`, `additionalEmails` | Person.emails |
| Phones | `primaryPhoneNumber`, `primaryPhoneCountryCode`, `additionalPhones` | Person.phones |
| Links | `primaryLinkUrl`, `primaryLinkLabel`, `secondaryLinks` | Company.domainName, *.linkedinLink, *.xLink |
| Address | `addressStreet1`, `addressStreet2`, `addressCity`, `addressState`, `addressPostcode`, `addressCountry` | Company.address |
| Currency | `amountMicros`, `currencyCode` | Company.annualRecurringRevenue, Opportunity.amount |
| Actor | `source`, `workspaceMemberId`, `name` | *.createdBy, *.updatedBy |
| RichText | (structured rich text) | Note.bodyV2, Task.bodyV2 |

## Rate Limits

| Constraint | Value |
|------------|-------|
| Requests per minute | 100 |
| Default page size | 60 |
| Max page size | 200 |
| Batch max records | 10,000 |
| Max merge records | 9 |

## Metadata API

Use the metadata API to inspect or modify workspace schema:

```graphql
# List all objects in workspace
query { objects { edges { node { id nameSingular namePlural isCustom fields { edges { node { name type } } } } } } }
```

```graphql
# Get current workspace info
query { currentWorkspace { id displayName } }
```

```graphql
# Get current user
query { currentUser { id email } }
```

Endpoint: `POST {base}/metadata` with same auth header.

## Webhooks

Configure in Settings > APIs & Webhooks. Events:
- `{object}.created` — fires on record creation
- `{object}.updated` — fires on record update
- `{object}.deleted` — fires on record deletion

Payloads are signed with HMAC SHA256 via `X-Twenty-Webhook-Signature` header.

## Detailed Object References

See the `docs/` subfolder for per-object field references:
- [docs/people.md](docs/people.md) — Person object
- [docs/companies.md](docs/companies.md) — Company object
- [docs/opportunities.md](docs/opportunities.md) — Opportunity object
- [docs/tasks.md](docs/tasks.md) — Task object
- [docs/notes.md](docs/notes.md) — Note object
- [docs/workspace-members.md](docs/workspace-members.md) — WorkspaceMember object
- [docs/workflows.md](docs/workflows.md) — Workflow, WorkflowVersion, WorkflowRun
- [docs/messaging.md](docs/messaging.md) — Messages, threads, channels
- [docs/calendar.md](docs/calendar.md) — Calendar events and channels
- [docs/metadata-api.md](docs/metadata-api.md) — Metadata API reference

## MCP Server Setup & Maintenance

The MCP server source lives at `~/.openclaw/workspace/mcp-servers/twenty-mcp/`. If you need to rebuild after updates:

```bash
cd ~/.openclaw/workspace/mcp-servers/twenty-mcp
git pull
npm install
npm run build
```

Restart Claude Code after rebuilding to pick up changes. The server runs as a stdio child process — no separate daemon to manage.
