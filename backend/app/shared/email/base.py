"""Email sender contract — provider-agnostic (mirrors the LLM provider seam).

Feature code depends on this interface, never on a concrete backend, so SMTP,
a console/dev logger, or a future transactional provider are interchangeable
via `factory.get_email_sender()` (ARCHITECTURE.md shared/, D23).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    def send(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        """Send one message. Implementations must not raise for a merely
        unknown recipient; transport failures may raise and are handled by the
        caller."""
        raise NotImplementedError
