# Microsoft Teams Sources

Last checked: 2026-06-17.

## Primary Microsoft Guidance

- Teams SDK welcome: https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/welcome
  - Teams SDK is the current suite for building Teams agents/apps.
  - Fastest path is Teams Developer CLI: register app, build first bot, write message handler.
  - Supports TypeScript, C#, and Python.
- Teams SDK register quickstart: https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/get-started/quickstart-register
  - Requires Node.js 20+, M365 tenant with sideloading/custom app upload, and a public HTTPS tunnel for local server.
  - Installs CLI with `npm install -g @microsoft/teams.cli@preview`.
  - Uses `teams login`, `teams status`, and `teams app create --endpoint https://<tunnel-host>/api/messages --env .env`.
  - `teams app create` writes credentials into `.env` and prints Teams App ID plus install link.
- Teams SDK build quickstart: https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/get-started/quickstart-build
  - TypeScript scaffold uses `import { App } from '@microsoft/teams.apps'`.
  - Minimal handler pattern is `app.on('message', async ({ send, activity }) => { ... })`.
  - `app.start(process.env.PORT || 3978)` starts the HTTP server.
- Bots in Teams: https://learn.microsoft.com/en-us/microsoftteams/platform/bots/build-a-bot
  - Conventional Teams bots can use Agents Toolkit, Bot Framework SDK, or Teams SDK.
  - Existing conventional bots can be elevated with an AI layer.
- Bot Framework SDK overview: https://learn.microsoft.com/en-us/azure/bot-service/bot-service-overview?view=azure-bot-service-4.0
  - Microsoft notes the Bot Framework SDK and Emulator GitHub projects are archived and no longer maintained.
  - Microsoft recommends Microsoft 365 Agents SDK for new choice-of-AI-service agents and Teams SDK for collaborative agents in Teams.
- Connect Bot Framework bot to Teams: https://learn.microsoft.com/en-us/azure/bot-service/channel-connect-teams?view=azure-bot-service-4.0
  - Keep as fallback for existing Azure Bot Service/Bot Framework environments.
  - Production bots should be added to Teams as part of a Teams app, not just by bot GUID.
  - Use one bot channel registration per environment.
- Proactive messages in Teams: https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/conversations/send-proactive-messages
  - Store `tenantId` and user/channel/team addressing data.
  - Teams does not support proactive messages by email or UPN.
  - `403` can mean bot blocked/uninstalled or bot not installed in target scope.
- AI generated bot messages: https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content
  - Add AI label, citations, feedback buttons, and sensitivity labels for production AI responses.
  - Teams SDK can enable feedback loop; Bot Framework requires explicit message entities/channelData.

## Recommended Architecture for Hermes

Use a thin Teams SDK bridge:

```text
Teams client
  -> Microsoft Teams/Bot service
  -> public HTTPS endpoint /api/messages
  -> Teams SDK TypeScript bridge
  -> private Hermes Agent HTTP API
```

Keep Hermes private. The bridge owns Teams auth, message cleanup, error handling, and conversation policy. Hermes remains a model/agent backend.

## Decision Notes

- Prefer TypeScript for first implementation because Microsoft quickstarts show the shortest Teams SDK path and the local runtime is easy to deploy behind a reverse proxy or tunnel.
- Prefer Teams Developer CLI over hand-building app manifests unless the tenant already has a managed app packaging workflow.
- Prefer Teams SDK over Bot Framework SDK for new work. Use Bot Framework only when migrating an existing bot or when a tenant's Azure Bot Service process is already established and cannot move yet.

