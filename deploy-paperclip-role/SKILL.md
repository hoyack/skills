---
name: "deploy-paperclip-role"
description: "Deploy Paperclip roles backed by OpenClaw gateway or Hermes local adapters."
---

# Deploy Paperclip Role

Use this skill to hire or reconfigure a Paperclip agent role using either `openclaw_gateway` or `hermes_local`.

## Safety Rules

- Do not print raw Paperclip API keys, OpenClaw gateway tokens, private keys, OAuth credentials, or kubeconfig material.
- Prefer API/UI flows when authenticated board access is available; direct DB edits are acceptable for controlled admin repair work inside the Paperclip pod.
- Do not overwrite another agent's API key file. For OpenClaw roles, confirm the claimed key path before writing.
- Do not leave a new role unverified. A successful setup means a fresh wake/heartbeat run ends `succeeded` with `error=null`.
- Keep historical failed runs in mind: Paperclip shows earlier attempts in the UI. Verify the latest run, not just the visible error list.

## Current Hoyack Paperclip Environment

- K3s context: `leonidas-k3s`
- Namespace: `paperclip`
- Deployment: `paperclip`
- Public base URL: `https://paperclip.hoyack.ai`
- In-pod Postgres: `127.0.0.1:54329`, database/user/password currently `paperclip`/`paperclip`/`paperclip`; use only from inside the pod.
- Current company ID: `0a97037e-27d6-4f0a-a546-b727063169da`
- Current CEO agent ID: `51a10671-fbd5-4e84-bda4-549b28968742`
- Current COO agent ID: `c05ed82d-2dd0-4392-915e-3b7624f534ee`
- Current deployed compatibility image after COO setup: `docker.io/library/paperclip:20260705-0818`

## Decide Adapter Type

Use `hermes_local` when the role should run inside the Paperclip pod through Hermes and use the Hermes terminal/browser/tooling model.

Use `openclaw_gateway` when the role should be a named OpenClaw agent profile on Leonidas/Spartacus, with OpenClaw memory, skills, and gateway-managed tools.

Default runtime config for both paths unless the user asks otherwise:

```json
{"heartbeat":{"enabled":false,"cooldownSec":10,"intervalSec":300,"wakeOnDemand":true,"maxConcurrentRuns":1}}
```

Default role permissions for leadership/hiring roles:

```json
{"canCreateAgents":true}
```

Also add `tasks:assign` in `principal_permission_grants` for active operational roles.

## Inspect Current Paperclip State

Run these from the operator machine:

```bash
kubectl --context leonidas-k3s -n paperclip get deploy paperclip -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl --context leonidas-k3s -n paperclip get pods -l app=paperclip -o wide
curl -sS --resolve paperclip.hoyack.ai:443:104.18.35.222 https://paperclip.hoyack.ai/api/health
```

Query existing agents with secrets redacted:

```bash
kubectl --context leonidas-k3s -n paperclip exec deploy/paperclip -- sh -c 'node --input-type=module << "NODE"
import pg from "/app/node_modules/.pnpm/node_modules/pg/lib/index.js";
const c = new pg.Client({host:"127.0.0.1",port:54329,database:"paperclip",user:"paperclip",password:"paperclip"});
await c.connect();
const rows=(await c.query(`select id,company_id,name,role,title,status,reports_to,adapter_type,adapter_config,runtime_config,permissions,capabilities,icon from agents order by created_at`)).rows;
for (const row of rows) {
  if (row.adapter_config?.authToken) row.adapter_config.authToken = "<redacted>";
  if (row.adapter_config?.devicePrivateKeyPem) row.adapter_config.devicePrivateKeyPem = "<redacted>";
  console.log(JSON.stringify(row));
}
await c.end();
NODE'
```

## Path A: OpenClaw Gateway Role

### 1. Create the OpenClaw Agent Profile

On the OpenClaw host, normally Leonidas:

```bash
openclaw agents add <agent-id> \
  --workspace ~/.openclaw/agents/<agent-id>/workspace \
  --agent-dir ~/.openclaw/agents/<agent-id>/agent \
  --model openai/gpt-5.5 \
  --non-interactive --json
```

If cloning Andromeda-style identity, copy only non-secret workspace files such as `SOUL.md`, `IDENTITY.md`, `USER.md`, `AGENTS.md`, `MEMORY.md`, and recent `memory/YYYY-MM-DD.md`. Then set identity:

```bash
openclaw agents set-identity --agent <agent-id> --identity-file ~/.openclaw/agents/<agent-id>/workspace/IDENTITY.md --json
```

Smoke test before touching Paperclip:

```bash
openclaw agent --agent <agent-id> --session-key paperclip-<role>-smoke --message 'Reply exactly: READY' --json --timeout 120
```

### 2. Prepare Paperclip Agent API Key

Generate a Paperclip API token in `pcp_<48 hex>` format and store only its SHA-256 hash in `agent_api_keys`. Save the raw token only on the OpenClaw host in a `0600` JSON file.

Current deployed adapter wake text uses the default path:

```text
~/.openclaw/workspace/paperclip-claimed-api-key.json
```

For multiple OpenClaw-backed roles on the same host, patch the adapter so wake text honors `adapter_config.claimedApiKeyPath`, then store each token in a per-role path. Until that patch exists, do not overwrite the default path without understanding which Paperclip role will read it.

Safe token-file pattern:

```bash
install -d -m 700 ~/.openclaw/workspace
umask 077
printf '{"apiKey":"%s"}\n' "$PAPERCLIP_TOKEN" > ~/.openclaw/workspace/paperclip-claimed-api-key.json
chmod 600 ~/.openclaw/workspace/paperclip-claimed-api-key.json
```

### 3. Insert the Paperclip Agent

Create the agent row, membership, permission grant, and API key hash in one transaction. Redact secrets in all output.

OpenClaw adapter config template:

```json
{
  "url": "ws://192.168.0.142:18789",
  "authToken": "<leonidas gateway token>",
  "agentId": "<openclaw-agent-id>",
  "role": "operator",
  "scopes": ["operator.admin", "operator.read", "operator.write"],
  "sessionKeyStrategy": "fixed",
  "sessionKey": "paperclip-<role>",
  "timeoutSec": 300,
  "waitTimeoutMs": 300000,
  "paperclipApiUrl": "https://paperclip.hoyack.ai",
  "payloadTemplate": {
    "message": "You are <name> serving as Paperclip <ROLE>. Work through Paperclip issues using the provided API instructions. Keep leadership informed. Do not expose secrets."
  },
  "devicePrivateKeyPem": "<persistent ed25519 private key PEM>"
}
```

Generate a persistent Ed25519 key for `devicePrivateKeyPem` and keep it in `adapter_config` so OpenClaw device approval persists across wakes.

### 4. Ensure OpenClaw Adapter Compatibility

For Leonidas OpenClaw 2026.6.11, Paperclip's `openclaw-gateway` adapter must:

- Use gateway protocol `4`, not `3`.
- Sign device auth with the `v2` payload format.
- Avoid sending an extra top-level `paperclip` property in the gateway `agent` params.
- Include explicit `operator.read` and `operator.write` scopes; do not rely on `operator.admin` implying them.

Verify in the running pod:

```bash
kubectl --context leonidas-k3s -n paperclip exec deploy/paperclip -- sh -c '
  grep -R "const PROTOCOL_VERSION = 4" -n /app/node_modules/.pnpm/node_modules/@paperclipai/adapter-openclaw-gateway/src/server/execute.ts /app/packages/adapters/openclaw-gateway/src/server/execute.ts 2>/dev/null | head
  grep -R "\"v2\"," -n /app/node_modules/.pnpm/node_modules/@paperclipai/adapter-openclaw-gateway/src/server/execute.ts /app/packages/adapters/openclaw-gateway/src/server/execute.ts 2>/dev/null | head
  grep -R "agentParams.paperclip" -n /app/node_modules/.pnpm/node_modules/@paperclipai/adapter-openclaw-gateway/src/server/execute.ts /app/packages/adapters/openclaw-gateway/src/server/execute.ts 2>/dev/null || true
'
```

### 5. Approve OpenClaw Device Pairing

Wake once to create a pending request. If the run fails with `openclaw_gateway_pairing_required`, approve the latest explicit request on the OpenClaw host without printing the token:

```bash
TOKEN=$(node - <<'NODE'
const fs=require("fs");
const j=JSON.parse(fs.readFileSync(process.env.HOME+"/.openclaw/openclaw.json","utf8"));
process.stdout.write(j.gateway.auth.token);
NODE
)
openclaw devices approve --latest --url ws://127.0.0.1:18789 --token "$TOKEN" --json
# If --latest only selects, approve the returned requestId explicitly:
openclaw devices approve <request-id> --url ws://127.0.0.1:18789 --token "$TOKEN" --json
```

Then wake again and verify success.

## Path B: Hermes Local Role

### 1. Create the Paperclip Agent

Use `adapter_type='hermes_local'`. Leadership roles should include `permissions.canCreateAgents=true` when they may hire or assign work.

Hermes adapter config template:

```json
{
  "extraArgs": ["--yolo"],
  "instructionsFilePath": "/paperclip/instances/default/companies/<company-id>/agents/<agent-id>/instructions/AGENTS.md",
  "instructionsRootPath": "/paperclip/instances/default/companies/<company-id>/agents/<agent-id>/instructions",
  "instructionsEntryFile": "AGENTS.md",
  "instructionsBundleMode": "managed"
}
```

### 2. Write Managed Instructions

Create the instructions directory under `/paperclip/instances/default/companies/<company-id>/agents/<agent-id>/instructions/` and write `AGENTS.md` with:

- Role title and authority.
- Paperclip issue workflow.
- Explicit instruction to use `Authorization: Bearer $PAPERCLIP_API_KEY` for all API calls.
- Explicit instruction to include `X-Paperclip-Run-Id: $PAPERCLIP_RUN_ID` on mutating calls.
- Reminder that stderr session IDs can be benign; judge run status by Paperclip run status and exit code.

### 3. Ensure Hermes Adapter Auth Patch

Hermes unattended Paperclip runs must not wait for curl approval and must receive Paperclip auth.

Verify the deployed image includes the Hermes patch script effects:

- Hermes runs with `extraArgs:["--yolo"]`.
- Hermes adapter injects `PAPERCLIP_API_KEY = ctx.authToken` when no explicit key exists.
- Default Paperclip curl instructions include bearer auth.

If missing, patch `/home/hoyack/work/paperclip/scripts/patch-hermes-adapter-xai-oauth.mjs`, rebuild Paperclip, import to Leonidas K3s, and roll the deployment.

## Rebuild and Deploy Paperclip Image

Use when adapter source or Dockerfile changes are required:

```bash
cd /home/hoyack/work/paperclip
TAG=paperclip:$(date +%Y%m%d-%H%M)
docker build -t "$TAG" .
docker save "$TAG" | ssh leonidas 'sudo k3s ctr images import -'
kubectl --context leonidas-k3s -n paperclip set image deploy/paperclip paperclip="docker.io/library/${TAG}"
kubectl --context leonidas-k3s -n paperclip rollout status deploy/paperclip --timeout=180s
kubectl --context leonidas-k3s -n paperclip get pods -l app=paperclip -o wide
```

Validate health after every rollout:

```bash
curl -sS --resolve paperclip.hoyack.ai:443:104.18.35.222 https://paperclip.hoyack.ai/api/health
```

## Wake and Verify

Use the role's Paperclip API key to invoke itself:

```bash
STATUS=$(curl -sS -o /tmp/paperclip-wake.json -w '%{http_code}' \
  --resolve paperclip.hoyack.ai:443:104.18.35.222 \
  -X POST \
  -H "Authorization: Bearer $PAPERCLIP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "https://paperclip.hoyack.ai/api/agents/<agent-id>/heartbeat/invoke")
```

Poll the run:

```bash
kubectl --context leonidas-k3s -n paperclip exec deploy/paperclip -- sh -c 'node --input-type=module << "NODE"
import pg from "/app/node_modules/.pnpm/node_modules/pg/lib/index.js";
const id=process.env.RUN_ID;
const c=new pg.Client({host:"127.0.0.1",port:54329,database:"paperclip",user:"paperclip",password:"paperclip"});
await c.connect();
const run=(await c.query(`select id,status,started_at,finished_at,error,error_code,result_json,log_ref from heartbeat_runs where id=$1`, [id])).rows[0];
console.log(JSON.stringify(run, null, 2));
await c.end();
NODE'
```

A healthy no-work role run usually:

- Authenticates with `GET /api/agents/me`.
- Queries assigned active issues.
- Receives an empty array if no work is assigned.
- Finishes `succeeded` with `error=null` and result status `ok`.

Read the local NDJSON log if necessary:

```bash
kubectl --context leonidas-k3s -n paperclip exec deploy/paperclip -- sh -c 'find /paperclip -path "*<run-id>.ndjson" -type f -print -exec tail -n 80 {} \;'
```

## Common Failures

- `invalid connect params: /client/id`: remove custom `clientId`; use default `gateway-client` unless OpenClaw accepts the custom ID.
- `protocol mismatch`: adapter protocol version does not match OpenClaw gateway. Leonidas OpenClaw 2026.6.11 expects protocol 4.
- `missing scope: operator.write`: include explicit `operator.read` and `operator.write` in adapter scopes and approve the device with those scopes.
- `pairing required`: persist `devicePrivateKeyPem`, create a pending wake, approve the device on the OpenClaw host, then retry.
- `unexpected property 'paperclip'`: remove top-level `agentParams.paperclip`; put Paperclip context in the message/wake text.
- `401` from Paperclip API: verify the raw Paperclip agent token file matches the hash in `agent_api_keys` and the agent is active.
- Hermes `Action blocked by user`: ensure `extraArgs` contains `--yolo`.
- Hermes API calls fail after approval bypass: ensure `PAPERCLIP_API_KEY` is injected from `ctx.authToken` and bearer headers are in the prompt.

## Final Report

Report:

- Agent name, role, agent ID, adapter type, reports-to relationship.
- Host/profile used for OpenClaw roles or instructions path for Hermes roles.
- Paperclip image tag if rebuilt.
- Latest verification run ID, status, error/error_code, and brief transcript summary.
- Any warnings, especially scheduled heartbeat disabled versus wake-on-demand enabled.
