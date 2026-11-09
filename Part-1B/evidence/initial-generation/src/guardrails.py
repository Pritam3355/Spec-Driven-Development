"""Deterministic output safety checks for the habit logger."""

import re

_PII_PATTERN = re.compile(
    r"\b\d{3}-\d{2}-\d{4}\b"
    r"|\b\d{13,19}\b"
    r"|(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])"
)
_DESTRUCTIVE_PATTERN = re.compile(
    r"\b(?:delete\s+all|reset\s+everything|wipe\s+my\s+data)\b",
    re.IGNORECASE,
)
_DESTRUCTIVE_QUESTION = (
    "I can't delete or reset data. Would you like help logging a habit instead?"
)


def safe_envelope(question: str) -> dict[str, object]:
    """Return a schema-valid clarification response."""
    safe_question = _PII_PATTERN.sub("[REDACTED]", question).strip()
    bounded_question = safe_question[:200] or "Could you clarify?"
    return {
        "intent": "clarify",
        "habit_name": None,
        "quantity": None,
        "unit": None,
        "date": None,
        "needs_clarification": True,
        "clarification_question": bounded_question,
    }


def apply(
    out: dict[str, object],
    raw: str,
    user_text: str,
) -> dict[str, object]:
    """Redact PII and block destructive intent in a parsed response."""
    if not isinstance(out, dict):
        return safe_envelope("I couldn't understand that. Could you clarify?")

    if _DESTRUCTIVE_PATTERN.search(user_text):
        return safe_envelope(_DESTRUCTIVE_QUESTION)

    sanitized = {
        key: _PII_PATTERN.sub("[REDACTED]", value)
        if isinstance(value, str)
        else value
        for key, value in out.items()
    }
    if _PII_PATTERN.search(str(sanitized)):
        return safe_envelope("I can't include sensitive information. Could you clarify?")

    return sanitized
