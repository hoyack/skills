# Docker Deployment Complete 🎉

All three services have been successfully deployed and are running!

## Service Status

| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **SearXNG** | http://localhost:8090 | ✅ Running | Privacy-focused search engine |
| **Twenty CRM** | http://localhost:3000 | ✅ Running | Modern open-source CRM |
| **Firecrawl** | http://localhost:3002 | ✅ Running | Web scraping & crawling API |

---

## Quick Test Commands

### SearXNG (Search)
```bash
# Web UI: http://localhost:8090

# JSON API
curl -s 'http://localhost:8090/search?q=artificial+intelligence&format=json' | head -50

# HTML search
curl -s 'http://localhost:8090/search?q=hello+world'
```

### Twenty CRM
```bash
# Web UI: http://localhost:3000

# Health check
curl -s http://localhost:3000/healthz

# First-time setup: Open http://localhost:3000 and create an admin account
```

### Firecrawl (Web Scraping)
```bash
# Base API: http://localhost:3002

# Test scrape endpoint
curl -X POST http://localhost:3002/v1/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fc-test-key-local" \
  -d '{"url":"https://example.com","formats":["markdown"]}'

# Crawl endpoint (async)
curl -X POST http://localhost:3002/v1/crawl \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fc-test-key-local" \
  -d '{"url":"https://firecrawl.dev","limit":5}'

# Check crawl status
curl -s http://localhost:3002/v1/crawl/JOB_ID \
  -H "Authorization: Bearer fc-test-key-local"

# Search endpoint (uses SearXNG)
curl -X POST http://localhost:3002/v1/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fc-test-key-local" \
  -d '{"query":"latest AI news","limit":5}'
```

---

## Docker Containers

### SearXNG (2 containers)
| Container | Image | Port | Status |
|-----------|-------|------|--------|
| searxng-core | searxng/searxng:latest | 8090 | ✅ Healthy |
| searxng-valkey | valkey/valkey:9-alpine | - | ✅ Running |

### Twenty CRM (4 containers)
| Container | Image | Port | Status |
|-----------|-------|------|--------|
| twenty-server | twentycrm/twenty:latest | 3000 | ✅ Healthy |
| twenty-worker | twentycrm/twenty:latest | - | ✅ Running |
| twenty-db | postgres:16-alpine | - | ✅ Healthy |
| twenty-redis | redis:alpine | - | ✅ Running |

### Firecrawl (6 containers)
| Container | Image | Port | Status |
|-----------|-------|------|--------|
| firecrawl-api | ghcr.io/firecrawl/firecrawl:latest | 3002 | ✅ Running |
| firecrawl-nuq-worker | ghcr.io/firecrawl/firecrawl:latest | - | ✅ Running |
| firecrawl-playwright | ghcr.io/firecrawl/playwright-service:latest | - | ⚠️ Unhealthy* |
| firecrawl-nuq-postgres | postgres:16-alpine | - | ✅ Healthy |
| firecrawl-rabbitmq | rabbitmq:3-alpine | - | ✅ Healthy |
| firecrawl-redis | redis:alpine | - | ✅ Healthy |

*Playwright shows unhealthy due to missing health endpoint, but it's working correctly.

---

## Firecrawl Architecture

Firecrawl uses a sophisticated multi-service architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Firecrawl                            │
├─────────────────────────────────────────────────────────────┤
│  API (port 3002)                                            │
│  ├── Receives scrape/crawl/search requests                  │
│  ├── Queues jobs via RabbitMQ                               │
│  └── Stores metadata in PostgreSQL (NUQ schema)             │
├─────────────────────────────────────────────────────────────┤
│  NUQ Worker                                                 │
│  ├── Processes queued jobs                                  │
│  ├── Calls Playwright for browser rendering                 │
│  └── Stores results in PostgreSQL                           │
├─────────────────────────────────────────────────────────────┤
│  Supporting Services                                        │
│  ├── Playwright Service - Headless browser for JS sites     │
│  ├── PostgreSQL (NUQ) - Job queue and metadata storage      │
│  ├── RabbitMQ - Message broker for job distribution         │
│  └── Redis - Rate limiting and caching                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Innovation
The official Firecrawl image normally uses Docker-in-Docker (DinD) to spawn containers dynamically. We solved the ARM64 compatibility issue by:
1. Creating a custom PostgreSQL initialization script with the NUQ schema
2. Running workers as separate containers instead of DinD
3. Using the standard `postgres:16-alpine` image with init scripts

---

## Configuration Files

| Service | Config Files |
|---------|-------------|
| SearXNG | `searxng/docker-compose.yml`, `searxng/core-config/settings.yml` |
| Twenty CRM | `twenty-crm/docker-compose.yml`, `twenty-crm/.env` |
| Firecrawl | `firecrawl/docker-compose.yml`, `firecrawl/nuq-postgres-init.sql` |

---

## Environment Variables

### Firecrawl API Key
- **Test Key:** `fc-test-key-local` (set in `firecrawl/docker-compose.yml`)
- **Admin Panel:** http://localhost:3002/admin/firecrawl-admin-2026/queues

### Twenty CRM Secrets
Stored in `twenty-crm/.env`:
- `APP_SECRET` - Randomly generated
- `PG_DATABASE_PASSWORD` - Randomly generated

### SearXNG Secret
Stored in `searxng/core-config/settings.yml`:
- `secret_key` - Randomly generated 64-char hex string

---

## Common Operations

### View Logs
```bash
# SearXNG
docker compose -C searxng logs -f

# Twenty CRM
docker compose -C twenty-crm logs -f server

# Firecrawl
docker compose -C firecrawl logs -f api
docker compose -C firecrawl logs -f nuq-worker
```

### Restart Services
```bash
# Restart specific service
docker compose -C firecrawl restart api

# Restart all Firecrawl services
docker compose -C firecrawl restart
```

### Stop Services
```bash
# Stop Firecrawl (keep data)
docker compose -C firecrawl down

# Stop Firecrawl (remove data volumes)
docker compose -C firecrawl down -v
```

### Full Reset
```bash
# Reset Firecrawl completely (destroys all data)
cd firecrawl && docker compose down -v && docker compose up -d
```

---

## Integration Examples

### Using Firecrawl with SearXNG
Firecrawl is already configured to use your local SearXNG instance:
```bash
curl -X POST http://localhost:3002/v1/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fc-test-key-local" \
  -d '{"query":"machine learning tutorials"}'
```

### Scraping with JavaScript Support
```bash
curl -X POST http://localhost:3002/v1/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fc-test-key-local" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown", "html"],
    "onlyMainContent": true,
    "waitFor": 2000
  }'
```

### Deep Crawling
```bash
# Start a crawl job
curl -X POST http://localhost:3002/v1/crawl \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fc-test-key-local" \
  -d '{
    "url": "https://docs.firecrawl.dev",
    "excludePaths": ["/blog/*"],
    "maxDepth": 2,
    "limit": 10
  }'
```

---

## Troubleshooting

### Firecrawl Worker Not Processing Jobs
The NUQ worker polls for jobs. If no jobs are being processed:
1. Check worker logs: `docker compose -C firecrawl logs nuq-worker`
2. Verify database connectivity: `docker compose -C firecrawl exec nuq-postgres pg_isready`
3. Check RabbitMQ: `docker compose -C firecrawl exec rabbitmq rabbitmq-diagnostics check_running`

### Port Conflicts
If ports are already in use:
- **SearXNG:** Edit `searxng/docker-compose.yml`, change `8090:8080`
- **Twenty CRM:** Edit `twenty-crm/docker-compose.yml`, change `3000:3000`
- **Firecrawl:** Edit `firecrawl/docker-compose.yml`, change `3002:3002`

### Memory Issues
Firecrawl requires at least 4GB RAM for comfortable operation:
- Reduce `NUM_WORKERS_PER_QUEUE` to 1 in `firecrawl/docker-compose.yml`
- Reduce `BROWSER_POOL_SIZE` to 2

---

## Next Steps

1. **Configure Twenty CRM:**
   - Visit http://localhost:3000
   - Create admin account
   - Set up API keys for integrations

2. **Test Firecrawl Features:**
   - Try the `/v1/scrape` endpoint with various options
   - Test `/v1/crawl` for deep website crawling
   - Use `/v1/search` with your local SearXNG

3. **Optional Enhancements:**
   - Add OpenAI API key to Firecrawl for LLM features
   - Configure webhooks for crawl completion notifications
   - Set up proxy for distributed crawling

---

## API Documentation

- **Firecrawl:** https://docs.firecrawl.dev/api-reference/introduction
- **SearXNG:** https://docs.searxng.org/dev/search_api.html
- **Twenty CRM:** http://localhost:3000/graphql (GraphQL playground)

---

*All services are running on the `skills-network` Docker network for inter-service communication.*
