#!/bin/bash
# Validate Slack tokens for OpenClaw integration

XOXB_TOKEN="$1"
XAPP_TOKEN="$2"

if [ -z "$XOXB_TOKEN" ] || [ -z "$XAPP_TOKEN" ]; then
  echo "Usage: $0 <xoxb-token> <xapp-token>"
  exit 1
fi

echo "=== Validating Bot Token (xoxb-...) ==="
BOT_TEST=$(curl -s -X POST "https://slack.com/api/auth.test" \
  -H "Authorization: Bearer ${XOXB_TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded")

if echo "$BOT_TEST" | grep -q '"ok":true'; then
  echo "✅ Bot token valid"
  echo "$BOT_TEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  Team: {d.get('team', 'N/A')}\"); print(f\"  Bot: {d.get('user', 'N/A')}\")"
else
  echo "❌ Bot token invalid"
  echo "$BOT_TEST" | python3 -m json.tool 2>/dev/null || echo "$BOT_TEST"
fi

echo ""
echo "=== Validating App Token (xapp-1-...) ==="
APP_TEST=$(curl -s -X GET "https://slack.com/api/apps.connections.open" \
  -H "Authorization: Bearer ${XAPP_TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded")

if echo "$APP_TEST" | grep -q '"ok":true'; then
  echo "✅ App token valid (Socket Mode)"
else
  echo "❌ App token invalid or missing connections:write scope"
  echo "$APP_TEST" | python3 -m json.tool 2>/dev/null || echo "$APP_TEST"
fi

echo ""
echo "=== Checking Bot Scopes ==="
SCOPES=$(curl -s -X POST "https://slack.com/api/oauth.v2.access" \
  -H "Authorization: Bearer ${XOXB_TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=${XOXB_TOKEN}")

echo "$SCOPES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'scope' in d:
  scopes = d['scope'].split(',')
  print('Granted scopes:')
  for s in scopes:
    print(f\"  - {s.strip()}\")
else:
  print('Could not retrieve scopes')
"

echo ""
echo "=== Testing Channel Access ==="
CHANNELS=$(curl -s -X POST "https://slack.com/api/conversations.list" \
  -H "Authorization: Bearer ${XOXB_TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "types=public_channel,private_channel")

if echo "$CHANNELS" | grep -q '"ok":true'; then
  COUNT=$(echo "$CHANNELS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('channels', [])))")
  echo "✅ Can access ${COUNT} channels"
else
  echo "❌ Cannot list channels"
  echo "$CHANNELS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error', 'Unknown error'))"
fi
