# Person Object Reference

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `createdAt` | DateTime | auto | Creation timestamp |
| `updatedAt` | DateTime | auto | Last update timestamp |
| `deletedAt` | DateTime | — | Soft-delete timestamp |
| `name` | FullName | — | `{ firstName, lastName }` |
| `emails` | Emails | — | `{ primaryEmail, additionalEmails }` |
| `phones` | Phones | — | `{ primaryPhoneNumber, primaryPhoneCountryCode, additionalPhones }` |
| `linkedinLink` | Links | — | `{ primaryLinkUrl, primaryLinkLabel, secondaryLinks }` |
| `xLink` | Links | — | X/Twitter profile link |
| `jobTitle` | String | — | Job title |
| `city` | String | — | City name |
| `avatarUrl` | String | — | Avatar image URL |
| `avatarFile` | [FileObject] | — | Uploaded avatar files |
| `position` | Float | auto | Sort position |
| `companyId` | UUID | — | FK to Company |
| `createdBy` | Actor | auto | `{ source, workspaceMemberId, name }` |
| `updatedBy` | Actor | auto | `{ source, workspaceMemberId, name }` |
| `searchVector` | TSVector | auto | Full-text search index |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `company` | Company | Associated company |
| `attachments` | AttachmentConnection | File attachments |
| `noteTargets` | NoteTargetConnection | Linked notes |
| `taskTargets` | TaskTargetConnection | Linked tasks |
| `favorites` | FavoriteConnection | Favorited by members |
| `messageParticipants` | MessageParticipantConnection | Email message links |
| `calendarEventParticipants` | CalendarEventParticipantConnection | Calendar event links |
| `pointOfContactForOpportunities` | OpportunityConnection | Opportunities where this person is POC |
| `timelineActivities` | TimelineActivityConnection | Activity timeline |

## Filter Fields (PersonFilterInput)

All fields above plus logical combinators: `and`, `or`, `not`.

Nested filters: `name { firstName { eq: "Jane" } }`, `emails { primaryEmail { like: "%@example.com" } }`

## GraphQL Examples

### List people with company
```graphql
query {
  people(first: 20, filter: { city: { eq: "San Francisco" } }) {
    edges {
      node {
        id
        name { firstName lastName }
        emails { primaryEmail }
        jobTitle
        company { id name }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

### Create person linked to company
```graphql
mutation {
  createPerson(data: {
    name: { firstName: "Jane", lastName: "Doe" }
    emails: { primaryEmail: "jane@acme.com" }
    phones: { primaryPhoneNumber: "+15551234567", primaryPhoneCountryCode: "US" }
    jobTitle: "VP Engineering"
    city: "Austin"
    companyId: "company-uuid-here"
  }) {
    id name { firstName lastName }
  }
}
```

### Update person
```graphql
mutation {
  updatePerson(id: "person-uuid", data: {
    jobTitle: "CTO"
    city: "New York"
  }) {
    id jobTitle city
  }
}
```

### Find duplicates
```graphql
query {
  personDuplicates(ids: ["uuid1", "uuid2"]) {
    edges { node { id name { firstName lastName } } }
  }
}
```

### Merge people
```graphql
mutation {
  mergePeople(ids: ["uuid1", "uuid2"], conflictPriorityIndex: 0) {
    id name { firstName lastName } emails { primaryEmail }
  }
}
```

## REST Examples

```bash
# List
curl "$BASE/rest/people?limit=10&order_by=name[AscNullsFirst]" -H "Authorization: Bearer $KEY"

# Get by ID
curl "$BASE/rest/people/{id}" -H "Authorization: Bearer $KEY"

# Filter by email domain
curl "$BASE/rest/people?filter=emails.primaryEmail[ilike]:\"%@anthropic.com\"" -H "Authorization: Bearer $KEY"

# Create
curl -X POST "$BASE/rest/people" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":{"firstName":"Jane","lastName":"Doe"},"emails":{"primaryEmail":"jane@acme.com"},"jobTitle":"Engineer"}'

# Update
curl -X PATCH "$BASE/rest/people/{id}" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"jobTitle":"Sr. Engineer"}'

# Soft delete
curl -X DELETE "$BASE/rest/people/{id}" -H "Authorization: Bearer $KEY"

# Restore
curl -X PATCH "$BASE/rest/restore/people/{id}" -H "Authorization: Bearer $KEY"
```
