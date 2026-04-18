---
name: ionos-smtp
version: 0.1.0
description: >
  Compose and send email via IONOS SMTP with attachments, threading,
  inline images, and optional queue-based async delivery.
tags: [smtp, email, ionos, mail, mcp, send]
metadata:
  clawdbot:
    emoji: "\U0001F4E4"
    requires:
      bins: [python3]
env:
  IONOS_SMTP_USERNAME:
    description: Full IONOS email address
    required: true
  IONOS_SMTP_PASSWORD:
    description: IONOS SMTP password
    required: true
---

# IONOS SMTP Mail Send

Outbound mail capability through IONOS SMTP. Composes MIME messages, authenticates, handles attachments and inline images, and optionally queues for retry. Does not generate content — upstream skills produce the message payload.

Composes with the IONOS IMAP skill: sent messages are APPENDed to the IMAP Sent folder so the mailbox reflects reality across clients.

## MCP Tools Quick Reference

| Tool | Purpose | Mode |
|------|---------|------|
| `send_message` | Compose and send synchronously | Sync |
| `send_reply` | Reply with correct threading headers | Sync |
| `queue_message` | Enqueue for async send (requires queue mode) | Async |
| `queue_status` | Query send status by queue ID | Query |
| `test_connection` | Verify auth + TLS without sending | Query |
| `validate_addresses` | RFC 5322 syntax check | Query |

## Usage Patterns

**Simple send:**
```
send_message(
    to=[{"name": "Jane", "email": "jane@example.com"}],
    subject="Hello",
    text="Plain text body",
    html="<p>HTML body</p>"
)
```

**Reply with threading:**
```
send_reply(
    folder="INBOX",
    uid="12847",
    text="Thanks for following up!",
    reply_all=false,
    quote_original=true
)
```

**Bulk send via queue:**
```
queue_message(
    to=[{"email": "prospect@company.com"}],
    subject="Proposal",
    html="<p>See attached.</p>",
    attachments=[{"path": "/tmp/proposal.pdf", "filename": "Proposal.pdf", "content_type": "application/pdf"}],
    custom_headers={"X-Campaign-Id": "abm-2026-q2"}
)
```

## Send Receipt Schema

```json
{
  "ok": true,
  "message_id": "<generated-uuid@hoyack.com>",
  "accepted_recipients": ["jane@example.com"],
  "rejected_recipients": [],
  "smtp_response": "250 2.0.0 Ok: queued",
  "sent_at": "2026-04-17T14:22:10+00:00",
  "appended_to_sent": true
}
```

## Error Codes

| Code | Meaning | Retryable |
|------|---------|-----------|
| `auth_failed` | Bad SMTP credentials | No |
| `connection_timeout` | Network unreachable | Yes |
| `tls_negotiation_failed` | TLS handshake error | Yes (once) |
| `recipient_rejected` | 550 from server | Partial — check `rejected_recipients` |
| `message_too_large` | Exceeds size limit | No |
| `rate_limited` | Local or remote rate limit | Yes |
| `malformed_message` | Invalid MIME input | No |
| `attachment_unreadable` | Path not found / not readable | No |

## IMAP Integration

- **send_reply** fetches the original message via the IMAP skill for threading
- **APPEND to Sent** copies sent messages to the IMAP Sent folder
- Both features are configurable — skill works without IMAP at reduced capability

## Security

- Credentials never logged or returned in tool output
- Password sent only over established TLS
- From address validated against authenticated account
- BCC stripped from headers, delivered via envelope only
