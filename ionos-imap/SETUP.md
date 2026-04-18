# IONOS IMAP — Setup Guide

## Prerequisites

- Python 3.11+
- IONOS email account with IMAP access enabled
- pip or uv for package management

## 1. Install

```bash
cd /home/hoyack/Documents/skills/ionos-imap/mcp-server
pip install -e .
```

Or with uv:
```bash
uv pip install -e .
```

## 2. Configure Credentials

Set environment variables:
```bash
export IONOS_IMAP_USERNAME="your-email@yourdomain.com"
export IONOS_IMAP_PASSWORD="your-imap-password"
```

Or create a `.env` file from the template:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## 3. Optional: TOML Config

For advanced settings (watched folders, attachment limits, RabbitMQ):
```bash
mkdir -p ~/.config/openclaw
cp config/ionos-imap.toml.example ~/.config/openclaw/ionos-imap.toml
# Edit as needed
```

## 4. MCP Server Registration

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "ionos-imap": {
      "command": "ionos-imap-mcp",
      "env": {
        "IONOS_IMAP_USERNAME": "your-email@yourdomain.com",
        "IONOS_IMAP_PASSWORD": "your-imap-password"
      }
    }
  }
}
```

Or if running from source:
```json
{
  "mcpServers": {
    "ionos-imap": {
      "command": "python",
      "args": ["/home/hoyack/Documents/skills/ionos-imap/mcp-server/src/ionos_imap/server.py"],
      "env": {
        "IONOS_IMAP_USERNAME": "your-email@yourdomain.com",
        "IONOS_IMAP_PASSWORD": "your-imap-password"
      }
    }
  }
}
```

## 5. IDLE Worker (Phase 2)

The IDLE worker maintains a persistent connection for near-instant new-mail detection.

### Manual start:
```bash
ionos-imap-worker
```

### systemd user service:
```bash
# Copy service file
mkdir -p ~/.config/systemd/user
cp worker/openclaw-imap-worker.service ~/.config/systemd/user/

# Create env file with credentials
mkdir -p ~/.config/openclaw
cat > ~/.config/openclaw/ionos-imap.env << 'EOF'
IONOS_IMAP_USERNAME=your-email@yourdomain.com
IONOS_IMAP_PASSWORD=your-imap-password
EOF
chmod 600 ~/.config/openclaw/ionos-imap.env

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now openclaw-imap-worker.service

# Check status
systemctl --user status openclaw-imap-worker.service
journalctl --user -u openclaw-imap-worker.service -f
```

## 6. Verify

Test the MCP server:
```bash
ionos-imap-mcp  # starts in stdio mode, Ctrl+C to stop
```

Test from an agent — call `list_folders` to verify connectivity.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `auth_failed` | Verify credentials; IONOS may require app-specific password |
| `connection_timeout` | Check network; verify `imap.ionos.com:993` is reachable |
| Worker keeps restarting | Check `journalctl --user -u openclaw-imap-worker` for errors |
| Stale envelopes after folder reorganization | UIDVALIDITY change triggers auto-resync on next connect |
