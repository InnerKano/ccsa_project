"""Console email sender — development fallback only.

Logs the message (including the reset link) so the recovery flow is testable
without configuring SMTP. This deliberately prints a link that would normally be
private; it is only selected when EMAIL_ENABLED is False, which must never be the
case in production (D23, ARCHITECTURE.md graceful degradation).
"""

from __future__ import annotations

import logging

from app.shared.email.base import EmailSender

logger = logging.getLogger("ccsa.email")


class ConsoleEmailSender(EmailSender):
    def send(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        logger.info(
            "[dev email] EMAIL_ENABLED is false — not sending. "
            "To: %s | Subject: %s\n%s",
            to,
            subject,
            text_body,
        )
