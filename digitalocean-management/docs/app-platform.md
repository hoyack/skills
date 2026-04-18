# App Platform Reference

App Platform is DigitalOcean's managed PaaS. It builds from Git, runs containers, handles HTTPS, and scales horizontally — the nearest equivalent to Heroku, Netlify's build infrastructure, or Railway, with DigitalOcean's pricing.

This is the primary escalation target for `netlify-landing-page-deploy` and the natural home for FastAPI / Express / Rails / Django backends.

## Component Types

An **app** is a collection of **components**. One app can have multiple.

| Component | Purpose | Serves HTTP? | Always-on? |
|---|---|---|---|
| `service` | Long-running web process (HTTP server) | Yes | Yes |
| `worker` | Long-running background process | No | Yes |
| `job` | One-off or scheduled task | No | No (runs on trigger) |
| `static_site` | Prebuilt static assets on CDN | Yes | — |
| `database` | Dev database bundled with the app | — | Yes |
| `function` | Serverless function | Yes | No (cold start) |

**For backend-only apps** (FastAPI, Express, etc.), use a single `service` component.

**For SPA + backend in one app,** use a `service` (backend) + `static_site` (frontend). But the more common pattern is to deploy them separately — frontend on Netlify, backend here — because it gives each piece the best-fit platform.

## App Spec

App Platform uses a YAML (or JSON) "app spec" that describes the whole app. The MCP tools can abstract this, but for non-trivial apps you'll write or edit specs directly.

Minimal spec for a FastAPI service:

```yaml
name: thunderstaff-api
region: nyc
services:
  - name: api
    github:
      repo: <your-org>/<your-repo>
      branch: main
      deploy_on_push: true
    source_dir: /
    build_command: pip install -r requirements.txt
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
    http_port: 8080
    instance_size_slug: basic-xxs
    instance_count: 1
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
        scope: RUN_TIME
        type: SECRET
      - key: PYTHON_VERSION
        value: "3.12"
        scope: BUILD_TIME
    health_check:
      http_path: /api/v1/health
      initial_delay_seconds: 10
      period_seconds: 10
      timeout_seconds: 3
      failure_threshold: 3
```

### Spec field notes

- `region` — short slug (`nyc`, `sfo`, `ams`, `sgp`, `lon`, `fra`, `blr`, `syd`, `tor`). App Platform is NOT in every region; check availability.
- `deploy_on_push: true` — auto-redeploy on each push to `branch`. Turn off for manual deploy control.
- `source_dir` — monorepo support; subdirectory where this component lives.
- `http_port` — must match the port your app actually listens on. `${PORT}` env var is also injected.
- `instance_size_slug` — see Instance Sizes below.
- `instance_count` — horizontal scaling; only `professional-*` sizes support >1.
- `envs[].scope` — `BUILD_TIME`, `RUN_TIME`, or `RUN_AND_BUILD_TIME`. Secrets only have RUN_TIME.
- `envs[].type` — `GENERAL` (default, visible) or `SECRET` (encrypted, not shown after set).
- `envs[].value: ${db.DATABASE_URL}` — reference another component; DO substitutes automatically.

## Deployment Sources

| Source | Notes |
|---|---|
| **GitHub** | Requires one-time DO GitHub app install. Most common. |
| **GitLab** | Public and private; similar integration model. |
| **Bitbucket** | Same. |
| **DOCR** | `docr` key: pin to a registry/repo/tag. Pull-based, no build step. |
| **Docker Hub / GHCR** | `image` key with `registry_type: DOCR`/`GHCR`/`DOCKER_HUB`. |

Container sources skip the buildpack. You supply a prebuilt image; App Platform just runs it.

## Buildpacks vs. Dockerfile

App Platform auto-detects the runtime from repo contents:

- `package.json` → Node.js buildpack (Heroku-compatible)
- `requirements.txt` / `pyproject.toml` → Python buildpack
- `Gemfile` → Ruby
- `go.mod` → Go
- `pom.xml` / `build.gradle` → Java/Kotlin
- `composer.json` → PHP
- `Dockerfile` → Docker build (overrides buildpack detection)

If a `Dockerfile` exists at `source_dir`, App Platform uses Docker build instead of a buildpack. Dockerfile builds give full control (arbitrary system deps, custom layers) at the cost of slower cold builds.

## Instance Sizes

| Slug | vCPU | RAM | ~$/mo | Notes |
|---|---|---|---|---|
| `basic-xxs` | Shared | 256 MB | $5 | Good for worker/cron; tight for web apps |
| `basic-xs` | Shared | 512 MB | $10 | Minimum for most Node/Python web apps |
| `basic-s` | Shared | 1 GB | $15 | Comfortable for small production |
| `basic-m` | Shared | 2 GB | $25 | Heavier Python/Java apps |
| `professional-xs` | 1 | 1 GB | $12 | Dedicated CPU; supports horizontal scaling |
| `professional-s` | 1 | 2 GB | $25 | |
| `professional-m` | 2 | 4 GB | $50 | |
| `professional-l` | 4 | 8 GB | $100 | |

Only `professional-*` supports `instance_count > 1`. For redundancy on small apps, run two `basic-s` instances in different regions behind a manual failover rather than horizontally scaling a `basic-*` (not supported).

## Environment Variables

Three scopes, two types:

- Scopes: `BUILD_TIME` (bundle-into-build), `RUN_TIME` (runtime only), `RUN_AND_BUILD_TIME` (both)
- Types: `GENERAL` (plaintext, visible in spec), `SECRET` (encrypted at rest, not retrievable after set)

**Binding to managed databases:** when an app has a managed database attachment, App Platform injects `${db.DATABASE_URL}`, `${db.CA_CERT}`, etc. as substitution tokens in the spec. Use these instead of hardcoding.

**For frontend SPAs with build-time env vars** (e.g., `VITE_API_URL`): scope must be `BUILD_TIME` or `RUN_AND_BUILD_TIME`. Vite inlines values at build time, so RUN_TIME only is useless for those.

## Deployment Lifecycle

```
PENDING_BUILD → BUILDING → PENDING_DEPLOY → DEPLOYING → ACTIVE
                    ↓                             ↓
                  ERROR                        ERROR
```

- `app-logs --component <name> --type BUILD` — build output
- `app-logs --component <name> --type RUN --follow` — live runtime logs
- `app-rollback --deployment <id>` — revert to a previous successful deploy

## Health Checks

Every `service` component should define a `health_check`. If omitted, App Platform defaults to TCP on `http_port`, which passes even if the app is broken.

```yaml
health_check:
  http_path: /health       # endpoint your app defines
  initial_delay_seconds: 10  # wait before first check
  period_seconds: 10         # check every N seconds
  timeout_seconds: 3         # fail check if > N seconds
  failure_threshold: 3       # restart after N consecutive failures
  success_threshold: 1
```

A misconfigured health check causes constant restart loops. If a deploy is stuck in `DEPLOYING` forever, check the health_check path exists and returns 200.

## Domains

Once an app is deployed, it's reachable at `<app-name>-<hash>.ondigitalocean.app`. To attach a custom domain:

1. Add the domain to the app spec's top-level `domains` array:
   ```yaml
   domains:
     - domain: api.example.com
       type: PRIMARY
       zone: example.com
   ```
2. DO returns a CNAME or A target (depending on apex vs. subdomain)
3. Configure DNS at the provider:
   - **If DNS is on IONOS** → use `ionos-dns-management` to add the CNAME/A
   - **If DNS is on DigitalOcean** → networking service handles it automatically when `zone` matches a DO-hosted domain
4. SSL (Let's Encrypt) provisions automatically once DNS resolves

For an apex domain + `www` subdomain:
```yaml
domains:
  - domain: example.com
    type: PRIMARY
  - domain: www.example.com
    type: ALIAS
```

## Cost Controls

- Set `instance_count: 1` and `instance_size_slug: basic-xxs` for development/staging apps
- Delete preview environments when the feature branch is merged (App Platform auto-creates them for PR builds if enabled)
- Check `app-list` periodically — abandoned apps keep billing

## Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| Build succeeds, health check fails forever | Health check path doesn't exist, or app binds to wrong port |
| Build fails with "no command to run" | `run_command` missing or buildpack couldn't detect entrypoint |
| `${db.DATABASE_URL}` literal appears in runtime env | Spec typo, or database component name doesn't match |
| Deploy succeeds, app returns 502 | App listening on wrong port — must honor `$PORT` or match `http_port` |
| Build step runs out of memory | Larger instance size needed during build; consider switching to Dockerfile for builds that need more than the buildpack box offers |
| Frontend env vars are empty in production build | Scope is `RUN_TIME` only; for Vite/Next/static bundlers, must be `BUILD_TIME` |

## Workflow: Deploy a FastAPI Backend

1. **Prep the repo** — ensure `requirements.txt` (or `pyproject.toml`), the app is launched via `uvicorn` or `gunicorn`, and there's a `/health` endpoint.
2. **Create or update the spec** — either write YAML locally and `app-create --spec spec.yaml`, or let the MCP generate one from a repo URL.
3. **Set secrets** — DATABASE_URL, third-party API keys, webhook secrets as `SECRET` scope `RUN_TIME`.
4. **Attach a database** (optional) — add a `databases` component with `engine: PG, version: "16"`.
5. **Set health check** — match the app's `/health` endpoint.
6. **Watch the deploy** — `app-logs --type BUILD` during build, `--type RUN` after.
7. **Verify** — curl the `.ondigitalocean.app` URL's health endpoint.
8. **Attach custom domain** — add to `domains`, then update DNS at the appropriate provider.

## Workflow: Deploy a Docker Image from DOCR

1. **Push the image** to DOCR (see `container-registry` service)
2. **Reference in spec:**
   ```yaml
   services:
     - name: api
       image:
         registry_type: DOCR
         repository: my-app
         tag: v1.2.3
       http_port: 8080
       instance_size_slug: basic-xs
   ```
3. **Rolling deploys** — push a new tag, update the spec's `tag`, `app-deploy`. Zero-downtime rollover.
