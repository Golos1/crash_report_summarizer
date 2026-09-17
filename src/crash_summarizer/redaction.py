"""Small, conservative redaction helpers for crash-report text."""

from __future__ import annotations

import re


_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?i)\b(authorization\s*:\s*(?:bearer|basic)\s+)[^\s,;]+"
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)"
            r"(\s*[:=]\s*)[\"']?[^\s,;\"']+"
        ),
        r"\1\2[REDACTED]",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED_OPENAI_KEY]"),
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED_AWS_ACCESS_KEY]",
    ),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
        "[REDACTED_PRIVATE_KEY]",
    ),
)


def redact_secrets(text: str) -> str:
    """Redact common credential shapes without altering ordinary stack traces."""

    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text

