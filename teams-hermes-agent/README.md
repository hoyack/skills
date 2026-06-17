# Teams Hermes Agent Skill

This skill helps an operator build and deploy a Microsoft Teams / Microsoft 365 Teams SDK bot that routes Teams chat messages to a Nous Research Hermes Agent.

The recommended pattern is deliberately boring:

```text
Teams user
  -> Microsoft Teams service
  -> public HTTPS /api/messages endpoint
  -> small TypeScript Teams SDK bridge
  -> private Hermes Agent HTTP API
```

Keep Hermes private. Expose only the bridge to Teams. The bridge owns Teams credentials, input cleanup, error handling, logging, and production policy. Hermes remains the agent backend.

## Why This Path

Microsoft's current Teams SDK documentation points new Teams agents toward the Teams SDK and Teams Developer CLI. The older Bot Framework path still exists, but Microsoft now notes that the Bot Framework SDK and Bot Framework Emulator GitHub repositories are archived and no longer maintained. For a fresh Teams/Hermes integration, the Teams SDK path is the lower-friction and more future-facing choice.

Use Bot Framework only when you are maintaining an existing Bot Framework/Azure Bot Service implementation or when the tenant already has a hard requirement for that process.

## Repository Contents

```text
teams-hermes-agent/
├── SKILL.md
├── README.md
├── references/
│   └── microsoft-teams-sources.md
└── scripts/
    └── create-teams-hermes-bridge.sh
```

`SKILL.md` is the lean operational instruction file for agents. This README is the human-facing deployment and setup guide. `references/microsoft-teams-sources.md` captures the Microsoft docs used to make the design choices. The scaffold script creates a minimal TypeScript Teams SDK bridge that calls Hermes through an OpenAI-compatible `/v1/chat/completions` endpoint.

## Official How-To References

Start with these Microsoft docs:

- Teams SDK welcome: <https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/welcome>
- Teams SDK quickstart: <https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/getting-started/quickstart>
- Register a Teams app with Teams Developer CLI: <https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/get-started/quickstart-register>
- Build your first Teams SDK bot: <https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/get-started/quickstart-build>
- Run Teams SDK apps in Teams: <https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/getting-started/running-in-teams/overview>
- Create and host a Microsoft Dev Tunnel: <https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started>
- Dev Tunnels CLI reference: <https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/cli-commands>
- Build a bot for Teams: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/build-a-bot>
- Bot Framework SDK overview and maintenance status: <https://learn.microsoft.com/en-us/azure/bot-service/bot-service-overview?view=azure-bot-service-4.0>
- Connect an Azure/Bot Framework bot to Teams: <https://learn.microsoft.com/en-us/azure/bot-service/channel-connect-teams?view=azure-bot-service-4.0>
- Send proactive Teams bot messages: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/conversations/send-proactive-messages>
- Add AI labels, citations, feedback, and sensitivity metadata: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content>
- Format bot messages in Teams: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/format-your-bot-messages>
- Stream bot messages in Teams: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/streaming-ux>
- Teams conversational AI UX best practices: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/teams-conversational-ai/ai-ux>
- Microsoft 365 Agents Toolkit project creation: <https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/create-new-project>

## Prerequisites

You need:

- A Microsoft 365 tenant where you can sign in and upload custom Teams apps.
- Teams custom app upload / sideloading enabled for your account or test policy.
- Node.js 20 or newer.
- npm.
- Teams Developer CLI preview package.
- A public HTTPS tunnel for local development, such as Microsoft Dev Tunnels or ngrok.
- A running Hermes Agent with HTTP API enabled.
- The Hermes API key, loaded from an environment variable or secret manager.

Install the Teams CLI:

```bash
npm install -g @microsoft/teams.cli@preview
teams --version
teams login
teams status
```

`teams status` must show that your account and tenant can create or sideload Teams apps. If tenant app upload is disabled, stop and ask the Microsoft 365 administrator to enable custom app upload for the relevant policy.

## Hermes API Assumptions

The bridge expects Hermes to behave like an OpenAI-compatible chat-completions API:

```text
GET  /health
POST /v1/chat/completions
Authorization: Bearer <HERMES_API_KEY>
```

Known local Docker Hermes deployment pattern:

```bash
curl -sS http://127.0.0.1:8643/health
```

Expected health style:

```json
{"status":"ok","platform":"hermes-agent","version":"0.16.0"}
```

Do not expose Hermes directly to the internet just to make Teams work. The bridge should be the public endpoint. Hermes should remain loopback-only, private-LAN-only, or reachable through an internal service network.

## Local Development: Fast Path

From the public `hoyack/skills` repo:

```bash
git clone git@github.com:hoyack/skills.git
cd skills/teams-hermes-agent
./scripts/create-teams-hermes-bridge.sh ~/work/teams-hermes-bridge
cd ~/work/teams-hermes-bridge
cp .env.example .env
```

Edit `.env`:

```dotenv
PORT=3978

# The Teams CLI writes these during registration.
CLIENT_ID=
CLIENT_SECRET=
TENANT_ID=

HERMES_BASE_URL=http://127.0.0.1:8643
HERMES_API_KEY=replace-with-local-secret
HERMES_MODEL=glm-5.2:cloud
HERMES_SYSTEM_PROMPT=You are a helpful Hermes Agent inside Microsoft Teams. Be concise, accurate, and transparent when unsure.
```

Install dependencies:

```bash
npm install
npm run typecheck
```

Start the bridge:

```bash
npm run dev
```

You should see the Teams SDK process listening on port `3978`.

## Create a Public HTTPS Tunnel

Teams cannot call `localhost`. Use a public HTTPS tunnel during local development.

With Microsoft Dev Tunnels:

```bash
devtunnel user login
devtunnel create teams-hermes
devtunnel port create teams-hermes -p 3978
devtunnel host teams-hermes --allow-anonymous
```

Or with a short-lived anonymous tunnel:

```bash
devtunnel host -p 3978 --allow-anonymous
```

With ngrok:

```bash
ngrok http 3978
```

Save the HTTPS hostname. Your Teams endpoint will be:

```text
https://<tunnel-host>/api/messages
```

If the tunnel URL changes, update the Teams app registration or create a new dev registration. For less churn, use a named Dev Tunnel or a reserved ngrok domain.

## Register the Teams App

Run this from the generated bridge project directory:

```bash
teams app create \
  --name hermes-agent \
  --endpoint https://<tunnel-host>/api/messages \
  --env .env
```

The CLI creates/registers the Teams app and writes the needed credentials to `.env`. It also prints a Teams App ID and install link.

If you need the install link later:

```bash
teams app list
teams app get <teamsAppId> --install-link
```

Open the install link in a browser signed in to Teams and select Add.

## First Conversation Test

In Teams, send:

```text
hello
```

Then try:

```text
summarize what you are and what model/backend you are using
```

Expected behavior:

- Teams message reaches the local bridge.
- Bridge sends one chat-completions request to Hermes.
- Hermes returns a response.
- Bridge posts the response back to Teams.

If the bridge replies with a controlled error, check bridge logs and Hermes credentials. If Teams never triggers a log line, check the tunnel, endpoint path, Teams app registration, and whether the app is actually installed.

## Production Deployment Pattern

For production, do not use a temporary tunnel. Deploy the bridge behind a stable HTTPS endpoint.

Recommended minimum layout:

```text
internet
  -> reverse proxy or ingress with TLS
  -> teams-hermes-bridge Node.js service
  -> private Hermes Agent endpoint
```

Example production environment:

```dotenv
NODE_ENV=production
PORT=3978
CLIENT_ID=<from Teams registration>
CLIENT_SECRET=<from secret manager>
TENANT_ID=<from Teams registration>
HERMES_BASE_URL=http://127.0.0.1:8643
HERMES_API_KEY=<from secret manager>
HERMES_MODEL=glm-5.2:cloud
HERMES_SYSTEM_PROMPT=You are a helpful Hermes Agent inside Microsoft Teams. Be concise, accurate, and transparent when unsure.
```

Build:

```bash
npm ci
npm run typecheck
npm run build
```

Run:

```bash
node dist/index.js
```

Register the production endpoint:

```bash
teams app create \
  --name hermes-agent-prod \
  --endpoint https://teams-hermes.example.com/api/messages \
  --env .env.production
```

Use one Teams app registration per environment:

- `hermes-agent-dev`
- `hermes-agent-staging`
- `hermes-agent-prod`

Do not casually delete and recreate production Teams app registrations, because conversation IDs and proactive messaging references can become invalid.

## Docker Deployment

Example Dockerfile for the generated bridge project:

```Dockerfile
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM deps AS build
COPY tsconfig.json ./
COPY src ./src
RUN npm run typecheck && npm run build

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3978
CMD ["node", "dist/index.js"]
```

Build and run:

```bash
docker build -t teams-hermes-bridge:latest .
docker run -d \
  --name teams-hermes-bridge \
  --restart unless-stopped \
  --env-file .env.production \
  -p 127.0.0.1:3978:3978 \
  teams-hermes-bridge:latest
```

Put nginx, Caddy, Traefik, or Kubernetes ingress in front of it for HTTPS.

## Kubernetes Deployment Sketch

Use this only after validating local Teams registration and Hermes API behavior.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: teams-hermes-secrets
type: Opaque
stringData:
  CLIENT_ID: ""
  CLIENT_SECRET: ""
  TENANT_ID: ""
  HERMES_API_KEY: ""
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: teams-hermes-config
data:
  PORT: "3978"
  HERMES_BASE_URL: "http://hermes-agent.default.svc.cluster.local:8642"
  HERMES_MODEL: "glm-5.2:cloud"
  HERMES_SYSTEM_PROMPT: "You are a helpful Hermes Agent inside Microsoft Teams. Be concise, accurate, and transparent when unsure."
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: teams-hermes-bridge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: teams-hermes-bridge
  template:
    metadata:
      labels:
        app: teams-hermes-bridge
    spec:
      containers:
        - name: bridge
          image: teams-hermes-bridge:latest
          ports:
            - containerPort: 3978
          envFrom:
            - configMapRef:
                name: teams-hermes-config
            - secretRef:
                name: teams-hermes-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: teams-hermes-bridge
spec:
  selector:
    app: teams-hermes-bridge
  ports:
    - name: http
      port: 80
      targetPort: 3978
```

Add ingress/TLS separately:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: teams-hermes-bridge
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - teams-hermes.example.com
      secretName: teams-hermes-tls
  rules:
    - host: teams-hermes.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: teams-hermes-bridge
                port:
                  number: 80
```

Register Teams with:

```bash
teams app create \
  --name hermes-agent-prod \
  --endpoint https://teams-hermes.example.com/api/messages \
  --env .env.production
```

## Security Checklist

Before production:

- `.env` is ignored and not committed.
- `CLIENT_SECRET` and `HERMES_API_KEY` live in a secret manager.
- Hermes API is not publicly reachable.
- Public ingress exposes only the Teams bridge.
- TLS is valid and auto-renewing.
- Logs redact authorization headers, Teams tokens, Teams conversation IDs if needed, and Hermes errors that may contain prompt text.
- Bridge returns safe generic errors to Teams users.
- Tenant upload policy is restricted to the right users/groups.
- App registration ownership is clear.
- Separate app registrations exist for dev/staging/prod.

## AI UX Checklist

For internal testing, a plain text response is acceptable. For production AI use in Teams, add:

- AI-generated content labels.
- Citations when Hermes uses retrieved or external material.
- Feedback buttons.
- Sensitivity labels where content policy requires them.
- A system prompt that says the bot is an AI/Hermes assistant and should not claim to be a human.
- A support/escalation path for failed answers.

Microsoft's AI-generated bot message docs cover AI labels, citations, feedback buttons, and sensitivity labels:

<https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content>

## Proactive Messaging

Do not start with proactive messaging. Add it only after basic chat works.

For proactive messages:

- Store the Teams `tenantId`.
- Store the Teams user/channel/team identifiers from actual conversation context.
- Store conversation references only after the bot has been installed in that scope.
- Do not address proactive messages by email or UPN.
- Handle `403` as a possible uninstall/block/not-installed condition.

Reference:

<https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/conversations/send-proactive-messages>

## Troubleshooting

### `teams` command not found

Install the CLI:

```bash
npm install -g @microsoft/teams.cli@preview
```

Then restart your shell or ensure npm global bin is on `PATH`.

### `teams status` says sideloading is disabled

The Microsoft 365 tenant policy does not allow custom app upload for your user. Ask a tenant admin to enable custom app upload or assign a Teams app setup/custom app policy that permits it.

### Teams app installs but the bot never answers

Check:

- `npm run dev` is running.
- Tunnel is running.
- Endpoint in Teams app registration exactly matches `https://<host>/api/messages`.
- The generated `.env` has Teams credentials from `teams app create`.
- You installed the same Teams app whose ID you just registered.

### Teams says something went wrong

Usually one of:

- Tunnel expired.
- TLS certificate is invalid.
- Endpoint URL changed after registration.
- Bot server is not listening on `PORT`.
- App registration credentials do not match local `.env`.

### Hermes returns `401 Unauthorized`

`HERMES_API_KEY` is wrong or missing. Do not print the key. Update the local `.env` or production secret manager, restart the bridge, and retest.

### Hermes health passes but Teams responses fail

Check that the Hermes server exposes `/v1/chat/completions`, not just `/health`. The bridge uses the OpenAI-compatible chat-completions endpoint.

### Local curl works but Teams cannot reach the bridge

Teams calls from Microsoft's cloud, not from your laptop. Localhost and private IPs do not work unless exposed through a public HTTPS tunnel or production ingress.

### Production ingress returns 404

Confirm the Teams registration endpoint path is `/api/messages` and the reverse proxy forwards that path to the bridge.

### Proactive send returns `403`

The bot may not be installed in the target scope, the user blocked/uninstalled it, or stored conversation references are stale.

## Maintenance

When Microsoft Teams SDK or CLI behavior changes:

1. Re-read the official quickstart and registration docs.
2. Update `references/microsoft-teams-sources.md`.
3. Regenerate a temp bridge with `scripts/create-teams-hermes-bridge.sh`.
4. Run:

```bash
npm install
npm run typecheck
```

5. Test `teams app create` in a dev tenant before touching production app registrations.

## Tested During Skill Creation

On 2026-06-17:

```text
quick_validate.py /home/hoyack/work/skills/teams-hermes-agent -> Skill is valid
bash -n scripts/create-teams-hermes-bridge.sh -> OK
scripts/create-teams-hermes-bridge.sh /tmp/teams-hermes-bridge-test -> OK
npm install in generated project -> OK
npm run typecheck in generated project -> OK
```

No live Microsoft tenant registration was performed during skill creation. Tenant registration requires a signed-in Microsoft 365 account with custom app upload enabled.

