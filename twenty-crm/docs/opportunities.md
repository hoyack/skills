# Opportunity Object Reference

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `createdAt` | DateTime | auto | Creation timestamp |
| `updatedAt` | DateTime | auto | Last update timestamp |
| `deletedAt` | DateTime | — | Soft-delete timestamp |
| `name` | String | — | Opportunity/deal name |
| `amount` | Currency | — | `{ amountMicros, currencyCode }` — value in micros |
| `closeDate` | DateTime | — | Expected close date |
| `stage` | OpportunityStageEnum | yes | Pipeline stage |
| `position` | Float | auto | Sort position |
| `companyId` | UUID | — | FK to Company |
| `pointOfContactId` | UUID | — | FK to Person (primary contact) |
| `ownerId` | UUID | — | FK to WorkspaceMember (deal owner) |
| `createdBy` | Actor | auto | Creation actor |
| `updatedBy` | Actor | auto | Last update actor |
| `searchVector` | TSVector | auto | Full-text search index |

## OpportunityStageEnum

| Value | Description |
|-------|-------------|
| `NEW` | New lead/opportunity |
| `SCREENING` | Initial qualification |
| `MEETING` | Meeting scheduled/completed |
| `PROPOSAL` | Proposal sent |
| `CUSTOMER` | Won — converted to customer |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `company` | Company | Associated company |
| `pointOfContact` | Person | Primary contact person |
| `owner` | WorkspaceMember | Deal owner |
| `attachments` | AttachmentConnection | File attachments |
| `noteTargets` | NoteTargetConnection | Linked notes |
| `taskTargets` | TaskTargetConnection | Linked tasks |
| `favorites` | FavoriteConnection | Favorited by members |
| `timelineActivities` | TimelineActivityConnection | Activity timeline |

## GraphQL Examples

### List pipeline
```graphql
query {
  opportunities(
    first: 50
    filter: { stage: { in: ["NEW", "SCREENING", "MEETING", "PROPOSAL"] } }
    orderBy: [{ closeDate: { direction: AscNullsLast } }]
  ) {
    edges {
      node {
        id name
        amount { amountMicros currencyCode }
        closeDate stage
        company { id name }
        pointOfContact { name { firstName lastName } }
        owner { name { firstName lastName } }
      }
    }
  }
}
```

### Create opportunity
```graphql
mutation {
  createOpportunity(data: {
    name: "Acme Enterprise Deal"
    amount: { amountMicros: 120000000000, currencyCode: "USD" }
    closeDate: "2025-06-30T00:00:00.000Z"
    stage: SCREENING
    companyId: "company-uuid"
    pointOfContactId: "person-uuid"
  }) {
    id name stage
  }
}
```

### Advance stage
```graphql
mutation {
  updateOpportunity(id: "opp-uuid", data: { stage: PROPOSAL }) {
    id name stage
  }
}
```

### Won — mark as customer
```graphql
mutation {
  updateOpportunity(id: "opp-uuid", data: { stage: CUSTOMER }) {
    id name stage closeDate
  }
}
```

### Filter by close date range
```graphql
query {
  opportunities(filter: {
    and: [
      { closeDate: { gte: "2025-01-01T00:00:00Z" } }
      { closeDate: { lte: "2025-03-31T23:59:59Z" } }
    ]
  }) {
    edges { node { id name amount { amountMicros currencyCode } closeDate stage } }
  }
}
```

## REST Examples

```bash
# List opportunities in proposal stage
curl "$BASE/rest/opportunities?filter=stage[eq]:\"PROPOSAL\"&limit=20" \
  -H "Authorization: Bearer $KEY"

# Create
curl -X POST "$BASE/rest/opportunities" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Big Deal","amount":{"amountMicros":50000000000,"currencyCode":"USD"},"stage":"NEW","companyId":"uuid"}'

# Update stage
curl -X PATCH "$BASE/rest/opportunities/{id}" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"stage":"MEETING"}'
```
