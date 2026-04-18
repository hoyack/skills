# Mautic API Access Guide

## API Endpoints

Mautic provides a REST API at the following base URL:

```
http://192.168.1.68:8080/api/
```

## Authentication

Mautic API supports two authentication methods:

### 1. OAuth2 (Recommended for production)
### 2. Basic Auth (Easier for scripting/MCP)

## Enabling API Access

### Step 1: Enable the API in Mautic

1. Log in to Mautic: http://192.168.1.68:8080
2. Go to **Settings** (gear icon) → **Configuration**
3. Click on **API Settings** tab
4. Set **API enabled?** to **Yes**
5. Set **Enable HTTP basic auth?** to **Yes** (for Basic Auth)
6. Save & Close

### Step 2: Create API Credentials

For **Basic Auth**:
- Use your Mautic username and password directly
- No additional setup needed

For **OAuth2**:
1. Go to **Settings** → **API Credentials**
2. Click **New**
3. Select **OAuth2** as protocol
4. Enter:
   - Name: "API Access"
   - Redirect URI: http://localhost (for testing)
5. Save - you'll get Client ID and Client Secret

## API Endpoints

### Contacts (Leads)

```bash
# List contacts
GET /api/contacts

# Get specific contact
GET /api/contacts/{id}

# Create contact
POST /api/contacts/new
{
  "firstname": "John",
  "lastname": "Doe",
  "email": "john@example.com"
}

# Update contact
PATCH /api/contacts/{id}/edit

# Delete contact
DELETE /api/contacts/{id}/delete
```

### Companies

```bash
# List companies
GET /api/companies

# Create company
POST /api/companies/new
{
  "companyname": "Acme Corp",
  "companyemail": "info@acme.com"
}
```

### Segments (Lists)

```bash
# List segments
GET /api/segments

# Add contact to segment
POST /api/segments/{segmentId}/contact/{contactId}/add
```

### Campaigns

```bash
# List campaigns
GET /api/campaigns

# Add contact to campaign
POST /api/campaigns/{campaignId}/contact/{contactId}/add
```

### Emails

```bash
# List emails
GET /api/emails

# Send email to contact
POST /api/emails/{emailId}/contact/{contactId}/send
```

### Forms

```bash
# List forms
GET /api/forms

# Submit form
POST /api/forms/{formId}/submit
```

## Example API Calls

### Using Basic Auth (curl)

```bash
# Get all contacts
export MAUTIC_USER="your-mautic-username"
export MAUTIC_PASS="your-mautic-password"

curl -X GET http://192.168.1.68:8080/api/contacts \
  -u "$MAUTIC_USER:$MAUTIC_PASS" \
  -H "Content-Type: application/json"

# Create a contact
curl -X POST http://192.168.1.68:8080/api/contacts/new \
  -u "$MAUTIC_USER:$MAUTIC_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "Jane",
    "lastname": "Smith",
    "email": "jane.smith@example.com",
    "company": "Tech Corp"
  }'

# Get contact by ID
curl -X GET http://192.168.1.68:8080/api/contacts/1 \
  -u "$MAUTIC_USER:$MAUTIC_PASS" \
  -H "Content-Type: application/json"

# Update contact
curl -X PATCH http://192.168.1.68:8080/api/contacts/1/edit \
  -u "$MAUTIC_USER:$MAUTIC_PASS" \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "Jane Updated"
  }'

# Delete contact
curl -X DELETE http://192.168.1.68:8080/api/contacts/1/delete \
  -u "$MAUTIC_USER:$MAUTIC_PASS"
```

### Using Python

```python
import requests

base_url = "http://192.168.1.68:8080/api"
auth = ("username", "password")

# Get contacts
response = requests.get(f"{base_url}/contacts", auth=auth)
contacts = response.json()

# Create contact
new_contact = {
    "firstname": "John",
    "lastname": "Doe",
    "email": "john@example.com"
}
response = requests.post(
    f"{base_url}/contacts/new",
    json=new_contact,
    auth=auth
)
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

const mautic = axios.create({
  baseURL: 'http://192.168.1.68:8080/api',
  auth: {
    username: 'your-username',
    password: 'your-password'
  }
});

// Get contacts
mautic.get('/contacts')
  .then(response => console.log(response.data))
  .catch(error => console.error(error));

// Create contact
mautic.post('/contacts/new', {
  firstname: 'John',
  lastname: 'Doe',
  email: 'john@example.com'
})
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

## Response Format

All API responses are in JSON format:

```json
{
  "total": 150,
  "contacts": [
    {
      "id": 1,
      "dateAdded": "2026-04-11T10:00:00+00:00",
      "dateModified": "2026-04-11T10:00:00+00:00",
      "createdBy": 1,
      "createdByUser": "Admin User",
      "modifiedBy": null,
      "modifiedByUser": null,
      "points": 0,
      "color": null,
      "fields": {
        "core": {
          "firstname": {
            "id": 2,
            "label": "First Name",
            "type": "text",
            "value": "John"
          },
          "lastname": {
            "id": 3,
            "label": "Last Name",
            "type": "text",
            "value": "Doe"
          },
          "email": {
            "id": 6,
            "label": "Email",
            "type": "email",
            "value": "john@example.com"
          }
        }
      }
    }
  ]
}
```

## Common Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `limit` | Number of results | `?limit=100` |
| `start` | Offset for pagination | `?start=50` |
| `order` | Sort order | `?order=asc` |
| `where` | Filter conditions | `?where[0][col]=email&where[0][expr]=eq&where[0][val]=test` |
| `search` | Search query | `?search=john` |

## API Documentation

For complete API documentation:
1. Log in to Mautic
2. Go to the right sidebar menu
3. Click on **API Documentation**

Or visit: http://192.168.1.68:8080/api/docs (after enabling API)

## Rate Limiting

By default, Mautic doesn't have strict rate limiting for the API, but it's good practice to:
- Cache responses when possible
- Use batch operations for bulk updates
- Add delays between requests for large imports

## Troubleshooting

### 401 Unauthorized
- Check that API is enabled in Configuration
- Verify Basic Auth is enabled
- Ensure credentials are correct

### 403 Forbidden
- Check user permissions in Mautic
- User needs API access rights

### 404 Not Found
- Verify the endpoint URL is correct
- Check that the resource exists

### Connection Refused
- Verify Mautic container is running: `docker compose ps`
- Check port mapping: `docker compose port mautic 80`
