# OpenClaw Configuration Reference

## Key Sections

### `agents.defaults`

Controls agent behavior defaults.

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "kimi/kimi-for-coding"
      },
      "workspace": "/data/workspace",
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      }
    }
  }
}
```

### `gateway`

Gateway network and auth settings.

```json
{
  "gateway": {
    "auth": {
      "mode": "token",
      "token": "SECURE_TOKEN_HERE"
    },
    "bind": "lan",
    "mode": "local",
    "port": 18789,
    "controlUi": {
      "allowedOrigins": [
        "https://your-domain.com",
        "http://localhost:18789"
      ],
      "dangerouslyDisableDeviceAuth": true
    }
  }
}
```

**Auth modes:**
- `token`: Simple bearer token
- `oauth`: OAuth 2.0 / OIDC (requires additional config)

**Bind modes:**
- `lan`: Bind to all interfaces (0.0.0.0)
- `localhost`: Bind to 127.0.0.1 only

**Gateway modes:**
- `local`: Standalone gateway
- `cluster`: Part of a gateway cluster (requires clustering config)

### `models`

Model provider configuration. Supports multiple providers.

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "kimi": {
        "baseUrl": "https://api.kimi.com/coding/",
        "api": "anthropic-messages",
        "apiKey": "YOUR_API_KEY",
        "models": [
          {
            "id": "kimi-for-coding",
            "name": "Kimi K2.6",
            "reasoning": true,
            "input": ["text", "image"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 262144,
            "maxTokens": 32768
          }
        ]
      }
    }
  }
}
```

**API types:**
- `anthropic-messages`: Anthropic Messages API format
- `openai-chat`: OpenAI Chat Completions format
- `google-generative`: Google Gemini API format

### `plugins`

Plugin entries enable external integrations.

#### SearXNG Plugin

```json
{
  "plugins": {
    "entries": {
      "searxng": {
        "enabled": true,
        "config": {
          "webSearch": {
            "baseUrl": "http://searxng.searxng.svc.cluster.local:8080/"
          }
        }
      }
    }
  }
}
```

**Critical:** The `baseUrl` must end with a trailing slash (`/`).

#### Firecrawl Plugin

```json
{
  "plugins": {
    "entries": {
      "firecrawl": {
        "enabled": true,
        "config": {
          "webFetch": {
            "baseUrl": "http://firecrawl.firecrawl.svc.cluster.local/"
          },
          "webSearch": {
            "baseUrl": "http://firecrawl.firecrawl.svc.cluster.local/"
          }
        }
      }
    }
  }
}
```

### `tools.web`

Selects which plugins provide search and fetch capabilities.

```json
{
  "tools": {
    "web": {
      "search": {
        "provider": "searxng"
      },
      "fetch": {
        "provider": "firecrawl"
      }
    }
  }
}
```

**Search providers:** `searxng`, `firecrawl`, `brave`, `perplexity`
**Fetch providers:** `firecrawl`, `raw` (direct HTTP)

## Full Working Example

See `assets/openclaw-config-template.json` for a complete template with variable substitution.

## Hot Reload

Config changes via the `gateway config.patch` or `gateway config.apply` tools hot-reload when possible. A safe restart is only required for:
- Gateway port/bind changes
- Auth mode changes
- Plugin dependency changes

Model provider and plugin config changes typically hot-reload without restart.
