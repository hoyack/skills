# Get Twenty CRM API Key

The provided API key appears to be invalid (401 Unauthorized). Here's how to generate a fresh one:

## Step 1: Open Twenty CRM

Navigate to: http://localhost:3000

## Step 2: Sign In

- If you already have an account, sign in
- If not, create a new account (this will be the admin account)

## Step 3: Navigate to API Settings

1. Click on your **profile picture/avatar** (top right)
2. Select **Settings**
3. Click on **APIs & Webhooks** in the left sidebar

## Step 4: Create API Key

1. Click **"+ Create Key"** button
2. Give it a name (e.g., "Claude MCP")
3. Copy the generated API key

## Step 5: Update Configuration

Replace the API key in `~/.mcp.json`:

```bash
# Edit the file
nano ~/.mcp.json
```

Replace the `TWENTY_API_KEY` value with your new key:
```json
{
  "mcpServers": {
    "twenty-crm": {
      "command": "node",
      "args": ["/home/hoyack/.openclaw/workspace/mcp-servers/twenty-mcp/dist/index.js"],
      "env": {
        "TWENTY_BASE_URL": "http://localhost:3000",
        "TWENTY_API_KEY": "YOUR_NEW_API_KEY_HERE"
      }
    }
  }
}
```

## Step 6: Restart Claude Code

The MCP servers are loaded at startup. You need to restart Claude Code for the new API key to take effect.

## Alternative: Direct API Test

You can test your API key directly:

```bash
curl -s http://localhost:3000/rest/companies?limit=1 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

If it returns company data (or an empty list `[]`), the key is valid!

---

**Note:** The previous API key may have been invalidated if:
- The Twenty CRM container was restarted
- The database was reset
- The key was manually revoked
