# Calendar Objects Reference

Twenty integrates with Google Calendar and Microsoft Calendar via connected accounts. Calendar data is synced and linked to CRM contacts.

## CalendarEvent

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `title` | String | Event title |
| `isCanceled` | Boolean | Whether event is canceled |
| `isFullDay` | Boolean | All-day event flag |
| `startsAt` | DateTime | Event start time |
| `endsAt` | DateTime | Event end time |
| `externalCreatedAt` | DateTime | Creation time in external calendar |
| `externalUpdatedAt` | DateTime | Last update in external calendar |
| `description` | String | Event description |
| `location` | String | Event location |
| `iCalUID` | String | iCalendar UID |
| `conferenceSolution` | String | Video conference type |
| `conferenceLink` | Links | Video conference URL |
| `recurringEventExternalId` | String | Recurring series ID |
| `createdAt` | DateTime | Twenty creation timestamp |
| `updatedAt` | DateTime | Twenty update timestamp |

### Relations
- `calendarEventParticipants` — CalendarEventParticipantConnection
- `calendarChannelEventAssociations` — CalendarChannelEventAssociationConnection

## CalendarEventParticipant

Links people/members to calendar events with response status.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `calendarEventId` | UUID | FK to CalendarEvent |
| `handle` | String | Email address |
| `displayName` | String | Display name |
| `isOrganizer` | Boolean | Whether this is the organizer |
| `responseStatus` | String | ACCEPTED, DECLINED, TENTATIVE, NEEDS_ACTION |
| `personId` | UUID | FK to Person (if matched) |
| `workspaceMemberId` | UUID | FK to WorkspaceMember (if matched) |

## CalendarChannel

Configuration for a synced calendar connection.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `handle` | String | Calendar email handle |
| `syncStatus` | String | Sync state |
| `isContactAutoCreationEnabled` | Boolean | Auto-create contacts from events |
| `contactAutoCreationType` | String | Filter for auto-creation |
| `connectedAccountId` | UUID | FK to ConnectedAccount |
| `visibility` | String | Event visibility filter |

## GraphQL Examples

### Get calendar events for a person
```graphql
query {
  getTimelineCalendarEventsFromPersonId(personId: "person-uuid", page: 1, pageSize: 10) {
    timelineCalendarEvents {
      id title startsAt endsAt
      isFullDay isCanceled
      description location
      participants { handle displayName responseStatus isOrganizer }
    }
    totalCount
  }
}
```

### Get calendar events for a company
```graphql
query {
  getTimelineCalendarEventsFromCompanyId(companyId: "company-uuid", page: 1, pageSize: 10) {
    timelineCalendarEvents { id title startsAt endsAt }
    totalCount
  }
}
```

### List upcoming events
```graphql
query {
  calendarEvents(
    filter: { startsAt: { gte: "2025-04-01T00:00:00Z" } }
    orderBy: [{ startsAt: { direction: AscNullsFirst } }]
    first: 20
  ) {
    edges {
      node {
        id title startsAt endsAt location
        calendarEventParticipants(first: 10) {
          edges { node { handle displayName responseStatus isOrganizer } }
        }
      }
    }
  }
}
```

### List calendar channels
```graphql
query {
  calendarChannels(first: 10) {
    edges {
      node {
        id handle syncStatus visibility
        isContactAutoCreationEnabled
      }
    }
  }
}
```

## REST Examples

```bash
# List calendar events
curl "$BASE/rest/calendarEvents?filter=startsAt[gte]:\"2025-04-01\"&order_by=startsAt&limit=20" \
  -H "Authorization: Bearer $KEY"

# List participants for an event
curl "$BASE/rest/calendarEventParticipants?filter=calendarEventId[eq]:\"event-uuid\"" \
  -H "Authorization: Bearer $KEY"

# List calendar channels
curl "$BASE/rest/calendarChannels" -H "Authorization: Bearer $KEY"
```
