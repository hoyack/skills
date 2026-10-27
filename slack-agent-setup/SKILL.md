---
name: slack-agent-setup
description: "Automate Slack app creation and OpenClaw agent configuration for new Slack integrations."
---

# Slack Agent Setup

Sets up a new Slack app for OpenClaw agent integration and configures OpenClaw to use it.

## Workflow

### 1. Generate Slack App Manifest

Create `manifest.json` for the Slack app:

```json
{
  "display_information": {
    "name": "OpenClaw Agent",
    "description": "AI agent powered by OpenClaw",
    "background_color": "#2c2d30"
  },
  "features": {
    "bot_user": {
      "display_name": "OpenClaw",
      "always_online": false
    }
  },
  "oauth_config": {
    "scopes": {
      "bot": [
        "channels:read",
        "channels:join",
        "chat:write",
        "chat:write.public",
        "users:read",
        "users:read.email",
        "groups:read",
        "im:read",
        "mpim:read",
        "app_mentions:read"
      ]
    }
  },
  "settings": {
    "event_subscriptions": {
      "bot_events": [
        "app_mention",
        "message.channels",
        "message.groups",
        "message.im",
        "message.mpim"
      ]
    },
    "socket_mode_enabled": true,
    "interactivity": {
      "is_enabled": true
    }
  }
}
```

### 2. Create Slack App

**Option A: Automated (requires existing Slack admin token)**
```bash
curl -s -X POST https://slack.com/api/apps.manifest.create \
  -H "Authorization: Bearer $SLACK_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @manifest.json
```

**Option B: Manual**
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From manifest"
3. Paste the generated manifest JSON
4. Note the App ID and tokens

### 3. Install App & Get Tokens

After creation:
1. Navigate to **OAuth & Permissions**
2. Install to workspace
3. Copy **Bot User OAuth Token** (`xoxb-...`)
4. Navigate to **Basic Information** → **App-Level Tokens**
5. Generate token with `connections:write` scope (`xapp-1-...`)

### 4. Configure OpenClaw

Update `~/.openclaw/openclaw.json`:

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "appToken": "xapp-1-...",
      "botToken": "xoxb-...",
      "channels": {
        "CHANNEL_ID": {
          "enabled": true,
          "users": ["USER_ID_1", "USER_ID_2"]
        }
      }
    }
  }
}
```

### 5. Validate Setup

Check tokens are valid:
```bash
# Test bot token
curl -s "https://slack.com/api/auth.test" -H "Authorization: Bearer xoxb-..."

# Test app token  
curl -s "https://slack.com/api/apps.connections.open" -H "Authorization: Bearer xapp-1-..."
```

### 6. Restart Gateway

```bash
openclaw gateway restart
```

## Scripts

### Generate manifest
```bash
scripts/generate-manifest.sh <agent-name> <workspace-name>
```

### Validate tokens
```bash
scripts/validate-slack.sh <xoxb-token> <xapp-token>
```

## References

- [Slack Manifest API](references/slack-manifest-api.md)
- [OpenClaw Slack Config](references/openclaw-slack-config.md)
