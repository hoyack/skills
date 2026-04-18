# IONOS SMTP — Setup Guide

## Prerequisites

- Python 3.11+
- IONOS email account with SMTP access
- pip or uv for package management
- (Optional) IONOS IMAP skill installed for send_reply and APPEND-to-Sent
- (Optional) RabbitMQ for queue mode

## 1. Install

```bash
cd /home/hoyack/Documents/skills/ionos-smtp/mcp-server
pip install -e .
```

With queue mode support:
```bash
pip install -e ".[rabbitmq]"
```

## 2. Configure Credentials

Set environment variables:
```bash
export IONOS_SMTP_USERNAME="your-email@yourdomain.com"
export IONOS_SMTP_PASSWORD="your-smtp-password"
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## 3. Optional: TOML Config

For advanced settings (from address, rate limits, queue mode):
```bash
mkdir -p ~/.config/openclaw
cp config/ionos-smtp.toml.example ~/.config/openclaw/ionos-smtp.toml
# Edit as needed
```

## 4. MCP Server Registration

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "ionos-smtp": {
      "command": "ionos-smtp-mcp",
      "env": {
        "IONOS_SMTP_USERNAME": "your-email@yourdomain.com",
        "IONOS_SMTP_PASSWORD": "your-smtp-password"
      }
    }
  }
}
```

Or from source:
```json
{
  "mcpServers": {
    "ionos-smtp": {
      "command": "python",
      "args": ["/home/hoyack/Documents/skills/ionos-smtp/mcp-server/src/ionos_smtp/server.py"],
      "env": {
        "IONOS_SMTP_USERNAME": "your-email@yourdomain.com",
        "IONOS_SMTP_PASSWORD": "your-smtp-password"
      }
    }
  }
}
```

## 5. Queue Worker (Optional — Phase 3)

Only needed if using `queue_message` for async/bulk sends.

### Enable queue mode:
In `~/.config/openclaw/ionos-smtp.toml`:
```toml
[queue]
enabled = true
rabbitmq_uri = "amqp://localhost"
```

### Manual start:
```bash
ionos-smtp-worker
```

### systemd user service:
```bash
mkdir -p ~/.config/systemd/user
cp worker/openclaw-smtp-worker.service ~/.config/systemd/user/

# Create env file
mkdir -p ~/.config/openclaw
cat > ~/.config/openclaw/ionos-smtp.env << 'EOF'
IONOS_SMTP_USERNAME=your-email@yourdomain.com
IONOS_SMTP_PASSWORD=your-smtp-password
EOF
chmod 600 ~/.config/openclaw/ionos-smtp.env

systemctl --user daemon-reload
systemctl --user enable --now openclaw-smtp-worker.service
```

## 6. Verify

Test connectivity without sending:
```bash
ionos-smtp-mcp  # starts in stdio mode
```

From an agent, call `test_connection` to verify auth and TLS.

## 7. Deliverability (DNS)

For messages to avoid spam filters, configure DNS records on the sending domain:
- **SPF:** include `_spf.perfora.net` and `_spf.kundenserver.de`
- **DKIM:** enable in IONOS control panel, publish CNAME records
- **DMARC:** publish policy record after SPF/DKIM validate

Use the `ionos-dns-management` skill to provision these records.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `auth_failed` | Verify credentials match IONOS email login |
| `tls_negotiation_failed` | Try switching `tls_mode` between `implicit` (465) and `starttls` (587) |
| `rate_limited` | Reduce `rate_limit_per_minute` in config or use queue mode |
| Sent mail not in webmail | Ensure `default_append_to_sent = true` and IMAP skill is installed |
| `send_reply` fails | Requires IMAP skill installed and configured |
| Queue worker can't connect | Check RabbitMQ is running and URI is correct |
