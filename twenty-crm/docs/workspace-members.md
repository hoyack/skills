# WorkspaceMember Object Reference

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `createdAt` | DateTime | auto | Creation timestamp |
| `updatedAt` | DateTime | auto | Last update timestamp |
| `deletedAt` | DateTime | — | Soft-delete timestamp |
| `name` | FullName | yes | `{ firstName, lastName }` |
| `userEmail` | String | — | User's email address |
| `avatarUrl` | String | — | Avatar image URL |
| `colorScheme` | String | yes | UI color scheme preference |
| `locale` | String | yes | Locale code (e.g., "en") |
| `timeZone` | String | yes | Timezone (e.g., "America/Chicago") |
| `calendarStartDay` | Int | yes | Calendar week start day |
| `userId` | UUID | yes | FK to auth user |
| `dateFormat` | WorkspaceMemberDateFormatEnum | yes | Date display format |
| `timeFormat` | WorkspaceMemberTimeFormatEnum | yes | Time display format |
| `numberFormat` | WorkspaceMemberNumberFormatEnum | yes | Number display format |
| `position` | Float | auto | Sort position |
| `createdBy` | Actor | auto | Creation actor |
| `updatedBy` | Actor | auto | Last update actor |
| `searchVector` | TSVector | auto | Full-text search index |

## Enums

### WorkspaceMemberDateFormatEnum
`SYSTEM`, `MONTH_FIRST`, `DAY_FIRST`, `YEAR_FIRST`

### WorkspaceMemberTimeFormatEnum
`SYSTEM`, `HOUR_24`, `HOUR_12`

### WorkspaceMemberNumberFormatEnum
`SYSTEM`, `COMMAS_AND_DOT`, `SPACES_AND_COMMA`, `DOTS_AND_COMMA`, `APOSTROPHE_AND_DOT`

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `accountOwnerForCompanies` | CompanyConnection | Companies this member owns |
| `ownedOpportunities` | OpportunityConnection | Opportunities this member owns |
| `assignedTasks` | TaskConnection | Tasks assigned to this member |
| `connectedAccounts` | ConnectedAccountConnection | OAuth-connected accounts |
| `favorites` | FavoriteConnection | Member's favorites |
| `blocklist` | BlocklistConnection | Member's blocklist |
| `calendarEventParticipants` | CalendarEventParticipantConnection | Calendar participations |
| `messageParticipants` | MessageParticipantConnection | Message participations |
| `timelineActivities` | TimelineActivityConnection | Activity timeline |

## GraphQL Examples

### List workspace members
```graphql
query {
  workspaceMembers(first: 50) {
    edges {
      node {
        id
        name { firstName lastName }
        userEmail
        locale timeZone
        accountOwnerForCompanies(first: 5) {
          edges { node { id name } }
        }
        assignedTasks(first: 5, filter: { status: { neq: "DONE" } }) {
          edges { node { id title status dueAt } }
        }
      }
    }
  }
}
```

### Get current workspace info (via metadata)
```graphql
# POST to /metadata
query {
  currentWorkspace { id displayName }
  currentUser { id email }
}
```

## REST Examples

```bash
# List members
curl "$BASE/rest/workspaceMembers" -H "Authorization: Bearer $KEY"

# Get specific member
curl "$BASE/rest/workspaceMembers/{id}" -H "Authorization: Bearer $KEY"
```
