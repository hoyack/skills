# Slack Manifest API Reference

## Required Scopes for OpenClaw

### Bot Token Scopes (`xoxb-...`)

| Scope | Required | Purpose |
|-------|----------|---------|
| `channels:read` | ✅ | List channels and get info |
| `channels:join` | ✅ | Join public channels |
| `chat:write` | ✅ | Send messages |
| `chat:write.public` | ✅ | Send messages to channels without joining |
| `users:read` | ✅ | Get user info for mentions |
| `users:read.email` | Optional | Match by email |
| `groups:read` | Optional | Access private channels |
| `im:read` | Optional | Access DMs |
| `mpim:read` | Optional | Access group DMs |
| `app_mentions:read` | Optional | Receive app mention events |

### App Token Scopes (`xapp-1-...`)

| Scope | Required | Purpose |
|-------|----------|---------|
| `connections:write` | ✅ | Socket Mode connections |

## Manifest Schema

Key fields for OpenClaw compatibility:
- `features.bot_user` - Required for the bot to appear in Slack
- `oauth_config.scopes.bot` - Defines what the bot can do
- `settings.socket_mode_enabled` - Must be `true` for OpenClaw
- `settings.event_subscriptions.bot_events` - Events to receive

## API Endpoints

### Create App from Manifest
```
POST https://slack.com/api/apps.manifest.create
Authorization: Bearer xoxe-... (admin token)
Content-Type: application/json

{"manifest": {...}}
```

### Validate Tokens
```
POST https://slack.com/api/auth.test
Authorization: Bearer xoxb-...
```
