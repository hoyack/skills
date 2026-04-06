# Crawl Strategies and Patterns

## Documentation Site Crawl

Crawl all pages under a docs subdirectory:

```bash
curl -X POST http://localhost:3002/v1/crawl \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com",
    "limit": 200,
    "maxDepth": 5,
    "includePaths": ["/docs/*", "/api/*"],
    "excludePaths": ["/blog/*", "/changelog/*"],
    "scrapeOptions": {
      "formats": ["markdown"],
      "onlyMainContent": true
    }
  }'
```

## Blog Crawl (Recent Posts Only)

```bash
curl -X POST http://localhost:3002/v1/crawl \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://blog.example.com",
    "limit": 50,
    "maxDepth": 2,
    "includePaths": ["/posts/*", "/articles/*"],
    "scrapeOptions": {
      "formats": ["markdown"],
      "onlyMainContent": true,
      "excludeTags": ["nav", "footer", ".sidebar"]
    }
  }'
```

## E-commerce Product Catalog

```bash
curl -X POST http://localhost:3002/v1/crawl \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://shop.example.com/products",
    "limit": 500,
    "maxDepth": 3,
    "includePaths": ["/products/*"],
    "excludePaths": ["/cart*", "/checkout*", "/account*"],
    "deduplicateSimilarURLs": true,
    "ignoreQueryParameters": true,
    "scrapeOptions": {"formats": ["markdown", "links"]}
  }'
```

## Full Domain Crawl

```bash
curl -X POST http://localhost:3002/v1/crawl \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "crawlEntireDomain": true,
    "allowSubdomains": true,
    "limit": 1000,
    "scrapeOptions": {"formats": ["markdown"]}
  }'
```

## Monitoring Crawl Progress

```bash
# Start crawl
JOB_ID=$(curl -s -X POST http://localhost:3002/v1/crawl \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://docs.example.com","limit":100}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

echo "Job: $JOB_ID"

# Poll status
curl -s http://localhost:3002/v1/crawl/$JOB_ID \
  -H "Authorization: Bearer fc-test-key-local" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f'Status: {d[\"status\"]}')
print(f'Progress: {d.get(\"completed\",0)}/{d.get(\"total\",\"?\")}')
print(f'Credits: {d.get(\"creditsUsed\",0)}')
"

# Cancel if needed
curl -X DELETE http://localhost:3002/v1/crawl/$JOB_ID \
  -H "Authorization: Bearer fc-test-key-local"
```

## Map Before Crawl

Discover URLs first, then selectively scrape:

```bash
# Step 1: Map the site
URLS=$(curl -s -X POST http://localhost:3002/v1/map \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","limit":100}')

echo "$URLS" | python3 -c "import sys,json; links=json.load(sys.stdin)['links']; print(f'{len(links)} URLs found'); [print(f'  {l}') for l in links[:10]]"

# Step 2: Batch scrape interesting URLs
curl -X POST http://localhost:3002/v1/batch/scrape \
  -H "Authorization: Bearer fc-test-key-local" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/pricing", "https://example.com/features"],
    "formats": ["markdown"]
  }'
```

## Performance Tuning

For large crawls, adjust Firecrawl `.env`:
```
CRAWL_CONCURRENT_REQUESTS=10   # Parallel page fetches
MAX_CONCURRENT_JOBS=5          # Parallel crawl jobs
BROWSER_POOL_SIZE=5            # Playwright instances
NUM_WORKERS_PER_QUEUE=8        # Worker threads
```

Add delays for polite crawling:
```json
{"url": "...", "delay": 1000}
```
