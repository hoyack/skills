# Note Object Reference

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `createdAt` | DateTime | auto | Creation timestamp |
| `updatedAt` | DateTime | auto | Last update timestamp |
| `deletedAt` | DateTime | — | Soft-delete timestamp |
| `title` | String | — | Note title |
| `bodyV2` | RichText | — | Rich text body content |
| `position` | Float | auto | Sort position |
| `createdBy` | Actor | auto | Creation actor |
| `updatedBy` | Actor | auto | Last update actor |
| `searchVector` | TSVector | auto | Full-text search index |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `noteTargets` | NoteTargetConnection | Polymorphic links to Person/Company/Opportunity |
| `attachments` | AttachmentConnection | File attachments |
| `favorites` | FavoriteConnection | Favorited by members |
| `timelineActivities` | TimelineActivityConnection | Activity timeline |

## Note Targets

Notes use the same polymorphic target pattern as Tasks. A note can be linked to people, companies, or opportunities via `NoteTarget`.

```graphql
# Link note to a company
mutation {
  createNoteTarget(data: {
    noteId: "note-uuid"
    companyId: "company-uuid"
  }) { id }
}
```

## GraphQL Examples

### List notes
```graphql
query {
  notes(first: 20, orderBy: [{ updatedAt: { direction: DescNullsLast } }]) {
    edges {
      node {
        id title createdAt
        noteTargets(first: 5) {
          edges {
            node {
              person { name { firstName lastName } }
              company { name }
            }
          }
        }
      }
    }
  }
}
```

### Create note linked to person
```graphql
mutation {
  createNote(data: {
    title: "Meeting notes - Q1 review"
  }) {
    id title
  }
}
# Then link it:
mutation {
  createNoteTarget(data: {
    noteId: "new-note-uuid"
    personId: "person-uuid"
  }) { id }
}
```

### Search notes by title
```graphql
query {
  notes(filter: { title: { ilike: "%quarterly%" } }) {
    edges { node { id title createdAt } }
  }
}
```

## REST Examples

```bash
# List recent notes
curl "$BASE/rest/notes?order_by=updatedAt[DescNullsLast]&limit=10" \
  -H "Authorization: Bearer $KEY"

# Create note
curl -X POST "$BASE/rest/notes" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Call summary with Acme"}'

# Link note to company
curl -X POST "$BASE/rest/noteTargets" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"noteId":"note-uuid","companyId":"company-uuid"}'
```
