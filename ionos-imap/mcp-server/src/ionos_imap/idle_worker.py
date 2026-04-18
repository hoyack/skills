"""IDLE worker daemon — maintains long-lived IMAP IDLE connections.

Watches configured folders for new mail, caches envelopes in the local
state store, and optionally emits events to RabbitMQ.

Run as: ionos-imap-worker
Or via systemd: openclaw-imap-worker.service
"""

from __future__ import annotations

import datetime
import json
import logging
import signal
import ssl
import sys
import time

from dotenv import load_dotenv
from imap_tools import AND, MailBox, MailboxLoginError

from .config import Config, load_config
from .imap_client import ImapClient
from .state import StateStore

load_dotenv()
log = logging.getLogger(__name__)


class IdleWorker:
    """Long-lived IMAP IDLE daemon for new-mail detection."""

    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._state = StateStore(cfg.state.sqlite_path)
        self._client = ImapClient(cfg)
        self._running = False
        self._backoff = cfg.worker.reconnect_backoff_initial
        self._consecutive_failures = 0
        self._rabbitmq_channel = None

    def start(self) -> None:
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        log.info(
            "IDLE worker starting — watching folders: %s",
            self._cfg.worker.watched_folders,
        )

        self._state.update_worker_health(
            connection_state="starting",
            watched_folders=self._cfg.worker.watched_folders,
        )

        if self._cfg.worker.emit_rabbitmq_events:
            self._init_rabbitmq()

        while self._running:
            for folder in self._cfg.worker.watched_folders:
                if not self._running:
                    break
                self._watch_folder(folder)

    def _handle_signal(self, signum: int, frame) -> None:
        log.info("Received signal %d, shutting down", signum)
        self._running = False

    def _watch_folder(self, folder: str) -> None:
        """Run one IDLE cycle for a folder."""
        conn = self._cfg.connection
        ssl_ctx = ssl.create_default_context() if conn.use_tls else None

        try:
            mb = MailBox(
                host=conn.host,
                port=conn.port,
                ssl_context=ssl_ctx,
                timeout=conn.timeout_seconds,
            )
            mb.login(
                self._cfg.account.username,
                self._cfg.account.password,
                initial_folder=folder,
            )
        except MailboxLoginError as exc:
            log.error("Auth failed for %s: %s", folder, exc)
            self._state.update_worker_health(connection_state="auth_failed")
            self._backoff_sleep()
            return
        except Exception as exc:
            log.error("Connection failed for %s: %s", folder, exc)
            self._state.update_worker_health(connection_state="disconnected")
            self._backoff_sleep()
            return

        log.info("Connected to %s, checking UIDVALIDITY", folder)
        self._consecutive_failures = 0
        self._backoff = self._cfg.worker.reconnect_backoff_initial

        # Check UIDVALIDITY
        self._check_uidvalidity(mb, folder)

        # Initial sync — fetch recent envelopes
        self._sync_recent(mb, folder)

        self._state.update_worker_health(
            connection_state="idle",
            last_idle_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            watched_folders=self._cfg.worker.watched_folders,
        )

        # Enter IDLE loop
        idle_start = time.monotonic()
        rotation_limit = self._cfg.worker.idle_rotation_seconds
        heartbeat_interval = self._cfg.worker.heartbeat_interval_seconds
        last_heartbeat = time.monotonic()

        try:
            while self._running:
                elapsed = time.monotonic() - idle_start
                if elapsed >= rotation_limit:
                    log.info(
                        "IDLE rotation after %.0fs on %s", elapsed, folder
                    )
                    break

                # IDLE for up to 60 seconds, then check for rotation
                responses = mb.idle.wait(timeout=min(60, rotation_limit - elapsed))

                if responses:
                    log.info("IDLE wake on %s: %d responses", folder, len(responses))
                    self._sync_recent(mb, folder)
                    self._state.update_worker_health(
                        last_idle_at=datetime.datetime.now(
                            tz=datetime.timezone.utc
                        ).isoformat(),
                    )

                # Heartbeat
                now = time.monotonic()
                if now - last_heartbeat >= heartbeat_interval:
                    self._state.update_worker_health(
                        connection_state="idle",
                        watched_folders=self._cfg.worker.watched_folders,
                    )
                    last_heartbeat = now

        except Exception as exc:
            log.error("IDLE error on %s: %s", folder, exc)
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                log.critical(
                    "5 consecutive IDLE failures on %s — continuing at max backoff",
                    folder,
                )
                self._state.update_worker_health(connection_state="critical")
            else:
                self._state.update_worker_health(connection_state="reconnecting")
            self._backoff_sleep()
        finally:
            try:
                mb.logout()
            except Exception:
                pass

    def _check_uidvalidity(self, mb: MailBox, folder: str) -> None:
        """Verify UIDVALIDITY hasn't changed; resync if it has."""
        status = mb.folder.status(folder)
        current_validity = status.get("UIDVALIDITY")
        current_next = status.get("UIDNEXT")

        stored = self._state.get_folder_state(folder)
        if stored and stored["uidvalidity"] != current_validity:
            log.warning(
                "UIDVALIDITY changed for %s: %s -> %s — full resync",
                folder,
                stored["uidvalidity"],
                current_validity,
            )
            purged = self._state.purge_folder(folder)
            log.warning("Purged %d stale envelopes from %s", purged, folder)

        self._state.update_folder_state(folder, current_validity, current_next)

    def _sync_recent(self, mb: MailBox, folder: str) -> None:
        """Fetch recent envelopes and cache them."""
        try:
            msgs = list(mb.fetch(AND(all=True), limit=50, reverse=True, headers_only=True))
            envelopes = []
            for msg in msgs:
                from .imap_client import _msg_to_envelope

                env = _msg_to_envelope(msg, folder).to_dict()
                envelopes.append(env)

            if envelopes:
                self._state.upsert_envelopes(envelopes)
                log.info("Synced %d envelopes for %s", len(envelopes), folder)

                if self._rabbitmq_channel and self._cfg.worker.emit_rabbitmq_events:
                    self._publish_events(envelopes)

        except Exception as exc:
            log.error("Sync failed for %s: %s", folder, exc)

    def _backoff_sleep(self) -> None:
        import random

        jitter = random.uniform(0, self._backoff * 0.1)
        sleep_time = min(
            self._backoff + jitter, self._cfg.worker.reconnect_backoff_max
        )
        log.info("Backing off for %.1fs", sleep_time)
        time.sleep(sleep_time)
        self._backoff = min(self._backoff * 2, self._cfg.worker.reconnect_backoff_max)

    def _init_rabbitmq(self) -> None:
        """Initialize RabbitMQ connection for event publishing."""
        try:
            import pika

            params = pika.URLParameters(self._cfg.worker.rabbitmq_uri)
            connection = pika.BlockingConnection(params)
            self._rabbitmq_channel = connection.channel()
            self._rabbitmq_channel.exchange_declare(
                exchange=self._cfg.worker.rabbitmq_topic,
                exchange_type="fanout",
                durable=True,
            )
            log.info("RabbitMQ connected: %s", self._cfg.worker.rabbitmq_topic)
        except Exception as exc:
            log.warning("RabbitMQ init failed (events disabled): %s", exc)
            self._rabbitmq_channel = None

    def _publish_events(self, envelopes: list[dict]) -> None:
        if not self._rabbitmq_channel:
            return
        try:
            for env in envelopes:
                self._rabbitmq_channel.basic_publish(
                    exchange=self._cfg.worker.rabbitmq_topic,
                    routing_key="",
                    body=json.dumps(env),
                )
        except Exception as exc:
            log.error("RabbitMQ publish failed: %s", exc)

    def stop(self) -> None:
        self._running = False
        self._state.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )
    cfg = load_config()

    if not cfg.account.username or not cfg.account.password:
        log.error("IONOS_IMAP_USERNAME and IONOS_IMAP_PASSWORD must be set")
        sys.exit(1)

    worker = IdleWorker(cfg)
    try:
        worker.start()
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()
        log.info("IDLE worker stopped")


if __name__ == "__main__":
    main()
