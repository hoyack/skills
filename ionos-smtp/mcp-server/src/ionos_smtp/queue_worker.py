"""Queue worker daemon — consumes RabbitMQ send jobs and delivers via SMTP.

Handles retry with exponential backoff for transient failures.
Permanent failures route to deadletter queue.

Run as: ionos-smtp-worker
Or via systemd: openclaw-smtp-worker.service
"""

from __future__ import annotations

import datetime
import json
import logging
import signal
import sys
import time

from dotenv import load_dotenv

from .config import Config, load_config
from .models import Address, AttachmentSpec, SmtpError
from .smtp_client import (
    compose_message,
    send_smtp,
    _parse_address_list,
    _resolve_from,
)
from .state import StateStore

load_dotenv()
log = logging.getLogger(__name__)


class QueueWorker:
    """Consumes mail send jobs from RabbitMQ and delivers via SMTP."""

    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._state = StateStore(cfg.state.sqlite_path)
        self._running = False
        self._channel = None
        self._connection = None

    def start(self) -> None:
        import pika

        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        log.info("SMTP queue worker starting — queue: %s", self._cfg.queue.queue_name)
        self._state.update_worker_health(connection_state="starting")

        params = pika.URLParameters(self._cfg.queue.rabbitmq_uri)
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()

        # Declare main queue and deadletter queue
        self._channel.queue_declare(
            queue=self._cfg.queue.deadletter_queue_name, durable=True
        )
        self._channel.queue_declare(
            queue=self._cfg.queue.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": self._cfg.queue.deadletter_queue_name,
            },
        )

        # Prefetch 1 — process one at a time for rate limiting
        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(
            queue=self._cfg.queue.queue_name,
            on_message_callback=self._on_message,
        )

        self._state.update_worker_health(connection_state="consuming")
        log.info("Consuming from %s", self._cfg.queue.queue_name)

        try:
            self._channel.start_consuming()
        except Exception as exc:
            log.error("Consumer error: %s", exc)
        finally:
            self._state.update_worker_health(connection_state="stopped")

    def _handle_signal(self, signum: int, frame) -> None:
        log.info("Received signal %d, shutting down", signum)
        self._running = False
        if self._channel:
            self._channel.stop_consuming()

    def _on_message(self, ch, method, properties, body: bytes) -> None:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            log.error("Invalid JSON in queue message, rejecting")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        queue_id = payload.get("queue_id", "unknown")
        log.info("Processing queue job %s", queue_id)

        self._state.update_outbound(
            queue_id, status="sending", increment_attempts=True
        )

        try:
            self._send_job(payload)
            self._state.update_outbound(queue_id, status="sent")
            self._state.update_worker_health(
                connection_state="consuming",
                last_send_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log.info("Job %s sent successfully", queue_id)

        except SmtpError as e:
            if e.retryable:
                outbound = self._state.get_outbound(queue_id)
                attempts = outbound["attempts"] if outbound else 0
                if attempts >= self._cfg.queue.max_retries:
                    log.error(
                        "Job %s exceeded max retries (%d), moving to deadletter",
                        queue_id,
                        self._cfg.queue.max_retries,
                    )
                    self._state.update_outbound(
                        queue_id, status="deadletter", last_error=str(e)
                    )
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                else:
                    backoff = min(
                        self._cfg.queue.retry_backoff_initial * (2 ** (attempts - 1)),
                        self._cfg.queue.retry_backoff_max,
                    )
                    log.warning(
                        "Job %s transient error (attempt %d): %s — requeue after %.1fs",
                        queue_id,
                        attempts,
                        e,
                        backoff,
                    )
                    self._state.update_outbound(
                        queue_id, status="pending", last_error=str(e)
                    )
                    time.sleep(backoff)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                log.error(
                    "Job %s permanent error: %s — moving to deadletter",
                    queue_id,
                    e,
                )
                self._state.update_outbound(
                    queue_id, status="deadletter", last_error=str(e)
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _send_job(self, payload: dict) -> None:
        """Compose and send a queued message."""
        from_resolved = _resolve_from(self._cfg, payload.get("from_addr"))
        to_addrs = _parse_address_list(payload.get("to", []))
        cc_addrs = _parse_address_list(payload.get("cc"))
        bcc_addrs = _parse_address_list(payload.get("bcc"))

        att_specs = [
            AttachmentSpec(
                path=a["path"],
                filename=a.get("filename", ""),
                content_type=a.get("content_type", "application/octet-stream"),
            )
            for a in (payload.get("attachments") or [])
        ]

        msg, mid = compose_message(
            self._cfg,
            from_addr=from_resolved,
            to=to_addrs,
            cc=cc_addrs,
            subject=payload.get("subject", ""),
            text=payload.get("text"),
            html=payload.get("html"),
            attachments=att_specs or None,
            custom_headers=payload.get("custom_headers"),
        )

        all_to = [a.email for a in to_addrs + cc_addrs]
        bcc_emails = [a.email for a in bcc_addrs]

        send_smtp(self._cfg, msg, all_to, bcc_emails)

        # Update with message ID
        queue_id = payload.get("queue_id")
        if queue_id:
            self._state.update_outbound(queue_id, status="sent", message_id=mid)

    def stop(self) -> None:
        self._running = False
        if self._connection and self._connection.is_open:
            self._connection.close()
        self._state.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )
    cfg = load_config()

    if not cfg.account.username or not cfg.account.password:
        log.error("IONOS_SMTP_USERNAME and IONOS_SMTP_PASSWORD must be set")
        sys.exit(1)

    if not cfg.queue.enabled:
        log.error("Queue mode is not enabled in config — set [queue] enabled = true")
        sys.exit(1)

    worker = QueueWorker(cfg)
    try:
        worker.start()
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()
        log.info("SMTP queue worker stopped")


if __name__ == "__main__":
    main()
