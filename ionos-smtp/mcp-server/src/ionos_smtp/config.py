"""Configuration loading for IONOS SMTP skill."""

from __future__ import annotations

import dataclasses
import os
import tomllib
from pathlib import Path


@dataclasses.dataclass(slots=True)
class ConnectionConfig:
    host: str = "smtp.ionos.com"
    port: int = 465
    tls_mode: str = "implicit"  # "implicit" (465) | "starttls" (587)
    timeout_seconds: int = 30


@dataclasses.dataclass(slots=True)
class AccountConfig:
    username: str = ""
    password: str = ""
    default_from_name: str = ""
    default_from_email: str = ""
    default_reply_to: str = ""


@dataclasses.dataclass(slots=True)
class SendConfig:
    default_append_to_sent: bool = True
    sent_folder_name: str = "Sent"
    max_attachment_mb: int = 25
    max_total_size_mb: int = 40
    rate_limit_per_minute: int = 30


@dataclasses.dataclass(slots=True)
class QueueConfig:
    enabled: bool = False
    rabbitmq_uri: str = "amqp://localhost"
    queue_name: str = "mail.ionos.send"
    deadletter_queue_name: str = "mail.ionos.send.deadletter"
    max_retries: int = 5
    retry_backoff_initial: float = 2.0
    retry_backoff_max: float = 300.0


@dataclasses.dataclass(slots=True)
class StateConfig:
    backend: str = "sqlite"
    sqlite_path: str = "~/.local/state/openclaw/smtp/state.db"


@dataclasses.dataclass(slots=True)
class ImapIntegrationConfig:
    enabled: bool = True
    mcp_tool_name: str = "mail.ionos.append_to_sent"


@dataclasses.dataclass(slots=True)
class McpConfig:
    transport: str = "stdio"
    http_port: int = 8766


@dataclasses.dataclass(slots=True)
class Config:
    connection: ConnectionConfig = dataclasses.field(default_factory=ConnectionConfig)
    account: AccountConfig = dataclasses.field(default_factory=AccountConfig)
    send: SendConfig = dataclasses.field(default_factory=SendConfig)
    queue: QueueConfig = dataclasses.field(default_factory=QueueConfig)
    state: StateConfig = dataclasses.field(default_factory=StateConfig)
    imap_integration: ImapIntegrationConfig = dataclasses.field(
        default_factory=ImapIntegrationConfig
    )
    mcp: McpConfig = dataclasses.field(default_factory=McpConfig)


def _apply_section(target: object, data: dict) -> None:
    for key, value in data.items():
        if hasattr(target, key):
            setattr(target, key, value)


def load_config() -> Config:
    """Load config from TOML file (if present) then overlay env vars."""
    cfg = Config()

    config_path = os.environ.get(
        "IONOS_SMTP_CONFIG",
        os.path.expanduser("~/.config/openclaw/ionos-smtp.toml"),
    )
    p = Path(config_path)
    if p.exists():
        with open(p, "rb") as f:
            data = tomllib.load(f)
        for section_name in (
            "connection", "account", "send", "queue", "state",
            "imap_integration", "mcp",
        ):
            if section_name in data:
                _apply_section(getattr(cfg, section_name), data[section_name])

    # Env var overrides (highest priority)
    if v := os.environ.get("IONOS_SMTP_HOST"):
        cfg.connection.host = v
    if v := os.environ.get("IONOS_SMTP_PORT"):
        cfg.connection.port = int(v)
    if v := os.environ.get("IONOS_SMTP_TLS_MODE"):
        cfg.connection.tls_mode = v
    if v := os.environ.get("IONOS_SMTP_USERNAME"):
        cfg.account.username = v
    if v := os.environ.get("IONOS_SMTP_PASSWORD"):
        cfg.account.password = v
    if v := os.environ.get("IONOS_SMTP_FROM_NAME"):
        cfg.account.default_from_name = v
    if v := os.environ.get("IONOS_SMTP_FROM_EMAIL"):
        cfg.account.default_from_email = v

    # Expand paths
    cfg.state.sqlite_path = os.path.expanduser(cfg.state.sqlite_path)

    return cfg
