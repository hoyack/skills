"""Configuration loading for IONOS IMAP skill."""

from __future__ import annotations

import dataclasses
import os
import tomllib
from pathlib import Path


@dataclasses.dataclass(slots=True)
class ConnectionConfig:
    host: str = "imap.ionos.com"
    port: int = 993
    use_tls: bool = True
    timeout_seconds: int = 30


@dataclasses.dataclass(slots=True)
class AccountConfig:
    username: str = ""
    password: str = ""


@dataclasses.dataclass(slots=True)
class WorkerConfig:
    watched_folders: list[str] = dataclasses.field(default_factory=lambda: ["INBOX"])
    idle_rotation_seconds: int = 1700
    reconnect_backoff_initial: float = 1.0
    reconnect_backoff_max: float = 60.0
    heartbeat_interval_seconds: int = 60
    emit_rabbitmq_events: bool = False
    rabbitmq_uri: str = "amqp://localhost"
    rabbitmq_topic: str = "mail.ionos.new"


@dataclasses.dataclass(slots=True)
class StateConfig:
    backend: str = "sqlite"
    sqlite_path: str = "~/.local/state/openclaw/imap/state.db"


@dataclasses.dataclass(slots=True)
class AttachmentConfig:
    staging_dir: str = "~/.local/state/openclaw/imap/attachments"
    max_size_mb: int = 50
    allowed_types: list[str] = dataclasses.field(default_factory=lambda: ["*"])


@dataclasses.dataclass(slots=True)
class McpConfig:
    transport: str = "stdio"
    http_port: int = 8765


@dataclasses.dataclass(slots=True)
class Config:
    connection: ConnectionConfig = dataclasses.field(default_factory=ConnectionConfig)
    account: AccountConfig = dataclasses.field(default_factory=AccountConfig)
    worker: WorkerConfig = dataclasses.field(default_factory=WorkerConfig)
    state: StateConfig = dataclasses.field(default_factory=StateConfig)
    attachments: AttachmentConfig = dataclasses.field(default_factory=AttachmentConfig)
    mcp: McpConfig = dataclasses.field(default_factory=McpConfig)


def _apply_section(target: object, data: dict) -> None:
    for key, value in data.items():
        if hasattr(target, key):
            setattr(target, key, value)


def load_config() -> Config:
    """Load config from TOML file (if present) then overlay env vars."""
    cfg = Config()

    # Try TOML config file
    config_path = os.environ.get(
        "IONOS_IMAP_CONFIG",
        os.path.expanduser("~/.config/openclaw/ionos-imap.toml"),
    )
    p = Path(config_path)
    if p.exists():
        with open(p, "rb") as f:
            data = tomllib.load(f)
        if "connection" in data:
            _apply_section(cfg.connection, data["connection"])
        if "worker" in data:
            _apply_section(cfg.worker, data["worker"])
        if "state" in data:
            _apply_section(cfg.state, data["state"])
        if "attachments" in data:
            _apply_section(cfg.attachments, data["attachments"])
        if "mcp" in data:
            _apply_section(cfg.mcp, data["mcp"])

    # Env var overrides (highest priority)
    if v := os.environ.get("IONOS_IMAP_HOST"):
        cfg.connection.host = v
    if v := os.environ.get("IONOS_IMAP_PORT"):
        cfg.connection.port = int(v)
    if v := os.environ.get("IONOS_IMAP_USERNAME"):
        cfg.account.username = v
    if v := os.environ.get("IONOS_IMAP_PASSWORD"):
        cfg.account.password = v

    # Expand paths
    cfg.state.sqlite_path = os.path.expanduser(cfg.state.sqlite_path)
    cfg.attachments.staging_dir = os.path.expanduser(cfg.attachments.staging_dir)

    return cfg
