from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import logging
from pathlib import Path
import smtplib
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger("creatorlab.mail")


@dataclass(frozen=True)
class MailMessage:
    to_email: str
    subject: str
    text_body: str
    html_body: str
    kind: str
    action_url: str | None = None


@dataclass(frozen=True)
class MailDeliveryResult:
    message_id: str
    preview_url: str | None = None


class MailProvider(ABC):
    @abstractmethod
    def ensure_directories(self) -> None: ...

    @abstractmethod
    def send(self, message: MailMessage) -> MailDeliveryResult: ...

    def get_message(self, message_id: str) -> dict[str, object] | None:
        return None

    def get_latest_message(self, to_email: str, kind: str) -> dict[str, object] | None:
        return None

    def stats(self) -> dict[str, int | str]:
        return {"message_count": 0, "backend": type(self).__name__}


class LocalFileMailProvider(MailProvider):
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure_directories(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def send(self, message: MailMessage) -> MailDeliveryResult:
        self.ensure_directories()
        message_id = uuid4().hex
        preview_url = f"{settings.api_public_url.rstrip('/')}/api/auth/dev/messages/{message_id}"
        payload = {
            "id": message_id,
            "kind": message.kind,
            "to_email": message.to_email.lower(),
            "subject": message.subject,
            "text_body": message.text_body,
            "html_body": message.html_body,
            "action_url": message.action_url,
            "preview_url": preview_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (self.root / f"{message_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("Saved local email preview %s for %s", message_id, message.to_email)
        return MailDeliveryResult(message_id=message_id, preview_url=preview_url)

    def get_message(self, message_id: str) -> dict[str, object] | None:
        path = self.root / f"{message_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def get_latest_message(self, to_email: str, kind: str) -> dict[str, object] | None:
        self.ensure_directories()
        matches: list[dict[str, object]] = []
        for path in self.root.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if str(payload.get("to_email", "")).lower() != to_email.lower():
                continue
            if str(payload.get("kind", "")) != kind:
                continue
            matches.append(payload)
        if not matches:
            return None
        matches.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        return matches[0]

    def stats(self) -> dict[str, int | str]:
        self.ensure_directories()
        return {
            "message_count": len(list(self.root.glob("*.json"))),
            "backend": "local_file",
        }


class LoggingMailProvider(MailProvider):
    def ensure_directories(self) -> None:
        return None

    def send(self, message: MailMessage) -> MailDeliveryResult:
        logger.info("Mail send requested | to=%s | subject=%s | kind=%s", message.to_email, message.subject, message.kind)
        return MailDeliveryResult(message_id=uuid4().hex, preview_url=None)

    def stats(self) -> dict[str, int | str]:
        return {"message_count": 0, "backend": "logging"}


class SmtpMailProvider(MailProvider):
    def ensure_directories(self) -> None:
        return None

    def send(self, message: MailMessage) -> MailDeliveryResult:
        if not settings.smtp_host:
            raise RuntimeError("SMTP_HOST must be configured when MAIL_BACKEND=smtp.")

        email_message = EmailMessage()
        email_message["Subject"] = message.subject
        email_message["From"] = settings.mail_from_email
        email_message["To"] = message.to_email
        email_message.set_content(message.text_body)
        email_message.add_alternative(message.html_body, subtype="html")

        smtp_client: smtplib.SMTP | smtplib.SMTP_SSL
        if settings.smtp_use_ssl:
            smtp_client = smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            )
        else:
            smtp_client = smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            )

        message_id = uuid4().hex
        try:
            with smtp_client as server:
                if settings.smtp_use_tls and not settings.smtp_use_ssl:
                    server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password or "")
                server.send_message(email_message)
        except Exception:
            logger.exception("SMTP mail send failed for %s", message.to_email)
            raise

        logger.info("Sent SMTP email %s to %s", message_id, message.to_email)
        return MailDeliveryResult(message_id=message_id, preview_url=None)

    def stats(self) -> dict[str, int | str]:
        return {
            "message_count": 0,
            "backend": "smtp",
            "host": settings.smtp_host or "",
        }


def _build_mail_provider() -> MailProvider:
    if settings.mail_backend == "local_file":
        return LocalFileMailProvider(settings.storage_root / "mail")
    if settings.mail_backend == "smtp":
        return SmtpMailProvider()
    return LoggingMailProvider()


mail_provider = _build_mail_provider()
