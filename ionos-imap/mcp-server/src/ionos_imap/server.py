"""IONOS IMAP MCP server — exposes mailbox tools to OpenClaw agents."""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from .config import Config, load_config
from .imap_client import ImapClient
from .models import ImapError
from .state import StateStore

load_dotenv()
log = logging.getLogger(__name__)

_cfg: Config | None = None
_client: ImapClient | None = None
_state: StateStore | None = None


def _validate_config(cfg: Config) -> None:
    if not cfg.account.username:
        print(
            "ERROR: IONOS_IMAP_USERNAME not set. "
            "Set it via env var or in ionos-imap.toml",
            file=sys.stderr,
        )
        sys.exit(1)
    if not cfg.account.password:
        print(
            "ERROR: IONOS_IMAP_PASSWORD not set. "
            "Set it via env var or in ionos-imap.toml",
            file=sys.stderr,
        )
        sys.exit(1)


@asynccontextmanager
async def _lifespan(server: FastMCP):
    global _cfg, _client, _state
    _cfg = load_config()
    _validate_config(_cfg)
    _client = ImapClient(_cfg)
    _state = StateStore(_cfg.state.sqlite_path)
    log.info(
        "ionos-imap MCP server started — host=%s user=%s",
        _cfg.connection.host,
        _cfg.account.username,
    )
    yield
    if _state:
        _state.close()
    log.info("ionos-imap MCP server stopped")


mcp = FastMCP(
    name="ionos-imap",
    instructions=(
        "IONOS IMAP mail access. Use list_envelopes for fast mailbox polling "
        "(reads from local cache). Use search_envelopes for server-side search. "
        "read_message fetches full body — set mark_seen=true only after processing."
    ),
    lifespan=_lifespan,
)


def _error_response(e: ImapError) -> dict[str, Any]:
    return e.to_dict()


# --- Tools ---


@mcp.tool()
async def list_folders() -> list[dict]:
    """List all mailbox folders (IMAP LIST). Returns name, delimiter, and flags for each folder."""
    try:
        return _client.list_folders()
    except ImapError as e:
        return [_error_response(e)]


@mcp.tool()
async def list_envelopes(
    folder: str = "INBOX",
    since: str | None = None,
    unseen_only: bool = False,
    limit: int = 50,
) -> list[dict]:
    """List message envelopes. Reads from local state cache (fast, sub-100ms).
    Use for routine polling. Falls back to IMAP if cache is empty.

    Args:
        folder: Mailbox folder (default INBOX)
        since: ISO datetime — only messages after this date
        unseen_only: If true, only unread messages
        limit: Max results (default 50)
    """
    # Try local state first
    cached = _state.list_envelopes(folder, since, unseen_only, limit)
    if cached:
        return cached

    # Fall back to live IMAP
    try:
        since_dt = datetime.datetime.fromisoformat(since) if since else None
        envelopes = _client.list_envelopes(folder, since_dt, unseen_only, limit)
        _state.upsert_envelopes(envelopes)
        return envelopes
    except ImapError as e:
        return [_error_response(e)]


@mcp.tool()
async def search_envelopes(
    folder: str = "INBOX",
    from_addr: str | None = None,
    to_addr: str | None = None,
    subject_contains: str | None = None,
    body_contains: str | None = None,
    date_gte: str | None = None,
    date_lte: str | None = None,
    flags: list[str] | None = None,
) -> list[dict]:
    """Server-side IMAP search (slower, 500ms-5s). Use when criteria exceed local index.

    Args:
        folder: Mailbox folder
        from_addr: Filter by sender address/name
        to_addr: Filter by recipient
        subject_contains: Subject keyword match
        body_contains: Body text search
        date_gte: Messages on or after this ISO date
        date_lte: Messages before this ISO date
        flags: Filter by flags (e.g. ["\\\\Seen", "\\\\Flagged"])
    """
    try:
        date_gte_dt = datetime.datetime.fromisoformat(date_gte) if date_gte else None
        date_lte_dt = datetime.datetime.fromisoformat(date_lte) if date_lte else None
        return _client.search_envelopes(
            folder, from_addr, to_addr, subject_contains, body_contains,
            date_gte_dt, date_lte_dt, flags,
        )
    except ImapError as e:
        return [_error_response(e)]


@mcp.tool()
async def read_message(
    folder: str,
    uid: str,
    mark_seen: bool = False,
) -> dict:
    """Fetch full message: envelope, text body, HTML body, headers, and attachment metadata.

    Args:
        folder: Mailbox folder containing the message
        uid: Message UID
        mark_seen: If true, set \\\\Seen flag on fetch (default false — mark explicitly after processing)
    """
    try:
        return _client.read_message(folder, uid, mark_seen)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def get_attachment(
    folder: str,
    uid: str,
    attachment_index: int,
    target_path: str | None = None,
) -> dict:
    """Download one attachment to staging directory.

    Args:
        folder: Mailbox folder
        uid: Message UID
        attachment_index: Zero-based index of the attachment
        target_path: Optional custom save path (default: staging dir)
    """
    try:
        return _client.get_attachment(folder, uid, attachment_index, target_path)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def mark_seen(folder: str, uid: str | None = None, uids: list[str] | None = None) -> dict:
    """Mark message(s) as read (set \\\\Seen flag).

    Args:
        folder: Mailbox folder
        uid: Single message UID
        uids: List of UIDs for bulk operation
    """
    try:
        uid_list = uids or ([uid] if uid else [])
        if not uid_list:
            return {"error": "Provide uid or uids"}
        return _client.set_flags(folder, uid_list, "\\Seen", True)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def mark_unseen(folder: str, uid: str | None = None, uids: list[str] | None = None) -> dict:
    """Mark message(s) as unread (remove \\\\Seen flag).

    Args:
        folder: Mailbox folder
        uid: Single message UID
        uids: List of UIDs for bulk operation
    """
    try:
        uid_list = uids or ([uid] if uid else [])
        if not uid_list:
            return {"error": "Provide uid or uids"}
        return _client.set_flags(folder, uid_list, "\\Seen", False)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def flag(folder: str, uid: str | None = None, uids: list[str] | None = None) -> dict:
    """Flag message(s) (set \\\\Flagged).

    Args:
        folder: Mailbox folder
        uid: Single message UID
        uids: List of UIDs for bulk operation
    """
    try:
        uid_list = uids or ([uid] if uid else [])
        if not uid_list:
            return {"error": "Provide uid or uids"}
        return _client.set_flags(folder, uid_list, "\\Flagged", True)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def unflag(folder: str, uid: str | None = None, uids: list[str] | None = None) -> dict:
    """Remove flag from message(s) (unset \\\\Flagged).

    Args:
        folder: Mailbox folder
        uid: Single message UID
        uids: List of UIDs for bulk operation
    """
    try:
        uid_list = uids or ([uid] if uid else [])
        if not uid_list:
            return {"error": "Provide uid or uids"}
        return _client.set_flags(folder, uid_list, "\\Flagged", False)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def move_message(folder: str, uid: str, destination_folder: str) -> dict:
    """Move a message to a different folder.

    Args:
        folder: Source folder
        uid: Message UID
        destination_folder: Target folder path
    """
    try:
        return _client.move_message(folder, uid, destination_folder)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def delete_message(folder: str, uid: str, soft: bool = True) -> dict:
    """Delete a message. Soft delete moves to Trash; hard delete expunges.

    Args:
        folder: Mailbox folder
        uid: Message UID
        soft: If true (default), move to Trash. If false, permanently delete.
    """
    try:
        return _client.delete_message(folder, uid, soft)
    except ImapError as e:
        return _error_response(e)


@mcp.tool()
async def watch_status() -> dict:
    """Report IDLE worker health: last heartbeat, last IDLE cycle, connection state."""
    return _state.get_worker_health()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="IONOS IMAP MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
