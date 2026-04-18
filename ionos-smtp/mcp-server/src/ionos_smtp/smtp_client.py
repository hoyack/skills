"""SMTP client for IONOS — MIME composition and send via stdlib smtplib."""

from __future__ import annotations

import datetime
import logging
import mimetypes
import os
import re
import smtplib
import ssl
import time
import uuid
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Any

from .config import Config
from .models import (
    Address,
    AttachmentSpec,
    InlineImageSpec,
    SendReceipt,
    SmtpError,
)

log = logging.getLogger(__name__)

# Simple rate limiter — tracks send timestamps in-process
_send_timestamps: list[float] = []


def _check_rate_limit(limit_per_minute: int) -> None:
    """Raise SmtpError if rate limit would be exceeded."""
    now = time.monotonic()
    cutoff = now - 60.0
    # Prune old entries
    while _send_timestamps and _send_timestamps[0] < cutoff:
        _send_timestamps.pop(0)
    if len(_send_timestamps) >= limit_per_minute:
        raise SmtpError(
            "rate_limited",
            f"Rate limit of {limit_per_minute}/min reached. Retry after a few seconds.",
            retryable=True,
        )


def validate_email_address(addr: str) -> tuple[bool, str]:
    """RFC 5322 basic syntax check. No DNS or SMTP probing."""
    if not addr or not isinstance(addr, str):
        return False, "Empty address"
    # Basic pattern — covers the vast majority of real addresses
    pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(pattern, addr):
        return False, "Invalid syntax"
    if len(addr) > 254:
        return False, "Address exceeds 254 characters"
    local, domain = addr.rsplit("@", 1)
    if len(local) > 64:
        return False, "Local part exceeds 64 characters"
    if "." not in domain:
        return False, "Domain has no TLD"
    return True, "Valid"


def _resolve_from(cfg: Config, from_dict: dict | None) -> Address:
    """Resolve the From address, validating against the authenticated account."""
    if from_dict:
        email = from_dict.get("email", cfg.account.default_from_email)
        name = from_dict.get("name", cfg.account.default_from_name)
    else:
        email = cfg.account.default_from_email
        name = cfg.account.default_from_name

    if not email:
        email = cfg.account.username

    # Validate from matches authenticated account
    if email.lower() != cfg.account.username.lower():
        log.warning(
            "From address '%s' differs from authenticated account '%s' — "
            "IONOS may reject this",
            email,
            cfg.account.username,
        )

    return Address(name=name or None, email=email)


def _parse_address_arg(arg: dict | str | None) -> Address | None:
    if arg is None:
        return None
    if isinstance(arg, str):
        return Address(name=None, email=arg)
    return Address(name=arg.get("name"), email=arg["email"])


def _parse_address_list(args: list | None) -> list[Address]:
    if not args:
        return []
    return [
        Address(name=a.get("name") if isinstance(a, dict) else None,
                email=a["email"] if isinstance(a, dict) else a)
        for a in args
    ]


def compose_message(
    cfg: Config,
    from_addr: Address,
    to: list[Address],
    cc: list[Address],
    subject: str,
    text: str | None = None,
    html: str | None = None,
    attachments: list[AttachmentSpec] | None = None,
    inline_images: list[InlineImageSpec] | None = None,
    custom_headers: dict[str, str] | None = None,
    in_reply_to: str | None = None,
    references: list[str] | None = None,
    reply_to: Address | None = None,
    message_id: str | None = None,
) -> tuple[EmailMessage, str]:
    """Compose a MIME message. Returns (EmailMessage, message_id)."""
    if not text and not html:
        raise SmtpError("malformed_message", "Either text or html body is required")

    msg = EmailMessage()
    mid = message_id or make_msgid(domain=from_addr.email.split("@")[-1])

    # Headers
    msg["Message-ID"] = mid
    msg["From"] = formataddr((from_addr.name or "", from_addr.email))
    msg["To"] = ", ".join(formataddr((a.name or "", a.email)) for a in to)
    if cc:
        msg["Cc"] = ", ".join(formataddr((a.name or "", a.email)) for a in cc)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    if reply_to:
        msg["Reply-To"] = formataddr((reply_to.name or "", reply_to.email))
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = " ".join(references)
    if custom_headers:
        for key, value in custom_headers.items():
            msg[key] = value

    # Body
    if text and html:
        msg.set_content(text)
        msg.add_alternative(html, subtype="html")
    elif text:
        msg.set_content(text)
    else:
        msg.set_content(html, subtype="html")

    # Inline images — must be added to the HTML alternative part
    if inline_images and html:
        # Get the HTML part for adding related content
        html_part = None
        if msg.is_multipart():
            for part in msg.iter_parts():
                if part.get_content_type() == "text/html":
                    html_part = part
                    break
        else:
            html_part = msg

        for img in inline_images:
            _validate_attachment_path(img.path)
            maintype, subtype = img.content_type.split("/", 1)
            with open(img.path, "rb") as f:
                data = f.read()
            if html_part and html_part.is_multipart():
                html_part.add_related(
                    data, maintype=maintype, subtype=subtype,
                    cid=f"<{img.cid}>",
                    filename=os.path.basename(img.path),
                )
            else:
                msg.add_related(
                    data, maintype=maintype, subtype=subtype,
                    cid=f"<{img.cid}>",
                    filename=os.path.basename(img.path),
                )

    # Attachments
    if attachments:
        total_size = 0
        max_per = cfg.send.max_attachment_mb * 1024 * 1024
        max_total = cfg.send.max_total_size_mb * 1024 * 1024

        for att in attachments:
            _validate_attachment_path(att.path)
            size = os.path.getsize(att.path)
            if size > max_per:
                raise SmtpError(
                    "message_too_large",
                    f"Attachment '{att.filename}' is {size} bytes, "
                    f"limit is {max_per} bytes ({cfg.send.max_attachment_mb} MB)",
                )
            total_size += size
            if total_size > max_total:
                raise SmtpError(
                    "message_too_large",
                    f"Total attachment size {total_size} bytes exceeds "
                    f"limit of {max_total} bytes ({cfg.send.max_total_size_mb} MB)",
                )

            maintype, subtype = (att.content_type or "application/octet-stream").split("/", 1)
            with open(att.path, "rb") as f:
                data = f.read()
            msg.add_attachment(
                data, maintype=maintype, subtype=subtype,
                filename=att.filename,
            )

    return msg, mid


def _validate_attachment_path(path: str) -> None:
    if not os.path.isfile(path):
        raise SmtpError(
            "attachment_unreadable",
            f"Attachment path does not exist or is not a file: {path}",
        )
    if not os.access(path, os.R_OK):
        raise SmtpError(
            "attachment_unreadable",
            f"Attachment path is not readable: {path}",
        )


def send_smtp(
    cfg: Config,
    msg: EmailMessage,
    to_addrs: list[str],
    bcc_addrs: list[str] | None = None,
) -> tuple[str, list[str], list[str]]:
    """Send via SMTP. Returns (response, accepted, rejected)."""
    _check_rate_limit(cfg.send.rate_limit_per_minute)

    all_recipients = list(to_addrs)
    if bcc_addrs:
        all_recipients.extend(bcc_addrs)

    conn = cfg.connection
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
    except ssl.SSLError as exc:
        raise SmtpError(
            "tls_negotiation_failed",
            f"TLS handshake failed: {exc}",
            retryable=True,
        ) from exc
    except (TimeoutError, OSError) as exc:
        raise SmtpError(
            "connection_timeout",
            f"Connection to {conn.host}:{conn.port} failed: {exc}",
            retryable=True,
        ) from exc

    try:
        smtp.login(cfg.account.username, cfg.account.password)
    except smtplib.SMTPAuthenticationError as exc:
        smtp.quit()
        raise SmtpError("auth_failed", f"SMTP auth failed: {exc}") from exc

    rejected: dict[str, Any] = {}
    response = ""
    try:
        result = smtp.send_message(msg, to_addrs=all_recipients)
        rejected = result  # dict of {addr: (code, msg)} for rejects
        response = "250 2.0.0 Ok"
    except smtplib.SMTPRecipientsRefused as exc:
        rejected = exc.recipients
        response = "550 All recipients rejected"
    except smtplib.SMTPDataError as exc:
        smtp.quit()
        raise SmtpError(
            "message_too_large",
            f"SMTP data error (possibly message too large): {exc}",
        ) from exc
    finally:
        try:
            smtp.quit()
        except Exception:
            pass

    _send_timestamps.append(time.monotonic())

    accepted = [a for a in all_recipients if a not in rejected]
    rejected_list = list(rejected.keys())

    if not accepted and rejected_list:
        raise SmtpError(
            "recipient_rejected",
            f"All recipients rejected: {rejected}",
        )

    return response, accepted, rejected_list


def build_reply_subject(original_subject: str) -> str:
    """Add 'Re: ' prefix, handling existing prefixes correctly."""
    # Strip existing Re: / Re[N]: prefixes
    cleaned = re.sub(r'^(Re:\s*|Re\[\d+\]:\s*)+', '', original_subject, flags=re.IGNORECASE)
    return f"Re: {cleaned}"


def build_quoted_text(
    original_text: str,
    original_from: str,
    original_date: str,
) -> str:
    """Build standard quoted reply text."""
    header = f"\nOn {original_date}, {original_from} wrote:\n"
    quoted = "\n".join(f"> {line}" for line in original_text.splitlines())
    return header + quoted + "\n"


def build_quoted_html(
    original_html: str,
    original_from: str,
    original_date: str,
) -> str:
    """Build quoted reply HTML with blockquote."""
    return (
        f'<br/><div style="padding-left:1em;border-left:2px solid #ccc;color:#555">'
        f'<p>On {original_date}, {original_from} wrote:</p>'
        f'{original_html}'
        f'</div>'
    )
