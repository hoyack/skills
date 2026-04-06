# Messaging Objects Reference

Twenty's messaging system integrates with email providers (Gmail, Microsoft 365) via connected accounts. Messages are organized in threads and channels.

## Object Hierarchy

```
ConnectedAccount
  └── MessageChannel
        └── MessageChannelMessageAssociation
              └── Message
                    ├── MessageThread
                    ├── MessageParticipant
                    └── MessageFolder
```

## Message

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `headerMessageId` | String | Email Message-ID header |
| `subject` | String | Email subject |
| `text` | String | Plain text body |
| `receivedAt` | DateTime | When message was received |
| `messageThreadId` | UUID | FK to MessageThread |
| `createdAt` | DateTime | Creation timestamp |

### Relations
- `messageThread` — MessageThread
- `messageParticipants` — MessageParticipantConnection (from, to, cc, bcc)
- `messageChannelMessageAssociations` — associations to channels

## MessageThread

Groups related messages into a conversation thread.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `createdAt` | DateTime | Creation timestamp |

### Relations
- `messages` — MessageConnection

## MessageChannel

Represents an email account/folder sync configuration.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `handle` | String | Email address |
| `type` | String | Channel type (email) |
| `isContactAutoCreationEnabled` | Boolean | Auto-create contacts |
| `contactAutoCreationType` | String | Auto-creation filter |
| `connectedAccountId` | UUID | FK to ConnectedAccount |

## MessageParticipant

Links people to messages with roles (from/to/cc/bcc).

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `role` | String | Participant role |
| `handle` | String | Email address |
| `displayName` | String | Display name |
| `messageId` | UUID | FK to Message |
| `personId` | UUID | FK to Person (if matched) |
| `workspaceMemberId` | UUID | FK to WorkspaceMember (if matched) |

## MessageFolder

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Folder name |
| `connectedAccountId` | UUID | FK to ConnectedAccount |

## GraphQL Examples

### Get email threads for a person
```graphql
query {
  getTimelineThreadsFromPersonId(personId: "person-uuid", page: 1, pageSize: 10) {
    timelineThreads {
      id
      subject
      lastMessageReceivedAt
      participantCount
      firstParticipant { displayName handle }
      lastTwoParticipants { displayName handle }
    }
    totalCount
  }
}
```

### Get threads for a company
```graphql
query {
  getTimelineThreadsFromCompanyId(companyId: "company-uuid", page: 1, pageSize: 10) {
    timelineThreads { id subject lastMessageReceivedAt }
    totalCount
  }
}
```

### List messages in a thread
```graphql
query {
  messages(filter: { messageThreadId: { eq: "thread-uuid" } }, orderBy: [{ receivedAt: { direction: AscNullsFirst } }]) {
    edges {
      node {
        id subject text receivedAt
        messageParticipants(first: 10) {
          edges { node { role handle displayName } }
        }
      }
    }
  }
}
```

### List message channels
```graphql
query {
  messageChannels(first: 10) {
    edges {
      node {
        id handle type
        isContactAutoCreationEnabled
        connectedAccount { id }
      }
    }
  }
}
```

## REST Examples

```bash
# List messages
curl "$BASE/rest/messages?limit=20&order_by=receivedAt[DescNullsLast]" \
  -H "Authorization: Bearer $KEY"

# List threads
curl "$BASE/rest/messageThreads?limit=20" -H "Authorization: Bearer $KEY"

# List message channels
curl "$BASE/rest/messageChannels" -H "Authorization: Bearer $KEY"
```
