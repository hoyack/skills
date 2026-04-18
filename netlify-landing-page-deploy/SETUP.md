# Netlify MCP Setup

One-time setup to make the Netlify MCP server available to Claude Code / OpenClaw. After this, the `netlify-landing-page-deploy` skill can drive deploys end-to-end.

## Prerequisites

- **Node.js ≥ 22** on the host running the MCP server (`node -v` to check)
- **Netlify account** with a Personal Access Token (PAT)
- **GitHub account** linked to the Netlify account (for git-based deploys)

## 1. Create a Netlify Personal Access Token

1. Log in at https://app.netlify.com
2. Click your avatar (top-right) → **User settings**
3. Left sidebar → **Applications** → **Personal access tokens**
4. Click **New access token**
5. Description: `Claude Code MCP` (or similar)
6. Expiration: choose per your policy (no expiration is acceptable for a local dev box; set one for shared/remote hosts)
7. Click **Generate token** and copy the value immediately — it won't be shown again

## 2. Enable Form Detection

Required for contact forms deployed by this skill:

1. https://app.netlify.com → select (or create) the target team
2. **Team settings** → **Forms** → ensure form detection is enabled at the team level
3. Per-site form detection is on by default for new sites once the team setting is on

## 3. Register the MCP Server

Install the MCP server globally (the package's bin is `netlify-mcp`, and `npx -y @netlify/mcp` does NOT resolve to it correctly — use the global install):

```bash
npm install -g @netlify/mcp
```

Then add to `~/.mcp.json` (merge with existing `mcpServers` object — do not overwrite):

```json
{
  "mcpServers": {
    "netlify": {
      "command": "netlify-mcp",
      "env": {
        "NETLIFY_PERSONAL_ACCESS_TOKEN": "<paste-PAT-here>"
      }
    }
  }
}
```

Then restart Claude Code so the MCP server loads at startup.

## 4. Verify

After restart, the agent should have access to tools prefixed `mcp__netlify__*`. A quick sanity check:

- Ask the agent to list your Netlify sites
- Or invoke a list/read tool (e.g., `netlify-deploy-services` list) and confirm a response

If tools are missing:

- Check `node -v` ≥ 22 on the host
- Run `npx -y @netlify/mcp` manually and confirm it starts without error
- Confirm the PAT is valid: `curl -H "Authorization: Bearer <PAT>" https://api.netlify.com/api/v1/sites | head`
- Check `~/.mcp.json` is valid JSON and has no trailing commas

## 5. GitHub Integration (for git-based deploys)

The skill's Phase 4 pushes to a GitHub repo that Netlify then deploys from. For this to work:

1. Netlify account must have the GitHub app installed: https://app.netlify.com → **Sites** → **Add new site** → **Import from Git** (first run installs the GitHub app)
2. Grant access to the repos (or org) that will host landing pages
3. The local agent host must have `git` installed and a working credential helper (HTTPS token or SSH key) so it can push to the target repo

## Security Notes

- Treat the PAT like a password — it grants full API access to your Netlify account
- Do NOT commit `~/.mcp.json` or any file containing the PAT
- Rotate the PAT via https://app.netlify.com → User settings → Applications if it's ever exposed
- Prefer team-scoped tokens when the product supports it (as of this writing, Netlify PATs are user-scoped)
