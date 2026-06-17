---
name: "deploy-hermes-docker-agent"
description: "Deploy a randomized local Docker Hermes agent with Ollama Cloud and SearXNG."
---

# Deploy Hermes Docker Agent

Use when Boss asks to deploy a new local Docker-hosted Hermes Agent like Birdie.

## Defaults

- Docker image: `nousresearch/hermes-agent:latest`
- Model provider: `ollama-cloud`
- Model: `glm-5.2:cloud`
- Ollama base URL: `https://ollama.com/v1`
- Search backend: `searxng`
- SearXNG URL: `https://searxng.hoyack.ai`
- Timezone: `America/Chicago`
- Gateway command: `gateway run`
- API bind: loopback only, `127.0.0.1:<host-port>->8642/tcp`
- Dashboard: disabled unless the user explicitly asks for it
- Data root: `$HOME/.hermes-agents/<random-slug>` mounted as `/opt/data`

## Rules

- Choose the agent name yourself unless the user provides one. Use a short random codename and derive a safe slug from it.
- Never hardcode API keys in the skill, memory, logs, Docker command line, or final response.
- Accept the Ollama Cloud key from `OLLAMA_API_KEY` or hidden terminal prompt. If a key was pasted in chat, recommend rotation after deployment is confirmed.
- Abort instead of overwriting if the chosen container name or data directory already exists.
- Avoid ports already in use. Pick the first available loopback host port starting at `8642` unless the user gives one.
- Do not enable messaging channels or Slack as part of this skill.

## Workflow

1. Confirm Docker is available with `docker --version`.
2. Generate a random display name and slug, for example `Astra` -> `hermes-astra`.
3. Pick an unused loopback host port starting at `8642`.
4. Pull or use `nousresearch/hermes-agent:latest`.
5. Create the data directory with mode `0700`.
6. Write Hermes config and `.env` through a transient container using `/opt/hermes/.venv/bin/python`, not host-side YAML editing.
7. Start the persistent container:

```bash
docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  -v "$DATA_DIR:/opt/data" \
  -p "127.0.0.1:$HOST_PORT:8642" \
  nousresearch/hermes-agent:latest gateway run
```

8. Verify:

```bash
docker ps --filter "name=$CONTAINER"
curl -sS --max-time 5 "http://127.0.0.1:$HOST_PORT/health"
docker exec "$CONTAINER" hermes status
docker exec "$CONTAINER" hermes doctor
```

9. Report the container name, data directory, host health URL, TUI command, and any non-blocking doctor warnings.

## TUI

Tell the user to open the TUI with:

```bash
docker exec -it <container-name> hermes --tui
```

Resume the latest TUI session with:

```bash
docker exec -it <container-name> hermes --tui --continue
```

## Expected Files

Write these into `/opt/data`:

- `config.yaml` with `model.provider=ollama-cloud`, `model.default=glm-5.2:cloud`, `web.search_backend=searxng`, `display.interface=tui`, and `timezone=America/Chicago`.
- `.env` with `OLLAMA_API_KEY`, `OLLAMA_BASE_URL`, `SEARXNG_URL`, `API_SERVER_ENABLED=true`, `API_SERVER_HOST=0.0.0.0`, `API_SERVER_PORT=8642`, and a generated `API_SERVER_KEY`.
- `SOUL.md` naming the agent and describing the runtime.
- `README-<SLUG>.md` with start/stop/status/logs/TUI commands.

## Helper Script

Prefer `scripts/deploy-hermes-docker-agent.sh` when available. It implements the default deployment path and keeps the API key out of the process command line by reading it from `OLLAMA_API_KEY` or a hidden prompt.
