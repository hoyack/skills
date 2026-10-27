# OpenClaw Slack Configuration

## Minimal Config

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "appToken": "xapp-1-...",
      "botToken": "xoxb-..."
    }
  }
}
```

## Full Config with Channel Restrictions

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "appToken": "xapp-1-TEAM-APPID-HASH",
      "botToken": "xoxb-TEAMID-USERID-HASH",
      "channels": {
        "C04H1M6CRJP": {
          "enabled": true,
          "users": ["ULN1KDFB9", "U013GSQCQF8"]
        }
      }
    }
  }
}
```

## Finding IDs

- **Channel ID**: Right-click channel → Copy link → Extract `C...` ID
- **User ID**: Click user profile → Copy member ID
- **Team ID**: Slack API `auth.test` response

## Environment Variables

Can also use env vars instead of config:
```bash
export SLACK_APP_TOKEN="xapp-1-..."
export SLACK_BOT_TOKEN="xoxb-..."
```

## Troubleshooting

### Bot not responding
1. Check tokens with `scripts/validate-slack.sh`
2. Ensure app is installed to workspace
3. Verify bot is in the channel
4. Check `users` allowlist if configured

### Socket Mode not connecting
- App token must have `connections:write` scope
- Only one connection per app token at a time
