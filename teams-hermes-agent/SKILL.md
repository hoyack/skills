---
name: teams-hermes-agent
description: Set up a Microsoft Teams/Microsoft 365 Teams SDK bot that bridges Teams chat to a Nous Research Hermes Agent HTTP API.
---

# Teams Hermes Agent

Use this skill when asked to connect a Nous Research Hermes Agent to Microsoft Teams or Microsoft 365 Teams chat.

## Default Path

Prefer the current Microsoft Teams SDK and Teams Developer CLI path:

1. Use Node.js 20+.
2. Use `@microsoft/teams.cli@preview` for registration, app manifest, credentials, and sideload link.
3. Use the Teams SDK TypeScript message-handler pattern for the bot runtime.
4. Bridge each incoming Teams message to the Hermes Agent OpenAI-compatible API, normally:
   `POST ${HERMES_BASE_URL}/v1/chat/completions`
5. Use Bot Framework SDK only as a legacy fallback for existing Bot Framework tenants, because Microsoft says the Bot Framework SDK GitHub project is archived and no longer maintained.

Read `references/microsoft-teams-sources.md` before making architecture decisions, tenant-registration choices, or claims about current Microsoft guidance.

## Security Rules

- Never commit Teams client secrets, Hermes API keys, tenant IDs if the user treats them as sensitive, `.env`, app packages containing secrets, or generated credentials.
- Use `.env.example` for placeholders only.
- Keep Hermes behind loopback or private network when possible. Expose only the Teams bridge over public HTTPS.
- Validate Teams can reach the bridge through HTTPS before registering the app.
- Treat Teams message content as untrusted input before sending it to Hermes.
- Add AI transparency labels, citations, and feedback handling when responses are AI-generated and the tenant UX needs production readiness.

## Battle-Tested Setup Workflow

1. Confirm prerequisites:

```bash
node --version
npm --version
npm install -g @microsoft/teams.cli@preview
teams --version
teams login
teams status
```

`teams status` must show sideloading/custom app upload enabled. If not, stop and ask the tenant admin to enable custom app upload.

2. Confirm Hermes health without exposing secrets:

```bash
curl -sS "${HERMES_BASE_URL:-http://127.0.0.1:8643}/health"
```

If Hermes requires an API key, load it from `HERMES_API_KEY` and do not print it.

3. Scaffold a bridge project:

```bash
skills/teams-hermes-agent/scripts/create-teams-hermes-bridge.sh ./teams-hermes-bridge
cd ./teams-hermes-bridge
cp .env.example .env
```

Fill `.env` locally:

```dotenv
PORT=3978
HERMES_BASE_URL=http://127.0.0.1:8643
HERMES_API_KEY=...
HERMES_MODEL=glm-5.2:cloud
```

4. Start a public HTTPS tunnel to the bridge port:

```bash
devtunnel host -p 3978 --allow-anonymous
# or
ngrok http 3978
```

5. Register the Teams app from the bridge project directory:

```bash
teams app create \
  --name hermes-agent \
  --endpoint https://<tunnel-host>/api/messages \
  --env .env
```

The CLI writes Teams credentials to `.env` and prints the Teams App ID plus install link.

6. Run and install:

```bash
npm install
npm run dev
teams app get <teamsAppId> --install-link
```

Open the install link in a browser signed in to Teams, add the app, and send a test message.

7. Verify:

- Teams receives a reply for a simple prompt.
- The bridge logs show an inbound Teams activity and one Hermes API call.
- Wrong or missing `HERMES_API_KEY` returns a controlled bridge error, not a stack trace to Teams.
- Teams registration endpoint exactly matches the public tunnel URL plus `/api/messages`.

## Production Hardening

- Replace the tunnel with a stable HTTPS endpoint before production.
- Store Teams and Hermes secrets in the deployment secret manager, not repo files.
- Add request logging with redaction for Teams activity IDs, conversation IDs, and Hermes errors.
- Persist conversation references only if proactive messaging is required.
- For proactive messages, store `tenantId` plus `userId`, `channelId`, or `teamId`; do not try to send proactive Teams messages by email or UPN.
- Use one Teams channel/app registration per environment. Do not delete and recreate channel registrations casually because it invalidates stored Teams IDs.
- Add AI label and feedback-loop support for production AI output.

## Common Failure Modes

- `teams status` shows sideloading disabled: tenant admin must enable custom app upload.
- Teams cannot reach local server: the tunnel is missing, wrong, expired, or endpoint path is not `/api/messages`.
- Teams bot installs but does not answer: app credentials in `.env` do not match the registered app, or the server is not running on `PORT`.
- Hermes returns `401`: `HERMES_API_KEY` is absent or wrong.
- Proactive message returns `403`: bot is not installed for that scope, or the user blocked/uninstalled it.
- Bot Framework guidance conflicts with Teams SDK guidance: prefer Teams SDK for new Teams agents unless maintaining an existing Bot Framework app.

