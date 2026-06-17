#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-teams-hermes-bridge}"

if [ -e "$TARGET_DIR" ]; then
  echo "Target already exists: $TARGET_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/src"

cat > "$TARGET_DIR/package.json" <<'JSON'
{
  "name": "teams-hermes-bridge",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "start": "node dist/index.js",
    "build": "tsc --noEmit false",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@microsoft/teams.apps": "latest",
    "dotenv": "latest"
  },
  "devDependencies": {
    "@types/node": "latest",
    "tsx": "latest",
    "typescript": "latest"
  }
}
JSON

cat > "$TARGET_DIR/tsconfig.json" <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist"
  },
  "include": ["src/**/*.ts"]
}
JSON

cat > "$TARGET_DIR/.gitignore" <<'EOF'
node_modules/
dist/
.env
*.log
EOF

cat > "$TARGET_DIR/.env.example" <<'EOF'
PORT=3978

# Written by `teams app create --env .env`.
CLIENT_ID=
CLIENT_SECRET=
TENANT_ID=

# Hermes Agent API. Keep the API private and expose only this bridge to Teams.
HERMES_BASE_URL=http://127.0.0.1:8643
HERMES_API_KEY=
HERMES_MODEL=glm-5.2:cloud
HERMES_SYSTEM_PROMPT=You are a helpful Hermes Agent inside Microsoft Teams. Be concise, accurate, and transparent when unsure.
EOF

cat > "$TARGET_DIR/src/index.ts" <<'TS'
import 'dotenv/config';
import { App } from '@microsoft/teams.apps';

type HermesMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

type HermesChatChoice = {
  message?: {
    content?: string;
  };
};

type HermesChatResponse = {
  choices?: HermesChatChoice[];
  error?: {
    message?: string;
  };
};

const app = new App();

const hermesBaseUrl = (process.env.HERMES_BASE_URL || 'http://127.0.0.1:8643').replace(/\/+$/, '');
const hermesModel = process.env.HERMES_MODEL || 'glm-5.2:cloud';
const hermesSystemPrompt =
  process.env.HERMES_SYSTEM_PROMPT ||
  'You are a helpful Hermes Agent inside Microsoft Teams. Be concise, accurate, and transparent when unsure.';

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function cleanTeamsText(text: string | undefined): string {
  return (text || '')
    .replace(/<at>.*?<\/at>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

async function askHermes(prompt: string): Promise<string> {
  const apiKey = requireEnv('HERMES_API_KEY');
  const messages: HermesMessage[] = [
    { role: 'system', content: hermesSystemPrompt },
    { role: 'user', content: prompt },
  ];

  const response = await fetch(`${hermesBaseUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${apiKey}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: hermesModel,
      messages,
      temperature: 0.2,
    }),
  });

  const data = (await response.json().catch(() => ({}))) as HermesChatResponse;

  if (!response.ok) {
    const detail = data.error?.message || `${response.status} ${response.statusText}`;
    throw new Error(`Hermes request failed: ${detail}`);
  }

  const answer = data.choices?.[0]?.message?.content?.trim();
  if (!answer) {
    throw new Error('Hermes returned no assistant message.');
  }

  return answer;
}

app.on('message', async ({ send, activity }) => {
  const prompt = cleanTeamsText(activity.text);

  if (!prompt) {
    await send('Send me a prompt and I will route it to Hermes.');
    return;
  }

  await send({ type: 'typing' });

  try {
    const answer = await askHermes(prompt);
    await send(answer);
  } catch (error) {
    console.error(error);
    await send('Hermes is reachable by Teams, but the agent call failed. Check the bridge logs and Hermes API credentials.');
  }
});

const port = Number(process.env.PORT || 3978);
app.start(port).catch((error) => {
  console.error(error);
  process.exit(1);
});
TS

cat > "$TARGET_DIR/OPERATIONS.md" <<'EOF'
# Teams Hermes Bridge Operations

## Local start

```bash
cp .env.example .env
npm install
npm run dev
```

Start a public HTTPS tunnel to port 3978, then register:

```bash
teams app create \
  --name hermes-agent \
  --endpoint https://<tunnel-host>/api/messages \
  --env .env
```

Install link:

```bash
teams app get <teamsAppId> --install-link
```

## Required secrets

- `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`: written by Teams CLI.
- `HERMES_API_KEY`: Hermes Agent API key.

Never commit `.env`.
EOF

echo "Created $TARGET_DIR"
echo "Next: cd $TARGET_DIR && cp .env.example .env && npm install && npm run dev"
