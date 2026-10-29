"""Parse HTTP Retry-After headers into delays.

Supports both the delta-seconds form (RFC 7231 §7.1.3) and the
HTTP-date form (RFC 7231 §7.1.1, IMF-fixdate subset of RFC 1123).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

_SECONDS_RE = re.compile(r"^\d+$")


class RetryAfterError(ValueError):
    """Raised when a Retry-After value cannot be interpreted."""


@dataclass(frozen=True)
class RetryAfterResult:
    """The interpretation of a Retry-After header.

    delay_seconds: wait in seconds from now (always >= 0).
    date: when the server suggests retrying, or None for delta-seconds.
    """

    delay_seconds: float
    date: float | None


class RetryAfterParser:
    """Convert a Retry-After header into a delay.

    A clock function is accepted so tests are deterministic. By default
    the real time.time is used.

    Non-integer delta values (e.g. "120.5") are rejected: RFC 7231
    specifies integer seconds, and accepting floats would imply a
    precision the protocol does not guarantee.

    A zero or negative delta clamps to 0 — servers occasionally send
    "0" to mean "retry immediately," and a negative delay is
    operationally identical.
    """

    def __init__(self, clock=time.time) -> None:
        self._clock = clock

    def parse(self, header: str) -> RetryAfterResult:
        if header is None:
            raise RetryAfterError("header is None")
        text = header.strip()
        if not text:
            raise RetryAfterError("empty header")

        if _SECONDS_RE.match(text):
            value = int(text)
            if value < 0:
                raise RetryAfterError("negative delta not allowed: " + text)
            delay = float(value) if value > 0 else 0.0
            return RetryAfterResult(delay_seconds=delay, date=None)

        try:
            dt = parsedate_to_datetime(text)
        except (TypeError, ValueError) as exc:
            raise RetryAfterError("unparseable Retry-After: " + text) from exc
        if dt is None:
            raise RetryAfterError("unparseable Retry-After: " + text)

        target = dt.timestamp()
        now = self._clock()
        delay = target - now
        if delay < 0:
            delay = 0.0
        return RetryAfterResult(delay_seconds=delay, date=target)
