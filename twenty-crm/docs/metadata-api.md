# Metadata API Reference

The Metadata API manages workspace schema: objects, fields, relationships, views, and configuration. It runs on a separate GraphQL endpoint at `POST {base}/metadata`.

## Authentication

Same as Core API:
```
Authorization: Bearer $TWENTY_CRM_API_KEY
```

## Key Queries

### Workspace Info
```graphql
query {
  currentWorkspace {
    id
    displayName
  }
}
```

### Current User
```graphql
query {
  currentUser {
    id
    email
    firstName
    lastName
  }
}
```

### List All Objects
```graphql
query {
  objects(paging: { first: 100 }) {
    edges {
      node {
        id
        nameSingular
        namePlural
        labelSingular
        labelPlural
        isCustom
        isActive
        fields(paging: { first: 100 }) {
          edges {
            node {
              id
              name
              label
              type
              isCustom
              isActive
              isNullable
              defaultValue
            }
          }
        }
      }
    }
  }
}
```

### Get Specific Object Schema
```graphql
query {
  object(id: "object-uuid") {
    id
    nameSingular
    namePlural
    fields(paging: { first: 100 }) {
      edges { node { id name label type } }
    }
  }
}
```

### List Views
```graphql
query {
  getViews {
    id name objectMetadataId type
  }
}
```

### List API Keys
```graphql
query {
  apiKeys(paging: { first: 50 }) {
    edges {
      node { id name expiresAt revokedAt }
    }
  }
}
```

### System Health
```graphql
query {
  getSystemHealthStatus {
    services { name status message }
  }
}
```

### Version Info
```graphql
query {
  versionInfo {
    current
    latest
  }
}
```

## Key Mutations

### Create Custom Object
```graphql
mutation {
  createOneObject(input: {
    object: {
      nameSingular: "project"
      namePlural: "projects"
      labelSingular: "Project"
      labelPlural: "Projects"
      description: "Custom project tracking"
      icon: "IconFolder"
    }
  }) {
    id nameSingular namePlural
  }
}
```

### Add Custom Field
```graphql
mutation {
  createOneField(input: {
    field: {
      objectMetadataId: "object-uuid"
      name: "priority"
      label: "Priority"
      type: TEXT
      description: "Priority level"
      icon: "IconFlag"
    }
  }) {
    id name label type
  }
}
```

### Update Object
```graphql
mutation {
  updateOneObject(input: {
    id: "object-uuid"
    update: {
      labelSingular: "Updated Label"
      description: "Updated description"
    }
  }) {
    id labelSingular
  }
}
```

### Delete Object
```graphql
mutation {
  deleteOneObject(input: { id: "object-uuid" }) {
    id
  }
}
```

### Update Field
```graphql
mutation {
  updateOneField(input: {
    id: "field-uuid"
    update: {
      label: "New Label"
      isActive: false
    }
  }) {
    id label isActive
  }
}
```

### API Key Management
```graphql
# Create API key
mutation {
  createApiKey(input: { name: "Integration Key", expiresAt: "2026-01-01T00:00:00Z" }) {
    token
    apiKey { id name expiresAt }
  }
}

# Revoke API key
mutation {
  revokeApiKey(input: { id: "key-uuid" }) {
    id revokedAt
  }
}
```

### Webhooks
```graphql
# Create webhook
mutation {
  createOneWebhook(input: {
    webhook: {
      targetUrl: "https://example.com/webhook"
      description: "CRM events"
    }
  }) {
    id targetUrl
  }
}

# List webhooks
query {
  webhooks {
    id targetUrl description
  }
}
```

## REST Metadata Endpoints

```bash
# List all object definitions
curl "$BASE/rest/metadata/objects" -H "Authorization: Bearer $KEY"

# Get specific object definition
curl "$BASE/rest/metadata/objects/person" -H "Authorization: Bearer $KEY"

# Create custom object (POST)
curl -X POST "$BASE/rest/metadata/objects" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"nameSingular":"project","namePlural":"projects","labelSingular":"Project","labelPlural":"Projects"}'
```

## Field Types

When creating custom fields, use these type values:

| Type | Description |
|------|-------------|
| `TEXT` | Plain text string |
| `NUMBER` | Numeric value |
| `BOOLEAN` | True/false |
| `DATE_TIME` | Date and time |
| `DATE` | Date only |
| `LINK` | URL link |
| `LINKS` | Multiple links (composite) |
| `CURRENCY` | Money amount (composite) |
| `EMAIL` | Email address |
| `EMAILS` | Multiple emails (composite) |
| `PHONE` | Phone number |
| `PHONES` | Multiple phones (composite) |
| `FULL_NAME` | First + last name (composite) |
| `ADDRESS` | Postal address (composite) |
| `RATING` | Star rating |
| `SELECT` | Single select dropdown |
| `MULTI_SELECT` | Multi select |
| `RELATION` | Relationship to another object |
| `RICH_TEXT` | Rich text content |
| `RAW_JSON` | Raw JSON data |
| `UUID` | UUID identifier |
| `POSITION` | Sort position float |
| `ACTOR` | Actor reference (composite) |
| `TS_VECTOR` | Full-text search vector |
