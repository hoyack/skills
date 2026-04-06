# Company Object Reference

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `createdAt` | DateTime | auto | Creation timestamp |
| `updatedAt` | DateTime | auto | Last update timestamp |
| `deletedAt` | DateTime | — | Soft-delete timestamp |
| `name` | String | — | Company name |
| `domainName` | Links | — | `{ primaryLinkUrl, primaryLinkLabel, secondaryLinks }` |
| `address` | Address | — | `{ addressStreet1, addressStreet2, addressCity, addressState, addressPostcode, addressCountry }` |
| `employees` | Float | — | Employee count |
| `linkedinLink` | Links | — | LinkedIn profile |
| `xLink` | Links | — | X/Twitter profile |
| `annualRecurringRevenue` | Currency | — | `{ amountMicros, currencyCode }` — amount is in micros (÷ 1,000,000) |
| `idealCustomerProfile` | Boolean | yes | ICP flag (default false) |
| `position` | Float | auto | Sort position |
| `accountOwnerId` | UUID | — | FK to WorkspaceMember |
| `createdBy` | Actor | auto | Creation actor |
| `updatedBy` | Actor | auto | Last update actor |
| `searchVector` | TSVector | auto | Full-text search index |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `people` | PersonConnection | People at this company |
| `accountOwner` | WorkspaceMember | Assigned account owner |
| `opportunities` | OpportunityConnection | Sales opportunities |
| `attachments` | AttachmentConnection | File attachments |
| `noteTargets` | NoteTargetConnection | Linked notes |
| `taskTargets` | TaskTargetConnection | Linked tasks |
| `favorites` | FavoriteConnection | Favorited by members |
| `timelineActivities` | TimelineActivityConnection | Activity timeline |

## GraphQL Examples

### List companies with people
```graphql
query {
  companies(first: 10, filter: { idealCustomerProfile: { eq: true } }) {
    edges {
      node {
        id
        name
        domainName { primaryLinkUrl }
        employees
        annualRecurringRevenue { amountMicros currencyCode }
        people(first: 5) {
          edges { node { id name { firstName lastName } jobTitle } }
        }
        accountOwner { name { firstName lastName } }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

### Create company
```graphql
mutation {
  createCompany(data: {
    name: "Acme Corp"
    domainName: { primaryLinkUrl: "https://acme.com", primaryLinkLabel: "Website" }
    address: {
      addressStreet1: "123 Main St"
      addressCity: "Austin"
      addressState: "TX"
      addressPostcode: "78701"
      addressCountry: "US"
    }
    employees: 250
    annualRecurringRevenue: { amountMicros: 5000000000000, currencyCode: "USD" }
    idealCustomerProfile: true
  }) {
    id name
  }
}
```

### Update company
```graphql
mutation {
  updateCompany(id: "company-uuid", data: {
    employees: 300
    annualRecurringRevenue: { amountMicros: 8000000000000, currencyCode: "USD" }
  }) {
    id name employees
  }
}
```

### Merge duplicate companies
```graphql
mutation {
  mergeCompanies(ids: ["uuid1", "uuid2"], conflictPriorityIndex: 0, dryRun: true) {
    id name domainName { primaryLinkUrl }
  }
}
```

### Group by
```graphql
query {
  companiesGroupBy(groupBy: [{ idealCustomerProfile: true }]) {
    groups { key count }
  }
}
```

## REST Examples

```bash
# List with revenue filter
curl "$BASE/rest/companies?filter=employees[gte]:100&order_by=name[AscNullsFirst]&limit=20" \
  -H "Authorization: Bearer $KEY"

# Create
curl -X POST "$BASE/rest/companies" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","domainName":{"primaryLinkUrl":"https://acme.com"},"employees":250}'

# Batch create
curl -X POST "$BASE/rest/batch/companies" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '[{"name":"Company A"},{"name":"Company B"},{"name":"Company C"}]'

# Find duplicates
curl -X POST "$BASE/rest/companies/duplicates" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"data":{"name":"Acme"}}'
```

## Currency Field Note

`annualRecurringRevenue` and `amount` use micros: the integer value divided by 1,000,000 gives the actual amount.

Example: `5000000000000` micros = `$5,000,000` (5M USD).
