# Kubernetes Deployment Reference

## Overview

Deploy OpenClaw on Kubernetes with SearXNG as the search provider.

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- SearXNG instance reachable from the cluster
- Optional: Firecrawl instance for web fetch

## Namespace Setup

```bash
kubectl create namespace openclaw
```

## SearXNG Deployment (if not already present)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: searxng
  namespace: openclaw
spec:
  replicas: 1
  selector:
    matchLabels:
      app: searxng
  template:
    metadata:
      labels:
        app: searxng
    spec:
      containers:
        - name: searxng
          image: searxng/searxng:latest
          ports:
            - containerPort: 8080
          env:
            - name: SEARXNG_SECRET
              valueFrom:
                secretKeyRef:
                  name: searxng-secrets
                  key: secret
          volumeMounts:
            - name: settings
              mountPath: /etc/searxng
      volumes:
        - name: settings
          configMap:
            name: searxng-settings
---
apiVersion: v1
kind: Service
metadata:
  name: searxng
  namespace: openclaw
spec:
  selector:
    app: searxng
  ports:
    - port: 8080
      targetPort: 8080
```

Key SearXNG settings in ConfigMap:
- `search.safe_search`: 0 (disabled), 1 (moderate), 2 (strict)
- `search.autocomplete`: "" (disabled), or provider name
- `server.limiter`: false (disable rate limiting for internal use)
- `server.method`: "GET" or "POST"

## OpenClaw Deployment

Use the template in `assets/k8s-deployment.yaml`. Replace placeholders:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{NAMESPACE}}` | K8s namespace | `openclaw` |
| `{{AUTH_TOKEN}}` | Gateway auth token | Generate with `openssl rand -hex 32` |
| `{{MODEL_PROVIDER}}` | Model provider key | `kimi`, `openai`, `anthropic` |
| `{{MODEL_ID}}` | Model identifier | `kimi-for-coding` |
| `{{MODEL_BASE_URL}}` | Provider API base URL | `https://api.kimi.com/coding/` |
| `{{MODEL_API_TYPE}}` | API format | `anthropic-messages` |
| `{{MODEL_API_KEY}}` | Provider API key | From secret |
| `{{MODEL_NAME}}` | Human-readable name | `Kimi K2.6` |
| `{{MODEL_CONTEXT_WINDOW}}` | Context window size | `262144` |
| `{{MODEL_MAX_TOKENS}}` | Max output tokens | `32768` |
| `{{SEARXNG_URL}}` | SearXNG service URL | `http://searxng.openclaw.svc.cluster.local:8080/` |
| `{{FIRECRAWL_URL}}` | Firecrawl service URL | `http://firecrawl.openclaw.svc.cluster.local/` |

## ConfigMap Generation

Generate the OpenClaw config and create the ConfigMap:

```bash
# 1. Fill out the config template
python3 scripts/generate-config.py \
  --provider kimi \
  --model kimi-for-coding \
  --searxng-url http://searxng.openclaw.svc.cluster.local:8080/ \
  --output openclaw.json

# 2. Create ConfigMap
kubectl create configmap openclaw-config \
  --from-file=openclaw.json=openclaw.json \
  -n openclaw

# 3. Create secret for auth token and model API key
kubectl create secret generic openclaw-secrets \
  --from-literal=auth-token="$(openssl rand -hex 32)" \
  --from-literal=model-api-key="YOUR_API_KEY" \
  -n openclaw
```

## Ingress (optional)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openclaw-gateway
  namespace: openclaw
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - openclaw.example.com
      secretName: openclaw-tls
  rules:
    - host: openclaw.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: openclaw-gateway
                port:
                  number: 18789
```

## Verification

After deployment, verify:

```bash
# Check pods
kubectl get pods -n openclaw

# Check OpenClaw is responding
kubectl port-forward svc/openclaw-gateway 18789:18789 -n openclaw
curl http://localhost:18789/healthz

# Verify SearXNG from within the pod
kubectl exec -it deploy/openclaw-gateway -n openclaw -- \
  curl -s http://searxng.openclaw.svc.cluster.local:8080/healthz
```

## Troubleshooting

| Issue | Check |
|-------|-------|
| Search returns no results | SearXNG pod status, network policy, SearXNG logs |
| Gateway won't start | ConfigMap JSON validity, secret values, model provider URL |
| 401 errors | Auth token mismatch between client and gateway |
| High latency | SearXNG rate limiting, model provider latency |
