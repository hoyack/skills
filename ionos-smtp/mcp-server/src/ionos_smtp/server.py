"""IONOS SMTP MCP server — exposes send tools to OpenClaw agents."""

from __future__ import annotations

import argparse
import datetime
import logging
import smtplib
import ssl
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from .config import Config, load_config
from .models import (
    Address,
    AttachmentSpec,
    InlineImageSpec,
    SendReceipt,
    SmtpError,
)
from .smtp_client import (
    build_quoted_html,
    build_quoted_text,
    build_reply_subject,
    compose_message,
    send_smtp,
    validate_email_address,
    _parse_address_arg,
    _parse_address_list,
    _resolve_from,
)
from .state import StateStore

load_dotenv()
log = logging.getLogger(__name__)

_cfg: Config | None = None
_state: StateStore | None = None


def _validate_config(cfg: Config) -> None:
    if not cfg.account.username:
        print(
            "ERROR: IONOS_SMTP_USERNAME not set. "
            "Set it via env var or in ionos-smtp.toml",
            file=sys.stderr,
        )
        sys.exit(1)
    if not cfg.account.password:
        print(
            "ERROR: IONOS_SMTP_PASSWORD not set. "
            "Set it via env var or in ionos-smtp.toml",
            file=sys.stderr,
        )
        sys.exit(1)


@asynccontextmanager
async def _lifespan(server: FastMCP):
    global _cfg, _state
    _cfg = load_config()
    _validate_config(_cfg)
    _state = StateStore(_cfg.state.sqlite_path)
    log.info(
        "ionos-smtp MCP server started — host=%s user=%s",
        _cfg.connection.host,
        _cfg.account.username,
    )
    yield
    if _state:
        _state.close()
    log.info("ionos-smtp MCP server stopped")


mcp = FastMCP(
    name="ionos-smtp",
    instructions=(
        "IONOS SMTP mail send. Use send_message for one-off emails. "
        "Use send_reply to reply to an existing message with correct threading. "
        "Use queue_message for bulk/retry-needed sends. "
        "Always call test_connection first if unsure about credentials."
    ),
    lifespan=_lifespan,
)


def _error_response(e: SmtpError) -> dict[str, Any]:
    return e.to_dict()


# --- Tools ---


@mcp.tool()
async def send_message(
    to: list[dict],
    subject: str,
    text: str | None = None,
    html: str | None = None,
    from_addr: dict | None = None,
    cc: list[dict] | None = None,
    bcc: list[dict] | None = None,
    reply_to: dict | None = None,
    attachments: list[dict] | None = None,
    inline_images: list[dict] | None = None,
    custom_headers: dict[str, str] | None = None,
    in_reply_to: str | None = None,
    references: list[str] | None = None,
    append_to_sent: bool | None = None,
) -> dict:
    """Compose and send an email synchronously.

    Args:
        to: Recipients — list of {name, email} dicts
        subject: Email subject line
        text: Plain text body (text or html required)
        html: HTML body (text or html required)
        from_addr: Sender {name, email} — defaults to configured account
        cc: CC recipients
        bcc: BCC recipients (envelope only, not in headers)
        reply_to: Reply-To address {name, email}
        attachments: List of {path, filename, content_type}
        inline_images: List of {path, cid, content_type} — ref in HTML as cid:name
        custom_headers: Arbitrary headers like {"X-Campaign-Id": "abc"}
        in_reply_to: Message-ID for threading
        references: List of Message-IDs for threading
        append_to_sent: Copy to IMAP Sent folder (default from config)
    """
    try:
        from_resolved = _resolve_from(_cfg, from_addr)
        to_addrs = _parse_address_list(to)
        cc_addrs = _parse_address_list(cc)
        bcc_addrs = _parse_address_list(bcc)
        reply_to_addr = _parse_address_arg(reply_to)

        if not to_addrs:
            raise SmtpError("malformed_message", "At least one recipient required in 'to'")

        att_specs = [
            AttachmentSpec(path=a["path"], filename=a.get("filename", ""), content_type=a.get("content_type", "application/octet-stream"))
            for a in (attachments or [])
        ]
        img_specs = [
            InlineImageSpec(path=i["path"], cid=i["cid"], content_type=i.get("content_type", "image/png"))
            for i in (inline_images or [])
        ]

        msg, mid = compose_message(
            _cfg,
            from_addr=from_resolved,
            to=to_addrs,
            cc=cc_addrs,
            subject=subject,
            text=text,
            html=html,
            attachments=att_specs or None,
            inline_images=img_specs or None,
            custom_headers=custom_headers,
            in_reply_to=in_reply_to,
            references=references,
            reply_to=reply_to_addr,
        )

        all_to = [a.email for a in to_addrs + cc_addrs]
        bcc_emails = [a.email for a in bcc_addrs]

        response, accepted, rejected = send_smtp(_cfg, msg, all_to, bcc_emails)

        should_append = append_to_sent if append_to_sent is not None else _cfg.send.default_append_to_sent
        appended = False
        if should_append and _cfg.imap_integration.enabled:
            appended = _append_to_sent(msg)

        receipt = SendReceipt(
            ok=True,
            message_id=mid,
            accepted_recipients=accepted,
            rejected_recipients=rejected,
            smtp_response=response,
            sent_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            appended_to_sent=appended,
        )
        return receipt.to_dict()

    except SmtpError as e:
        return _error_response(e)


@mcp.tool()
async def send_reply(
    folder: str,
    uid: str,
    text: str | None = None,
    html: str | None = None,
    reply_all: bool = False,
    quote_original: bool = True,
    attachments: list[dict] | None = None,
    append_to_sent: bool | None = None,
) -> dict:
    """Reply to an existing message with correct threading headers.

    Fetches the original via IMAP, builds In-Reply-To/References/Re: subject,
    optionally quotes original content.

    Args:
        folder: IMAP folder containing the original message
        uid: UID of the original message
        text: Reply text body
        html: Reply HTML body
        reply_all: If true, include all original recipients
        quote_original: If true (default), prepend quoted original content
        attachments: Attachments for the reply
        append_to_sent: Copy to IMAP Sent folder
    """
    if not _cfg.imap_integration.enabled:
        return {"error": "imap_not_configured", "message": "send_reply requires IMAP integration to be enabled"}

    try:
        # Fetch original message via IMAP skill
        original = _fetch_original_message(folder, uid)
        if not original:
            return {"error": "uid_not_found", "message": f"Could not fetch original message {uid} from {folder}"}

        orig_envelope = original.get("envelope", {})
        orig_from = orig_envelope.get("from", {})
        orig_to = orig_envelope.get("to", [])
        orig_cc = orig_envelope.get("cc", [])
        orig_subject = orig_envelope.get("subject", "")
        orig_message_id = orig_envelope.get("message_id", "")
        orig_date = orig_envelope.get("date", "")

        # Build threading headers
        new_subject = build_reply_subject(orig_subject)
        new_in_reply_to = orig_message_id
        new_references = []
        if original.get("headers", {}).get("references"):
            existing_refs = original["headers"]["references"].split()
            new_references = existing_refs
        if orig_message_id and orig_message_id not in new_references:
            new_references.append(orig_message_id)

        # Resolve recipients
        from_resolved = _resolve_from(_cfg, None)
        my_email = from_resolved.email.lower()

        if reply_all:
            # To: original From + original To (minus self)
            to_addrs = [Address(name=orig_from.get("name"), email=orig_from["email"])]
            for a in orig_to:
                if a.get("email", "").lower() != my_email:
                    to_addrs.append(Address(name=a.get("name"), email=a["email"]))
            # Cc: original Cc (minus self)
            cc_addrs = [
                Address(name=a.get("name"), email=a["email"])
                for a in orig_cc
                if a.get("email", "").lower() != my_email
            ]
        else:
            to_addrs = [Address(name=orig_from.get("name"), email=orig_from["email"])]
            cc_addrs = []

        # Quote original content
        reply_text = text or ""
        reply_html = html

        if quote_original:
            orig_from_str = orig_from.get("name") or orig_from.get("email", "")
            if original.get("text"):
                quoted = build_quoted_text(original["text"], orig_from_str, orig_date)
                reply_text = reply_text + quoted
            if reply_html and original.get("html"):
                reply_html = reply_html + build_quoted_html(
                    original["html"], orig_from_str, orig_date
                )

        att_specs = [
            AttachmentSpec(path=a["path"], filename=a.get("filename", ""), content_type=a.get("content_type", "application/octet-stream"))
            for a in (attachments or [])
        ]

        msg, mid = compose_message(
            _cfg,
            from_addr=from_resolved,
            to=to_addrs,
            cc=cc_addrs,
            subject=new_subject,
            text=reply_text or None,
            html=reply_html,
            attachments=att_specs or None,
            in_reply_to=new_in_reply_to,
            references=new_references,
        )

        all_to = [a.email for a in to_addrs + cc_addrs]
        response, accepted, rejected = send_smtp(_cfg, msg, all_to)

        should_append = append_to_sent if append_to_sent is not None else _cfg.send.default_append_to_sent
        appended = False
        if should_append and _cfg.imap_integration.enabled:
            appended = _append_to_sent(msg)

        receipt = SendReceipt(
            ok=True,
            message_id=mid,
            accepted_recipients=accepted,
            rejected_recipients=rejected,
            smtp_response=response,
            sent_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            appended_to_sent=appended,
        )
        return receipt.to_dict()

    except SmtpError as e:
        return _error_response(e)


@mcp.tool()
async def queue_message(
    to: list[dict],
    subject: str,
    text: str | None = None,
    html: str | None = None,
    from_addr: dict | None = None,
    cc: list[dict] | None = None,
    bcc: list[dict] | None = None,
    attachments: list[dict] | None = None,
    custom_headers: dict[str, str] | None = None,
    priority: int = 0,
) -> dict:
    """Enqueue a message for async send via the queue worker.

    Requires queue mode enabled in config. Use for bulk sends or when
    retry-on-failure is needed.

    Args:
        to: Recipients
        subject: Subject line
        text: Plain text body
        html: HTML body
        from_addr: Sender override
        cc: CC recipients
        bcc: BCC recipients
        attachments: List of {path, filename, content_type}
        custom_headers: Arbitrary headers
        priority: Queue priority (higher = sooner, default 0)
    """
    if not _cfg.queue.enabled:
        return {"error": "queue_not_enabled", "message": "Queue mode is not enabled in config"}

    queue_id = str(uuid.uuid4())
    payload = {
        "to": to,
        "subject": subject,
        "text": text,
        "html": html,
        "from_addr": from_addr,
        "cc": cc,
        "bcc": bcc,
        "attachments": attachments,
        "custom_headers": custom_headers,
        "priority": priority,
    }

    try:
        _state.create_outbound(queue_id, payload)
        _publish_to_queue(queue_id, payload)

        return {
            "queue_id": queue_id,
            "queued_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "status": "pending",
        }
    except Exception as e:
        return {"error": "queue_error", "message": str(e)}


@mcp.tool()
async def queue_status(queue_id: str) -> dict:
    """Query the send status of a queued message.

    Args:
        queue_id: The queue ID returned by queue_message
    """
    result = _state.get_outbound(queue_id)
    if not result:
        return {"error": "not_found", "message": f"Queue ID {queue_id} not found"}
    return result


@mcp.tool()
async def test_connection() -> dict:
    """Test SMTP connectivity and authentication without sending.

    Returns server banner, auth mechanisms, and TLS version.
    """
    conn = _cfg.connection
    try:
        if conn.tls_mode == "implicit":
            ctx = ssl.create_default_context()
            smtp = smtplib.SMTP_SSL(
                host=conn.host, port=conn.port,
                context=ctx, timeout=conn.timeout_seconds,
            )
        else:
            smtp = smtplib.SMTP(
                host=conn.host, port=conn.port,
                timeout=conn.timeout_seconds,
            )
            ctx = ssl.create_default_context()
            smtp.starttls(context=ctx)

        banner = smtp.ehlo_resp.decode() if smtp.ehlo_resp else "unknown"
        tls_info = "unknown"
        if hasattr(smtp, "sock") and smtp.sock:
            ssl_sock = smtp.sock
            if hasattr(ssl_sock, "version"):
                tls_info = ssl_sock.version() or "unknown"

        smtp.login(_cfg.account.username, _cfg.account.password)
        smtp.quit()

        return {
            "ok": True,
            "server_banner": banner[:200],
            "tls_version": tls_info,
            "host": conn.host,
            "port": conn.port,
            "tls_mode": conn.tls_mode,
        }
    except smtplib.SMTPAuthenticationError as exc:
        return {"ok": False, "error": "auth_failed", "message": str(exc)}
    except ssl.SSLError as exc:
        return {"ok": False, "error": "tls_negotiation_failed", "message": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": "connection_timeout", "message": str(exc)}


@mcp.tool()
async def validate_addresses(addresses: list[str]) -> list[dict]:
    """Validate email address syntax (RFC 5322). No DNS or SMTP probing.

    Args:
        addresses: List of email addresses to validate
    """
    results = []
    for addr in addresses:
        valid, reason = validate_email_address(addr)
        results.append({"address": addr, "valid": valid, "reason": reason})
    return results


# --- Internal helpers ---


def _fetch_original_message(folder: str, uid: str) -> dict | None:
    """Fetch an original message via the IMAP skill for reply threading.

    This imports and uses the IMAP client directly since both skills
    share the same credential store and run on the same host.
    """
    try:
        from ionos_imap.config import load_config as load_imap_config
        from ionos_imap.imap_client import ImapClient

        imap_cfg = load_imap_config()
        client = ImapClient(imap_cfg)
        return client.read_message(folder, uid, mark_seen=False)
    except ImportError:
        log.warning("IMAP skill not installed — send_reply cannot fetch original")
        return None
    except Exception as exc:
        log.error("Failed to fetch original message: %s", exc)
        return None


def _append_to_sent(msg) -> bool:
    """Append sent message to IMAP Sent folder."""
    try:
        from ionos_imap.config import load_config as load_imap_config
        from ionos_imap.imap_client import ImapClient

        import imaplib

        imap_cfg = load_imap_config()
        conn_cfg = imap_cfg.connection

        ctx = ssl.create_default_context() if conn_cfg.use_tls else None
        imap = imaplib.IMAP4_SSL(
            host=conn_cfg.host, port=conn_cfg.port, ssl_context=ctx
        )
        imap.login(imap_cfg.account.username, imap_cfg.account.password)

        sent_folder = _cfg.send.sent_folder_name
        result = imap.append(
            sent_folder,
            "\\Seen",
            imaplib.Time2Internaldate(datetime.datetime.now()),
            msg.as_bytes(),
        )
        imap.logout()

        ok = result[0] == "OK"
        if not ok:
            log.warning("IMAP APPEND to %s failed: %s", sent_folder, result)
        return ok

    except ImportError:
        log.warning("IMAP skill not installed — skipping APPEND to Sent")
        return False
    except Exception as exc:
        log.warning("APPEND to Sent failed (send succeeded): %s", exc)
        return False


def _publish_to_queue(queue_id: str, payload: dict) -> None:
    """Publish a send job to RabbitMQ."""
    import json

    try:
        import pika

        params = pika.URLParameters(_cfg.queue.rabbitmq_uri)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=_cfg.queue.queue_name, durable=True)

        body = json.dumps({"queue_id": queue_id, **payload})
        channel.basic_publish(
            exchange="",
            routing_key=_cfg.queue.queue_name,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2),  # persistent
        )
        connection.close()
    except ImportError:
        log.error("pika not installed — install ionos-smtp-mcp[rabbitmq]")
        raise
    except Exception as exc:
        log.error("Failed to publish to queue: %s", exc)
        raise


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="IONOS SMTP MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
