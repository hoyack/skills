#!/usr/bin/env bash
set -euo pipefail

IMAGE="${HERMES_IMAGE:-nousresearch/hermes-agent:latest}"
MODEL="${HERMES_MODEL:-glm-5.2:cloud}"
SEARXNG_URL="${SEARXNG_URL:-https://searxng.hoyack.ai}"
TIMEZONE="${HERMES_TIMEZONE:-America/Chicago}"
DATA_PARENT="${HERMES_DATA_PARENT:-$HOME/.hermes-agents}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

choose_name() {
  if [ -n "${HERMES_AGENT_NAME:-}" ]; then
    printf '%s\n' "$HERMES_AGENT_NAME"
    return
  fi
  python3 - <<'PY'
import random
names = ["Astra", "Lumen", "Quartz", "Vector", "Echo", "Prism", "Nova", "Sol", "Kite", "Rune", "Vega", "Halo"]
print(random.choice(names) + "-" + format(random.randrange(16**3), "03x"))
PY
}

slugify() {
  python3 - "$1" <<'PY'
import re, sys
s = sys.argv[1].strip().lower()
s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
print(s or "hermes-agent")
PY
}

pick_port() {
  if [ -n "${HERMES_HOST_PORT:-}" ]; then
    printf '%s\n' "$HERMES_HOST_PORT"
    return
  fi
  python3 - <<'PY'
import socket
for port in range(8642, 8743):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        raise SystemExit(0)
raise SystemExit("no free loopback port in 8642-8742")
PY
}

DISPLAY_NAME="$(choose_name)"
SLUG="$(slugify "$DISPLAY_NAME")"
CONTAINER="hermes-${SLUG}"
DATA_DIR="${DATA_PARENT}/${SLUG}"
HOST_PORT="$(pick_port)"

if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER"; then
  echo "container already exists: $CONTAINER" >&2
  exit 1
fi
if [ -e "$DATA_DIR" ]; then
  echo "data directory already exists: $DATA_DIR" >&2
  exit 1
fi

if [ -z "${OLLAMA_API_KEY:-}" ]; then
  printf 'Ollama Cloud API key: ' >&2
  stty -echo 2>/dev/null || true
  IFS= read -r OLLAMA_API_KEY
  stty echo 2>/dev/null || true
  printf '\n' >&2
fi
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  echo "OLLAMA_API_KEY is required" >&2
  exit 1
fi

install -d -m 700 "$DATA_DIR"
docker pull "$IMAGE" >/dev/null

printf '%s\n' "$OLLAMA_API_KEY" | docker run --rm -i \
  -v "$DATA_DIR:/opt/data" \
  --env HERMES_AGENT_DISPLAY="$DISPLAY_NAME" \
  --env HERMES_CONTAINER="$CONTAINER" \
  --env HERMES_MODEL="$MODEL" \
  --env HERMES_TIMEZONE="$TIMEZONE" \
  --env SEARXNG_URL="$SEARXNG_URL" \
  --env HERMES_HOST_PORT="$HOST_PORT" \
  --entrypoint sh "$IMAGE" -lc '/opt/hermes/.venv/bin/python - <<"PY"
import os, pathlib, secrets, sys
import yaml
api_key = sys.stdin.readline().rstrip("\n")
root = pathlib.Path("/opt/data")
root.mkdir(parents=True, exist_ok=True)
config_path = root / "config.yaml"
cfg = {}
if config_path.exists():
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
model = cfg.get("model") if isinstance(cfg.get("model"), dict) else {}
model.update({
    "provider": "ollama-cloud",
    "default": os.environ["HERMES_MODEL"],
    "base_url": "https://ollama.com/v1",
    "api_mode": "chat_completions",
})
cfg["model"] = model
cfg["timezone"] = os.environ["HERMES_TIMEZONE"]
display = cfg.get("display") if isinstance(cfg.get("display"), dict) else {}
display["interface"] = "tui"
cfg["display"] = display
web = cfg.get("web") if isinstance(cfg.get("web"), dict) else {}
web["search_backend"] = "searxng"
cfg["web"] = web
terminal = cfg.get("terminal") if isinstance(cfg.get("terminal"), dict) else {}
terminal.setdefault("backend", "local")
cfg["terminal"] = terminal
with config_path.open("w", encoding="utf-8") as f:
    yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=False)
os.chmod(config_path, 0o600)

env_path = root / ".env"
updates = {
    "OLLAMA_API_KEY": api_key,
    "OLLAMA_BASE_URL": "https://ollama.com/v1",
    "SEARXNG_URL": os.environ["SEARXNG_URL"],
    "API_SERVER_ENABLED": "true",
    "API_SERVER_HOST": "0.0.0.0",
    "API_SERVER_PORT": "8642",
    "API_SERVER_KEY": secrets.token_hex(32),
}
env_path.write_text("\n".join(f"{k}={v}" for k, v in updates.items()) + "\n", encoding="utf-8")
os.chmod(env_path, 0o600)

display_name = os.environ["HERMES_AGENT_DISPLAY"]
container = os.environ["HERMES_CONTAINER"]
host_port = os.environ["HERMES_HOST_PORT"]
readme = f"""# {display_name} Hermes Agent\n\n## Runtime\n\n- Container: `{container}`\n- Provider: `ollama-cloud`\n- Model: `{os.environ['HERMES_MODEL']}`\n- Search: `{os.environ['SEARXNG_URL']}`\n- Health: `http://127.0.0.1:{host_port}/health`\n\n## TUI\n\n```bash\ndocker exec -it {container} hermes --tui\ndocker exec -it {container} hermes --tui --continue\n```\n\n## Operations\n\n```bash\ndocker start {container}\ndocker stop {container}\ndocker exec {container} hermes status\ndocker logs -f {container}\n```\n"""
(root / f"README-{container}.md").write_text(readme, encoding="utf-8")
(root / "SOUL.md").write_text(f"""# SOUL.md - {display_name}\n\nYou are {display_name}, a Hermes Agent running inside the local Docker container `{container}`.\n\n- Provider: Ollama Cloud.\n- Model: `{os.environ['HERMES_MODEL']}`.\n- Search backend: SearXNG at `{os.environ['SEARXNG_URL']}`.\n- Timezone: `{os.environ['HERMES_TIMEZONE']}`.\n\nOpen the TUI from the host with:\n\n```bash\ndocker exec -it {container} hermes --tui\n```\n""", encoding="utf-8")
os.chmod(root / "SOUL.md", 0o644)
os.chmod(root / f"README-{container}.md", 0o644)
os.system("chown -R 10000:10000 /opt/data")
PY'

docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  -v "$DATA_DIR:/opt/data" \
  -p "127.0.0.1:$HOST_PORT:8642" \
  "$IMAGE" gateway run >/dev/null

printf 'Deployed %s\n' "$DISPLAY_NAME"
printf 'Container: %s\n' "$CONTAINER"
printf 'Data dir: %s\n' "$DATA_DIR"
printf 'Health: http://127.0.0.1:%s/health\n' "$HOST_PORT"
printf 'TUI: docker exec -it %s hermes --tui\n' "$CONTAINER"
