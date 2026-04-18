"""IMAP client wrapper around imap-tools for IONOS mailbox access."""

from __future__ import annotations

import datetime
import logging
import ssl
from contextlib import contextmanager
from typing import Generator

from imap_tools import AND, MailBox, MailboxLoginError, MailMessage

from .config import Config
from .models import Address, AttachmentMeta, Envelope, FullMessage, ImapError

log = logging.getLogger(__name__)


def _parse_address(addr_tuple: tuple[str, str] | None) -> Address:
    if addr_tuple is None:
        return Address(name=None, email="")
    name, email = addr_tuple
    return Address(name=name or None, email=email)


def _parse_addresses(addrs: tuple) -> list[Address]:
    return [Address(name=a.name or None, email=a.email) for a in addrs]


def _msg_to_envelope(msg: MailMessage, folder: str) -> Envelope:
    from_addr = Address(
        name=msg.from_values.name or None if msg.from_values else None,
        email=msg.from_values.email if msg.from_values else "",
    )
    return Envelope(
        uid=msg.uid,
        folder=folder,
        date=msg.date or datetime.datetime.now(tz=datetime.timezone.utc),
        from_addr=from_addr,
        to=_parse_addresses(msg.to_values),
        cc=_parse_addresses(msg.cc_values),
        subject=msg.subject or "",
        flags=list(msg.flags),
        size_bytes=msg.size,
        has_attachments=len(msg.attachments) > 0,
        message_id=msg.headers.get("message-id", [""])[0],
        in_reply_to=msg.headers.get("in-reply-to", [None])[0],
    )


def _msg_to_full(msg: MailMessage, folder: str) -> FullMessage:
    envelope = _msg_to_envelope(msg, folder)
    attachments = [
        AttachmentMeta(
            index=i,
            filename=att.filename or f"attachment_{i}",
            content_type=att.content_type or "application/octet-stream",
            size=att.size,
        )
        for i, att in enumerate(msg.attachments)
    ]
    # Flatten headers to single values for the common case
    headers = {k: v[0] if len(v) == 1 else "; ".join(v) for k, v in msg.headers.items()}
    return FullMessage(
        envelope=envelope,
        text=msg.text or None,
        html=msg.html or None,
        headers=headers,
        attachments=attachments,
    )


class ImapClient:
    """Manages short-lived IMAP connections to IONOS."""

    def __init__(self, cfg: Config):
        self._cfg = cfg

    @contextmanager
    def _connect(self, folder: str = "INBOX") -> Generator[MailBox, None, None]:
        """Open an authenticated IMAP connection to the given folder."""
        acct = self._cfg.account
        conn = self._cfg.connection
        if not acct.username or not acct.password:
            raise ImapError("auth_failed", "IMAP credentials not configured")

        ssl_ctx = ssl.create_default_context() if conn.use_tls else None
        try:
            mb = MailBox(
                host=conn.host,
                port=conn.port,
                ssl_context=ssl_ctx,
                timeout=conn.timeout_seconds,
            )
            mb.login(acct.username, acct.password, initial_folder=folder)
        except MailboxLoginError as exc:
            raise ImapError("auth_failed", f"Login failed: {exc}") from exc
        except TimeoutError as exc:
            raise ImapError(
                "connection_timeout",
                f"Connection to {conn.host}:{conn.port} timed out",
                retryable=True,
            ) from exc
        except Exception as exc:
            raise ImapError(
                "connection_timeout",
                f"Connection failed: {exc}",
                retryable=True,
            ) from exc

        try:
            yield mb
        finally:
            try:
                mb.logout()
            except Exception:
                pass

    def list_folders(self) -> list[dict]:
        with self._connect() as mb:
            folders = []
            for f in mb.folder.list():
                folders.append({
                    "name": f.name,
                    "delimiter": f.delim,
                    "flags": list(f.flags) if f.flags else [],
                })
            return folders

    def list_envelopes(
        self,
        folder: str = "INBOX",
        since: datetime.datetime | None = None,
        unseen_only: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        criteria = AND()
        if since:
            criteria = AND(date_gte=since.date())
        if unseen_only:
            criteria = AND(criteria, seen=False) if since else AND(seen=False)

        with self._connect(folder) as mb:
            msgs = list(mb.fetch(criteria, limit=limit, reverse=True, headers_only=True))
            return [_msg_to_envelope(m, folder).to_dict() for m in msgs]

    def search_envelopes(
        self,
        folder: str = "INBOX",
        from_addr: str | None = None,
        to_addr: str | None = None,
        subject_contains: str | None = None,
        body_contains: str | None = None,
        date_gte: datetime.datetime | None = None,
        date_lte: datetime.datetime | None = None,
        flags: list[str] | None = None,
    ) -> list[dict]:
        parts = []
        if from_addr:
            parts.append(AND(from_=from_addr))
        if to_addr:
            parts.append(AND(to=to_addr))
        if subject_contains:
            parts.append(AND(subject=subject_contains))
        if body_contains:
            parts.append(AND(body=body_contains))
        if date_gte:
            parts.append(AND(date_gte=date_gte.date()))
        if date_lte:
            parts.append(AND(date_lt=date_lte.date()))
        if flags:
            if "\\Seen" in flags:
                parts.append(AND(seen=True))
            if "\\Flagged" in flags:
                parts.append(AND(flagged=True))

        criteria = AND(*parts) if parts else AND()

        with self._connect(folder) as mb:
            msgs = list(mb.fetch(criteria, reverse=True, headers_only=True))
            return [_msg_to_envelope(m, folder).to_dict() for m in msgs]

    def read_message(
        self,
        folder: str,
        uid: str,
        mark_seen: bool = False,
    ) -> dict:
        with self._connect(folder) as mb:
            msgs = list(mb.fetch(AND(uid=uid), mark_seen=mark_seen))
            if not msgs:
                raise ImapError("uid_not_found", f"UID {uid} not found in {folder}")
            return _msg_to_full(msgs[0], folder).to_dict()

    def get_attachment(
        self,
        folder: str,
        uid: str,
        attachment_index: int,
        target_path: str | None = None,
    ) -> dict:
        import os

        with self._connect(folder) as mb:
            msgs = list(mb.fetch(AND(uid=uid), mark_seen=False))
            if not msgs:
                raise ImapError("uid_not_found", f"UID {uid} not found in {folder}")

            msg = msgs[0]
            atts = list(msg.attachments)
            if attachment_index >= len(atts):
                raise ImapError(
                    "uid_not_found",
                    f"Attachment index {attachment_index} out of range (message has {len(atts)} attachments)",
                )

            att = atts[attachment_index]

            # Check size limit
            max_bytes = self._cfg.attachments.max_size_mb * 1024 * 1024
            if att.size > max_bytes:
                raise ImapError(
                    "attachment_too_large",
                    f"Attachment {att.filename} is {att.size} bytes, limit is {max_bytes}",
                )

            staging = self._cfg.attachments.staging_dir
            os.makedirs(staging, exist_ok=True)

            filename = att.filename or f"attachment_{attachment_index}"
            dest = target_path or os.path.join(staging, f"{uid}_{filename}")
            with open(dest, "wb") as f:
                f.write(att.payload)

            return {
                "path": dest,
                "filename": filename,
                "size": att.size,
                "content_type": att.content_type or "application/octet-stream",
            }

    def set_flags(
        self,
        folder: str,
        uids: list[str],
        flag: str,
        value: bool,
    ) -> dict:
        with self._connect(folder) as mb:
            flag_map = {
                "\\Seen": "seen",
                "\\Flagged": "flagged",
            }
            flag_name = flag_map.get(flag)
            if not flag_name:
                raise ImapError("imap_protocol_error", f"Unsupported flag: {flag}")

            if value:
                mb.flag(uids, [flag], True)
            else:
                mb.flag(uids, [flag], False)

            return {"ok": True, "updated_count": len(uids)}

    def move_message(self, folder: str, uid: str, destination_folder: str) -> dict:
        with self._connect(folder) as mb:
            mb.move(uid, destination_folder)
            return {"ok": True, "new_uid": None}  # IMAP MOVE doesn't reliably return new UID

    def delete_message(self, folder: str, uid: str, soft: bool = True) -> dict:
        with self._connect(folder) as mb:
            if soft:
                mb.move(uid, "Trash")
            else:
                mb.delete(uid)
            return {"ok": True}
