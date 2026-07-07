"""Password strength policy — single source of truth for register and reset.

Aligned with NIST SP 800-63B: favor length over forced composition, block
known-weak/common passwords and trivial values, and never impose rules that
push users toward predictable patterns. The frontend mirrors these checks in
`lib/auth/passwordPolicy.ts` for live UX feedback; this module is the
authoritative gate (the frontend cannot be trusted). Red zone (AI_RULES.md).
"""

from __future__ import annotations

MIN_LENGTH = 8
MAX_LENGTH = 128

# A short, deliberately small blocklist of the most common/leaked passwords and
# obvious app-specific guesses. Not a full breach corpus (that would need a
# dependency/dataset — out of MVP scope, Risk #3); it stops the worst offenders
# that a strength meter alone would still let through. Compared lowercased.
COMMON_PASSWORDS: frozenset[str] = frozenset(
    {
        "password",
        "password1",
        "password123",
        "passw0rd",
        "12345678",
        "123456789",
        "1234567890",
        "qwerty",
        "qwerty123",
        "qwertyuiop",
        "111111",
        "11111111",
        "abc12345",
        "iloveyou",
        "admin",
        "administrator",
        "welcome",
        "welcome1",
        "letmein",
        "monkey",
        "dragon",
        "sunshine",
        "princess",
        "football",
        "baseball",
        "trustno1",
        "changeme",
        "secret",
        "master",
        "superman",
        "ccsa",
        "ccsa1234",
        "savings",
        "creditcard",
    }
)


def password_issues(password: str, email: str | None = None) -> list[str]:
    """Return a list of human-readable problems; empty list means acceptable.

    Kept as a list (not a bool) so the same rules drive both the API error and
    the frontend hint copy without diverging.
    """
    issues: list[str] = []

    if len(password) < MIN_LENGTH:
        issues.append(f"Use at least {MIN_LENGTH} characters")
    if len(password) > MAX_LENGTH:
        issues.append(f"Use at most {MAX_LENGTH} characters")

    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        issues.append("This password is too common — choose something less predictable")

    if email:
        local_part = email.split("@", 1)[0].strip().lower()
        if local_part and local_part in lowered:
            issues.append("Do not include your email in your password")

    stripped = password.strip()
    if stripped and len(set(stripped)) == 1:
        issues.append("Avoid repeating a single character")

    return issues


def validate_password(password: str, email: str | None = None) -> None:
    """Raise ValueError with the first problem if the password is unacceptable."""
    issues = password_issues(password, email)
    if issues:
        raise ValueError(issues[0])
