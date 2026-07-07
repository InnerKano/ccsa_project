"""Select the email sender based on configuration (D23).

EMAIL_ENABLED=true  → real SMTP delivery (App Password for Gmail).
EMAIL_ENABLED=false → console/dev sender that only logs (never in production).
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.shared.email.base import EmailSender
from app.shared.email.console import ConsoleEmailSender
from app.shared.email.smtp import SmtpEmailSender


@lru_cache
def get_email_sender() -> EmailSender:
    if settings.email_enabled:
        return SmtpEmailSender()
    return ConsoleEmailSender()
