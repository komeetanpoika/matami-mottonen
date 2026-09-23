import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.config import settings

log = logging.getLogger(__name__)


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailer:
    def __init__(
        self, host: str, port: int, user: str | None, password: str | None, sender: str
    ) -> None:
        self.host, self.port, self.user, self.password, self.sender = (
            host,
            port,
            user,
            password,
            sender,
        )

    def send(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, subject
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=20) as smtp:
            smtp.ehlo()
            if self.port != 25:
                smtp.starttls()
            if self.user and self.password:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)


class NullMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        log.warning("SMTP not configured; would send to %s: %s", to, subject)


_mailer: Mailer | None = None


def get_mailer() -> Mailer:
    global _mailer
    if _mailer is None:
        if settings.smtp_host:
            _mailer = SmtpMailer(
                settings.smtp_host,
                settings.smtp_port,
                settings.smtp_user,
                settings.smtp_password,
                settings.smtp_from,
            )
        else:
            _mailer = NullMailer()
    return _mailer
