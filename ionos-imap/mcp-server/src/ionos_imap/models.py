"""Data models for IONOS IMAP skill."""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any


@dataclasses.dataclass(frozen=True, slots=True)
class Address:
    name: str | None
    email: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "email": self.email}


@dataclasses.dataclass(frozen=True, slots=True)
class Envelope:
    uid: str
    folder: str
    date: datetime.datetime
    from_addr: Address
    to: list[Address]
    cc: list[Address]
    subject: str
    flags: list[str]
    size_bytes: int
    has_attachments: bool
    message_id: str
    in_reply_to: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "folder": self.folder,
            "date": self.date.isoformat(),
            "from": self.from_addr.to_dict(),
            "to": [a.to_dict() for a in self.to],
            "cc": [a.to_dict() for a in self.cc],
            "subject": self.subject,
            "flags": self.flags,
            "size_bytes": self.size_bytes,
            "has_attachments": self.has_attachments,
            "message_id": self.message_id,
            "in_reply_to": self.in_reply_to,
        }


@dataclasses.dataclass(frozen=True, slots=True)
class AttachmentMeta:
    index: int
    filename: str
    content_type: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
        }


@dataclasses.dataclass(frozen=True, slots=True)
class FullMessage:
    envelope: Envelope
    text: str | None
    html: str | None
    headers: dict[str, str]
    attachments: list[AttachmentMeta]

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "text": self.text,
            "html": self.html,
            "headers": self.headers,
            "attachments": [a.to_dict() for a in self.attachments],
        }


# Error codes per spec section 7.4
class ImapError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.code,
            "message": str(self),
            "retryable": self.retryable,
        }
