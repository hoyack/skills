# Task Object Reference

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | auto | Unique identifier |
| `createdAt` | DateTime | auto | Creation timestamp |
| `updatedAt` | DateTime | auto | Last update timestamp |
| `deletedAt` | DateTime | — | Soft-delete timestamp |
| `title` | String | — | Task title |
| `bodyV2` | RichText | — | Rich text body content |
| `dueAt` | DateTime | — | Due date |
| `status` | TaskStatusEnum | — | Task status |
| `position` | Float | auto | Sort position |
| `assigneeId` | UUID | — | FK to WorkspaceMember |
| `createdBy` | Actor | auto | Creation actor |
| `updatedBy` | Actor | auto | Last update actor |
| `searchVector` | TSVector | auto | Full-text search index |

## TaskStatusEnum

| Value | Description |
|-------|-------------|
| `TODO` | Not started |
| `IN_PROGRESS` | Currently being worked on |
| `DONE` | Completed |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `assignee` | WorkspaceMember | Assigned workspace member |
| `taskTargets` | TaskTargetConnection | Polymorphic links to Person/Company/Opportunity |
| `attachments` | AttachmentConnection | File attachments |
| `favorites` | FavoriteConnection | Favorited by members |
| `timelineActivities` | TimelineActivityConnection | Activity timeline |

## Task Targets

Tasks use a polymorphic linking pattern via `TaskTarget`. A task can be linked to multiple people, companies, or opportunities.

```graphql
# Link task to a person
mutation {
  createTaskTarget(data: {
    taskId: "task-uuid"
    personId: "person-uuid"
  }) { id }
}

# Link task to a company
mutation {
  createTaskTarget(data: {
    taskId: "task-uuid"
    companyId: "company-uuid"
  }) { id }
}
```

## GraphQL Examples

### List open tasks
```graphql
query {
  tasks(
    filter: { status: { in: ["TODO", "IN_PROGRESS"] } }
    orderBy: [{ dueAt: { direction: AscNullsLast } }]
    first: 20
  ) {
    edges {
      node {
        id title status dueAt
        assignee { name { firstName lastName } }
        taskTargets(first: 5) {
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

### Create task with target
```graphql
mutation {
  createTask(data: {
    title: "Follow up on proposal"
    status: TODO
    dueAt: "2025-04-15T09:00:00.000Z"
    assigneeId: "member-uuid"
  }) {
    id title status
  }
}
```

### Update task status
```graphql
mutation {
  updateTask(id: "task-uuid", data: { status: DONE }) {
    id title status
  }
}
```

### Overdue tasks
```graphql
query {
  tasks(filter: {
    and: [
      { status: { neq: "DONE" } }
      { dueAt: { lt: "2025-04-05T00:00:00Z" } }
    ]
  }) {
    edges { node { id title dueAt status assignee { name { firstName lastName } } } }
  }
}
```

## REST Examples

```bash
# List TODO tasks
curl "$BASE/rest/tasks?filter=status[eq]:\"TODO\"&order_by=dueAt[AscNullsLast]" \
  -H "Authorization: Bearer $KEY"

# Create
curl -X POST "$BASE/rest/tasks" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Call client","status":"TODO","dueAt":"2025-04-15T09:00:00Z"}'

# Mark done
curl -X PATCH "$BASE/rest/tasks/{id}" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"status":"DONE"}'
```
