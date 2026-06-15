---
name: deploy-openclaw
description: Deploy OpenClaw gateway instances on Kubernetes with SearXNG as the web search provider. Use when the user wants to (1) Deploy a new OpenClaw instance, (2) Configure or verify SearXNG search integration, (3) Generate OpenClaw configuration files, (4) Set up K8s manifests for OpenClaw + SearXNG, or (5) Troubleshoot search provider connectivity in an OpenClaw deployment.
---

# Deploy OpenClaw with SearXNG

Deploy OpenClaw gateway instances with SearXNG pre-configured as the web search provider.

## Quick Start

1. **Read `references/k8s-deployment.md`** for full K8s deployment patterns
2. **Read `references/configuration.md`** for config field details
3. **Use `assets/openclaw-config-template.json`** as the base config
4. **Run `scripts/verify-searxng.py`** to test SearXNG before deploying

## Deployment Workflow

### Step 1: Verify Prerequisites

- Kubernetes cluster accessible via kubectl
- SearXNG instance running and reachable from the cluster
- Model provider API key ready

Verify SearXNG is responding:

```bash
python3 scripts/verify-searxng.py --url http://searxng.YOUR_NAMESPACE.svc.cluster.local:8080/
```

### Step 2: Generate Configuration

Fill out the config template (`assets/openclaw-config-template.json`).

Required variables:

| Variable | Description |
|----------|-------------|
| `MODEL_PROVIDER` | Provider key (`kimi`, `openai`, `anthropic`) |
| `MODEL_ID` | Model identifier |
| `MODEL_BASE_URL` | Provider API endpoint |
| `MODEL_API_TYPE` | API format (`anthropic-messages`, `openai-chat`) |
| `MODEL_API_KEY` | Provider API key |
| `SEARXNG_URL` | SearXNG service URL (must end with `/`) |
| `FIRECRAWL_URL` | Firecrawl service URL (optional) |
| `AUTH_TOKEN` | Gateway bearer token |

Critical: `SEARXNG_URL` **must end with a trailing slash** (`/`).

Critical: Set `tools.web.search.provider` to `"searxng"`.

### Step 3: Deploy to Kubernetes

Use `assets/k8s-deployment.yaml` as the manifest template. Replace all `{{PLACEHOLDER}}` values.

Deploy order:

```bash
# 1. Create namespace
kubectl create namespace <NAMESPACE>

# 2. Create ConfigMap from generated config
kubectl create configmap openclaw-config \
  --from-file=openclaw.json=openclaw.json \
  -n <NAMESPACE>

# 3. Create secrets
kubectl create secret generic openclaw-secrets \
  --from-literal=auth-token="<AUTH_TOKEN>" \
  --from-literal=model-api-key="<MODEL_API_KEY>" \
  -n <NAMESPACE>

# 4. Apply deployment manifest
kubectl apply -f k8s-deployment.yaml
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n <NAMESPACE>

# Port-forward and test gateway
kubectl port-forward svc/openclaw-gateway 18789:18789 -n <NAMESPACE>
curl http://localhost:18789/healthz

# Test search via OpenClaw
# (Use the web_search tool in an OpenClaw session)
```

## Configuration Hot-Reload

After deployment, update config without restart:

```bash
# Via gateway config.patch (preferred for small changes)
# Or edit ConfigMap and bounce deployment
kubectl rollout restart deployment/openclaw-gateway -n <NAMESPACE>
```

Most plugin and model config changes hot-reload automatically.
Port/bind/auth changes require a gateway restart.

## Assets

- **`assets/openclaw-config-template.json`** — Config template with variable placeholders
- **`assets/k8s-deployment.yaml`** — Kubernetes manifest template

## References

- **`references/k8s-deployment.md`** — Full K8s deployment guide with SearXNG sidecar setup, Ingress, and troubleshooting
- **`references/configuration.md`** — Complete config field reference, all sections, and API type mappings

## Scripts

- **`scripts/verify-searxng.py`** — Verify SearXNG health and search functionality before deploying

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Search tool fails silently | Check `tools.web.search.provider` is `"searxng"`. Verify `SEARXNG_URL` ends with `/`. Run `verify-searxng.py`. |
| Gateway 401 | Verify auth token in secret matches client token. |
| Model errors | Verify `MODEL_BASE_URL`, `MODEL_API_KEY`, and `MODEL_API_TYPE`. |
| Config not applied | Check ConfigMap was updated and deployment was rolled out. |
