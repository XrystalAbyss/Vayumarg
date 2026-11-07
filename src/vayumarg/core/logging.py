"""Structured and sanitized logging for Vayumarg.

Ensures no credentials, secret tokens, or sensitive connection parameters
are leaked into log streams or persisted files.
"""

import logging
import re
import sys

# Sensitive regex patterns to redact
SENSITIVE_PATTERNS = [
    re.compile(r"(password|passwd|pwd|secret|token|api_key)=['\"]?[^'\";\s]+['\"]?", re.IGNORECASE),
    re.compile(r"(postgres(?:ql)?(?:\+[a-z0-9]+)?://[^:]+:)([^@]+)(@)", re.IGNORECASE),
]


class SanitizingFormatter(logging.Formatter):
    """Custom formatter that automatically redacts credentials."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in SENSITIVE_PATTERNS:
            if pattern.groups == 3:
                # e.g., postgresql://user:password@host
                msg = pattern.sub(r"\1***REDACTED***\3", msg)
            else:
                msg = pattern.sub(r"\1=***REDACTED***", msg)
        return msg


def get_logger(name: str = "vayumarg") -> logging.Logger:
    """Create or retrieve a pre-configured, sanitized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SanitizingFormatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
