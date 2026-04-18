# IONOS DNS API Setup

One-time credential provisioning. After this, the skill can manage any zone on the account.

## Prerequisites

- An IONOS account with at least one domain whose DNS is managed by IONOS
- Shell access on the agent host to set environment variables

## 1. Generate an API Key

1. Log in at https://www.ionos.com
2. Go to https://developer.hosting.ionos.com/keys
3. Click **Create key** (or "Generate new API Key")
4. Give it a name (e.g., `claude-code-dns`)
5. Copy both parts of the key immediately — the secret is shown once and cannot be retrieved later:
   - **Public Prefix** — roughly 32 hex characters
   - **Secret** — longer opaque string

## 2. Store the Credentials

### Option A — per-skill `.env` (recommended; matches convention in twenty-crm, mautic, paperclip)

Copy the template and fill it in:

```bash
cd /home/hoyack/Documents/skills/ionos-dns-management
cp .env.example .env
$EDITOR .env   # paste prefix and secret
chmod 600 .env
```

`.env` is already gitignored by the skills-repo root `.gitignore` (the `.env` pattern).

**Load into the current shell before running curl commands:**

```bash
set -a; source /home/hoyack/Documents/skills/ionos-dns-management/.env; set +a
```

`set -a` tells bash to export every variable defined during the source. Without it, the vars are set but not exported, and child processes (like `curl` subprocess environments) won't see them.

Verify:

```bash
echo "${IONOS_API_PREFIX:0:8}..."   # first 8 chars only, sanity check
[ -n "$IONOS_API_SECRET" ] && echo "secret is set" || echo "secret NOT set"
```

### Option B — shell profile (simplest; always-on)

Append to `~/.bashrc` or `~/.zshrc` if you want the creds available in every shell:

```bash
export IONOS_API_PREFIX="<your-prefix>"
export IONOS_API_SECRET="<your-secret>"
```

Then `source ~/.bashrc`. Downside: credentials live in your shell rc and are in `printenv` output.

### Option C — secrets manager

For shared or remote hosts, keep the secret in a vault (1Password, age-encrypted file, etc.) and inject at agent start.

## 3. Verify the Credentials Work

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  https://api.hosting.ionos.com/dns/v1/zones
```

Expected: `200`. If you see `401`, the prefix or secret is wrong.

## 4. Sanity-Check Zone Access

```bash
curl -s -H "X-API-Key: $IONOS_API_PREFIX.$IONOS_API_SECRET" \
  https://api.hosting.ionos.com/dns/v1/zones \
  | python3 -m json.tool | head -40
```

Expect a JSON array of zone objects. If the account has multiple zones, the target domain should appear.

## 5. Rotation

- Rotate the API key every 90 days, or immediately after any suspected leak
- Keys are revoked at https://developer.hosting.ionos.com/keys
- Generating a new key does NOT invalidate the old one — revoke the old key explicitly

## Security Notes

- The key grants full DNS access to the account — treat it like a password
- Never commit the key to a repo, log it, or paste it into shared chat
- The skill reads credentials from env vars exclusively — the skill will never be asked to print them
- If the key is ever exposed in conversation history, rotate immediately
