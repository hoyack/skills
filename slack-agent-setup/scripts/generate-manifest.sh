#!/bin/bash
# Generate Slack app manifest for OpenClaw agent integration

AGENT_NAME="${1:-OpenClaw Agent}"
WORKSPACE="${2:-default}"

cat <<EOF
{
  "display_information": {
    "name": "${AGENT_NAME}",
    "description": "AI agent powered by OpenClaw for ${WORKSPACE}",
    "background_color": "#2c2d30"
  },
  "features": {
    "bot_user": {
      "display_name": "${AGENT_NAME% *}",
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
EOF
