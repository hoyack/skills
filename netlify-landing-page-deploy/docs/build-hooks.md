# Build Hooks Reference

A **build hook** is a URL that triggers a deploy when POSTed to — no auth needed. Useful for:

- Scheduled deploys (cron → curl the hook)
- External CMS updates triggering a rebuild
- Re-running a deploy without a git push

## Build Hook Object

From `GET /api/v1/sites/:site_id/build_hooks`:

| Field | Type | Description |
|---|---|---|
| `id` | string | Hook ID |
| `site_id` | UUID | Parent project |
| `title` | string | Human label |
| `branch` | string | Branch to build |
| `url` | string | The trigger URL — treat as a secret |
| `created_at` | ISO 8601 | |

## Operations

### List hooks

```bash
curl -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/build_hooks"
```

### Create a hook

```bash
curl -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"title": "CMS rebuild", "branch": "main"}' \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/build_hooks"
```

Response includes `url` — save it, you can retrieve it again later via the list endpoint but leaking it triggers rebuilds.

### Trigger the hook (no auth)

```bash
curl -X POST "https://api.netlify.com/build_hooks/$HOOK_ID"
```

Optional body for Netlify to record with the deploy:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"trigger_title": "CMS content updated", "trigger_branch": "main"}' \
  "https://api.netlify.com/build_hooks/$HOOK_ID"
```

### Delete a hook

```bash
curl -X DELETE -H "Authorization: Bearer $TOK" \
  "https://api.netlify.com/api/v1/sites/$SITE_ID/build_hooks/$HOOK_ID"
```

## Security

- Hook URLs are bearer-token-equivalent: anyone with the URL can trigger a deploy
- Don't commit hook URLs to git
- Rotate by deleting + recreating if leaked
- Hooks only trigger deploys, they can't read site data — worst-case abuse is wasted build minutes

## Use Cases

### Cron-based rebuild

```bash
# crontab: rebuild every night at 3am
0 3 * * * curl -sS -X POST https://api.netlify.com/build_hooks/$HOOK_ID > /dev/null
```

### Headless CMS integration

Most headless CMSs (Contentful, Sanity, Storyblok, Strapi) have a "deploy on publish" webhook setting — paste the hook URL.

### Manual rebuild from the skill

When a deploy failed transiently or config changed without a code change, POST the hook instead of making a dummy commit.
