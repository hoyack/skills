# OpenClaw Configuration - Kimi Provider

## Summary

OpenClaw has been updated to use **Kimi** as the primary chat provider instead of Ollama.

## Changes Made

### 1. Authentication Profile
**File:** `~/.openclaw/openclaw.json`

```json
"auth": {
  "profiles": {
    "kimi:default": {
      "provider": "kimi",
      "mode": "api_key"
    }
  }
}
```

### 2. Model Provider Configuration

```json
"kimi": {
  "baseUrl": "https://api.moonshot.cn/v1",
  "apiKey": "<REDACTED>",
  "api": "openai",
  "models": [
    {
      "id": "kimi-k2.5",
      "name": "Kimi K2.5",
      "contextWindow": 256000,
      "maxTokens": 8192
    },
    {
      "id": "kimi-k1.5",
      "name": "Kimi K1.5",
      "reasoning": true,
      "contextWindow": 128000,
      "maxTokens": 8192
    }
  ]
}
```

### 3. Default Model

```json
"agents": {
  "defaults": {
    "model": {
      "primary": "kimi/kimi-k2.5"
    },
    "models": {
      "kimi/kimi-k2.5": {},
      "kimi/kimi-k1.5": {},
      ...
    }
  }
}
```

## Available Kimi Models

| Model | ID | Context Window | Reasoning |
|-------|-----|----------------|-----------|
| **Kimi K2.5** | `kimi-k2.5` | 256,000 tokens | No |
| **Kimi K1.5** | `kimi-k1.5` | 128,000 tokens | Yes |

## API Endpoint

- **Base URL:** `https://api.moonshot.cn/v1`
- **API Format:** OpenAI-compatible
- **Authentication:** Bearer token (API Key)

## To Switch Models

You can switch between Kimi models by updating the `primary` field:

```json
"model": {
  "primary": "kimi/kimi-k1.5"  // For reasoning model
}
```

Or keep using K2.5 (default):

```json
"model": {
  "primary": "kimi/kimi-k2.5"  // Default general-purpose model
}
```

## Testing

To verify the configuration is working:

```bash
# Test Kimi API directly
curl https://api.moonshot.cn/v1/models \
  -H "Authorization: Bearer <KIMI_API_KEY>"
```

## Previous Configuration Backup

The previous configuration using Ollama has been backed up automatically by openclaw:
- Check `~/.openclaw/openclaw.json.bak*` for previous versions

## Notes

- Ollama configuration is still present as a fallback option
- Kimi K2.5 is set as the primary model (good balance of capability and cost)
- Kimi K1.5 is available for reasoning tasks
- Context windows are significantly larger than typical local models
