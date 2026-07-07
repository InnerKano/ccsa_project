"""SMTP email sender (stdlib `smtplib` — no new dependency).

Gmail note: SMTP requires an **App Password** (a 16-char credential generated in
Google Account → Security), not the normal account password, which Google
disabled for SMTP. Configure via SMTP_* env vars (see .env.example).
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.shared.email.base import EmailSender


class SmtpEmailSender(EmailSender):
    def send(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = settings.email_sender_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text_body)
        if html_body is not None:
            message.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
