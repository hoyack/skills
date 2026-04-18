---
name: ionos-imap
version: 0.1.0
description: >
  Read, triage, search, and manage IONOS IMAP mailbox messages.
  Provides structured mail access for OpenClaw agents via MCP tools.
tags: [imap, email, ionos, mail, mcp]
metadata:
  clawdbot:
    emoji: "\U0001F4EC"
    requires:
      bins: [python3]
env:
  IONOS_IMAP_USERNAME:
    description: Full IONOS email address
    required: true
  IONOS_IMAP_PASSWORD:
    description: IONOS IMAP password
    required: true
---

# IONOS IMAP Mail Access

Structured read/triage access to an IONOS IMAP mailbox. Fetches, flags, moves, and searches messages. Does not interpret content — downstream skills (GemSieve, Crew workflows) consume its output.

## MCP Tools Quick Reference

| Tool | Purpose | Speed |
|------|---------|-------|
| `list_folders` | Enumerate mailbox folders | Fast |
| `list_envelopes` | List envelopes (cached, sub-100ms) | Fast |
| `search_envelopes` | Server-side IMAP search | 500ms-5s |
| `read_message` | Full message body + headers + attachments | Medium |
| `get_attachment` | Download attachment to staging dir | Varies |
| `mark_seen` / `mark_unseen` | Toggle read status | Fast |
| `flag` / `unflag` | Toggle flagged status | Fast |
| `move_message` | Move between folders | Fast |
| `delete_message` | Soft (Trash) or hard delete | Fast |
| `watch_status` | IDLE worker health report | Instant |

## Usage Patterns

**Routine polling** — use `list_envelopes`:
```
list_envelopes(folder="INBOX", unseen_only=true, limit=10)
```

**Deep search** — use `search_envelopes`:
```
search_envelopes(from_addr="jane@example.com", date_gte="2026-04-01")
```

**Read then mark** — fetch body without marking read, mark after processing:
```
msg = read_message(folder="INBOX", uid="12847", mark_seen=false)
# ... process message ...
mark_seen(folder="INBOX", uid="12847")
```

## Envelope Schema

```json
{
  "uid": "12847",
  "folder": "INBOX",
  "date": "2026-04-17T09:23:11+00:00",
  "from": {"name": "Jane Doe", "email": "jane@example.com"},
  "to": [{"name": null, "email": "brandon@hoyack.com"}],
  "cc": [],
  "subject": "Proposal follow-up",
  "flags": ["\\Seen"],
  "size_bytes": 24512,
  "has_attachments": true,
  "message_id": "<abc123@example.com>",
  "in_reply_to": "<xyz789@hoyack.com>"
}
```

## Error Codes

| Code | Meaning | Retryable |
|------|---------|-----------|
| `auth_failed` | Bad credentials | No |
| `connection_timeout` | Network unreachable | Yes |
| `imap_protocol_error` | Unexpected server response | Yes (once) |
| `uid_not_found` | Message deleted | No |
| `folder_not_found` | Bad folder name | No |
| `throttled` | IONOS rate-limiting | Yes (long backoff) |
| `attachment_too_large` | Exceeds config limit | No |
