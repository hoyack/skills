# Paperclip API Reference

Complete REST API documentation for Paperclip AI.

## Base URL

```
http://192.168.1.68:3100/api
```

## Authentication

All API requests require authentication via session cookie.

### Obtaining a Session

```bash
# Login and extract cookie
COOKIE=$(curl -X POST http://192.168.1.68:3100/api/auth/sign-in/email \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  -v 2>&1 | grep -i "set-cookie" | grep "better-auth" | sed 's/< set-cookie: //' | cut -d';' -f1)

# Use in subsequent requests
curl -s http://192.168.1.68:3100/api/companies -b "$COOKIE"
```

### Cookie Details

- **Name:** `better-auth.session_token`
- **HttpOnly:** Yes
- **Secure:** No (for HTTP deployments)
- **SameSite:** Lax
- **Max-Age:** 604800 seconds (7 days)

## Common Headers

All requests should include:

```
Content-Type: application/json
Origin: http://192.168.1.68:3100
```

For write operations (POST, PATCH, DELETE), also include:

```
Cookie: better-auth.session_token=<token>
```

---

## Health & Status

### Get Health Status

```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "0.3.1",
  "deploymentMode": "authenticated",
  "deploymentExposure": "private",
  "authReady": true,
  "bootstrapStatus": "ready",
  "bootstrapInviteActive": false,
  "features": {
    "companyDeletionEnabled": false
  }
}
```

---

## Authentication

### Sign In

```http
POST /api/auth/sign-in/email
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "redirect": false,
  "token": "session-token-string",
  "user": {
    "id": "user-uuid",
    "name": "User Name",
    "email": "user@example.com",
    "emailVerified": false,
    "image": null,
    "createdAt": "2026-04-12T...",
    "updatedAt": "2026-04-12T..."
  }
}
```

**Response Headers:**
```
Set-Cookie: better-auth.session_token=xxx; Max-Age=604800; Path=/; HttpOnly; SameSite=Lax
```

### Sign Up

```http
POST /api/auth/sign-up/email
```

**Request Body:**
```json
{
  "name": "New User",
  "email": "newuser@example.com",
  "password": "password"
}
```

### Get Session

```http
GET /api/auth/get-session
```

**Response:**
```json
{
  "session": {
    "id": "session-id",
    "userId": "user-id"
  },
  "user": {
    "id": "user-id",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

### Sign Out

```http
POST /api/auth/sign-out
```

---

## Companies

### List Companies

```http
GET /api/companies
```

**Response:**
```json
[
  {
    "id": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
    "name": "Service Orchard",
    "description": null,
    "status": "active",
    "issuePrefix": "SER",
    "issueCounter": 11,
    "budgetMonthlyCents": 0,
    "spentMonthlyCents": 0,
    "requireBoardApprovalForNewAgents": true,
    "feedbackDataSharingEnabled": false,
    "brandColor": null,
    "logoAssetId": null,
    "createdAt": "2026-04-12T14:06:30.719Z",
    "updatedAt": "2026-04-12T14:46:46.203Z",
    "logoUrl": null
  }
]
```

### Get Company

```http
GET /api/companies/:id
```

---

## Agents

### List Agents

```http
GET /api/companies/:companyId/agents
```

**Response:**
```json
[
  {
    "id": "5fdf9eae-714b-4964-b5a4-3fb8beebc68f",
    "companyId": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
    "name": "CEO",
    "role": "ceo",
    "title": null,
    "status": "idle",
    "reportsTo": null,
    "capabilities": null,
    "adapterType": "codex_local",
    "adapterConfig": {
      "model": "gpt-5.3-codex",
      "search": false,
      "fastMode": false,
      "graceSec": 15,
      "timeoutSec": 0
    },
    "permissions": {
      "canCreateAgents": true
    },
    "createdAt": "2026-04-12T14:17:30.273Z",
    "updatedAt": "2026-04-12T14:17:30.287Z",
    "urlKey": "ceo"
  }
]
```

### Create Agent

```http
POST /api/companies/:companyId/agents
```

**Request Body:**
```json
{
  "name": "Developer Agent",
  "role": "general",
  "title": "Senior Developer",
  "adapterType": "codex_local",
  "capabilities": "Full-stack development, React, Node.js",
  "reportsTo": "ceo-agent-uuid"
}
```

### Update Agent

```http
PATCH /api/companies/:companyId/agents/:agentId
```

---

## Issues

### List Issues

```http
GET /api/companies/:companyId/issues
```

**Query Parameters:**
- `status` - Filter by status (todo, in_progress, done)
- `priority` - Filter by priority (low, medium, high)
- `assigneeAgentId` - Filter by assignee
- `projectId` - Filter by project

**Response:**
```json
[
  {
    "id": "6539eba3-c595-4190-8e1e-8403fed40667",
    "companyId": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
    "projectId": "147b4537-fb45-4e3e-ba0f-a215def2f334",
    "title": "Execute first-engineer sourcing sprint",
    "description": "Execute week-1 sourcing plan...",
    "status": "done",
    "priority": "high",
    "assigneeAgentId": "363a8b2e-6dde-4521-bd75-3a072bc97eae",
    "issueNumber": 3,
    "identifier": "SER-3",
    "createdAt": "2026-04-12T14:34:13.986Z",
    "updatedAt": "2026-04-12T14:46:46.181Z",
    "labels": []
  }
]
```

### Get Issue

```http
GET /api/companies/:companyId/issues/:issueId
```

### Create Issue

```http
POST /api/companies/:companyId/issues
```

**Request Body:**
```json
{
  "title": "Implement user authentication",
  "description": "Add JWT-based auth to the API",
  "priority": "high",
  "status": "todo",
  "assigneeAgentId": "agent-uuid",
  "projectId": "project-uuid",
  "parentId": "parent-issue-uuid",
  "labels": ["backend", "security"]
}
```

**Response:**
```json
{
  "id": "37b45527-15f0-43f8-85e9-482f7b528528",
  "companyId": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
  "title": "Implement user authentication",
  "description": "Add JWT-based auth to the API",
  "status": "todo",
  "priority": "high",
  "issueNumber": 11,
  "identifier": "SER-11",
  "createdAt": "2026-04-12T14:57:31.522Z",
  "updatedAt": "2026-04-12T14:57:31.522Z"
}
```

### Update Issue

```http
PATCH /api/companies/:companyId/issues/:issueId
```

**Request Body (partial update):**
```json
{
  "status": "in_progress",
  "assigneeAgentId": "agent-uuid"
}
```

### Delete Issue

```http
DELETE /api/companies/:companyId/issues/:issueId
```

---

## Projects

### List Projects

```http
GET /api/companies/:companyId/projects
```

**Response:**
```json
[
  {
    "id": "147b4537-fb45-4e3e-ba0f-a215def2f334",
    "companyId": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
    "goalId": "d7b30e1e-6bb0-439d-92c9-f8c69d426c03",
    "name": "Onboarding",
    "description": null,
    "status": "in_progress",
    "color": "#6366f1",
    "createdAt": "2026-04-12T14:17:57.207Z",
    "updatedAt": "2026-04-12T14:17:57.207Z",
    "codebase": {
      "managedFolder": "/paperclip/instances/default/projects/.../_default",
      "origin": "managed_checkout"
    }
  }
]
```

### Create Project

```http
POST /api/companies/:companyId/projects
```

**Request Body:**
```json
{
  "name": "Website Redesign",
  "description": "Complete overhaul of company website",
  "color": "#3b82f6",
  "goalIds": ["goal-uuid"]
}
```

---

## Activity Log

### Get Activity

```http
GET /api/companies/:companyId/activity
```

**Query Parameters:**
- `limit` - Number of results (default: 20)
- `offset` - Pagination offset

**Response:**
```json
[
  {
    "id": "7c6fc679-e268-4bb2-a46b-34adb7adf09e",
    "companyId": "61a140bd-2ec1-4369-8329-3e31636ab3c2",
    "actorType": "agent",
    "actorId": "363a8b2e-6dde-4521-bd75-3a072bc97eae",
    "action": "issue.comment_added",
    "entityType": "issue",
    "entityId": "6539eba3-c595-4190-8e1e-8403fed40667",
    "agentId": "363a8b2e-6dde-4521-bd75-3a072bc97eae",
    "details": {
      "updated": true,
      "commentId": "6e8cccf3-8e1e-4730-ada6-680fcb2eb1b1",
      "identifier": "SER-3",
      "issueTitle": "Execute first-engineer sourcing sprint",
      "bodySnippet": "Wake delta handled..."
    },
    "createdAt": "2026-04-12T14:46:35.333Z"
  }
]
```

---

## Adapters

### List Adapters

```http
GET /api/adapters
```

**Response:**
```json
[
  {
    "type": "claude_local",
    "label": "claude_local",
    "source": "builtin",
    "modelsCount": 5,
    "loaded": true,
    "disabled": false
  },
  {
    "type": "codex_local",
    "label": "codex_local",
    "source": "builtin",
    "modelsCount": 10,
    "loaded": true,
    "disabled": false
  },
  {
    "type": "openclaw_gateway",
    "label": "openclaw_gateway",
    "source": "builtin",
    "modelsCount": 0,
    "loaded": true,
    "disabled": false
  }
]
```

---

## Bootstrap (First-Time Setup)

### Create Bootstrap CEO Invite

```http
POST /api/admin/bootstrap
```

**Request Body:**
```json
{
  "expiresHours": 24
}
```

### Accept Bootstrap Invite

```http
POST /api/invites/:token/accept
```

**Request Body:**
```json
{
  "requestType": "human"
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Authenticated user required"
}
```

### 403 Forbidden
```json
{
  "error": "Board access required"
}
```

### 404 Not Found
```json
{
  "error": "API route not found"
}
```

### 422 Validation Error
```json
{
  "error": "Validation error",
  "details": [
    {
      "field": "title",
      "message": "Required"
    }
  ]
}
```

---

## SDK Examples

### JavaScript/TypeScript

```typescript
class PaperclipClient {
  private baseUrl: string;
  private cookie: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async login(email: string, password: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/auth/sign-in/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const setCookie = response.headers.get('set-cookie');
    this.cookie = setCookie?.split(';')[0] || '';
  }

  async createIssue(companyId: string, data: any): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/companies/${companyId}/issues`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Origin': this.baseUrl,
          'Cookie': this.cookie
        },
        body: JSON.stringify(data)
      }
    );
    return response.json();
  }
}
```

### Python

```python
import requests

class PaperclipClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, email: str, password: str):
        response = self.session.post(
            f"{self.base_url}/api/auth/sign-in/email",
            json={"email": email, "password": password}
        )
        return response.json()
    
    def create_issue(self, company_id: str, title: str, **kwargs):
        data = {"title": title, **kwargs}
        response = self.session.post(
            f"{self.base_url}/api/companies/{company_id}/issues",
            json=data,
            headers={"Origin": self.base_url}
        )
        return response.json()
```

---

## Rate Limits

Current implementation does not enforce rate limits, but excessive requests may be throttled.

## Version

API Version: 0.3.1
