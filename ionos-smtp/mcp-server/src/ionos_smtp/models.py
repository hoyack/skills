"""Data models for IONOS SMTP skill."""

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

    def formatted(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclasses.dataclass(frozen=True, slots=True)
class AttachmentSpec:
    path: str
    filename: str
    content_type: str = "application/octet-stream"


@dataclasses.dataclass(frozen=True, slots=True)
class InlineImageSpec:
    path: str
    cid: str
    content_type: str = "image/png"


@dataclasses.dataclass(frozen=True, slots=True)
class SendReceipt:
    ok: bool
    message_id: str
    accepted_recipients: list[str]
    rejected_recipients: list[str]
    smtp_response: str
    sent_at: str
    appended_to_sent: bool
    sent_uid: str | None = None
    error: str | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "ok": self.ok,
            "message_id": self.message_id,
            "accepted_recipients": self.accepted_recipients,
            "rejected_recipients": self.rejected_recipients,
            "smtp_response": self.smtp_response,
            "sent_at": self.sent_at,
            "appended_to_sent": self.appended_to_sent,
        }
        if self.sent_uid:
            d["sent_uid"] = self.sent_uid
        if self.error:
            d["error"] = self.error
            d["error_code"] = self.error_code
        return d


class SmtpError(Exception):
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
