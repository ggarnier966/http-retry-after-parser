# http-retry-after-parser

Converts a `Retry-After` HTTP header value into a delay in seconds, supporting both the delta-seconds form (`"120"`) and the HTTP-date form (`"Wed, 15 Nov 2023 06:35:40 GMT"`).

```python
from http_retry_after_parser import RetryAfterParser, RetryAfterResult, RetryAfterError

parser = RetryAfterParser()
result = parser.parse("120")
print(result.delay_seconds)  # 120.0

result = parser.parse("Wed, 15 Nov 2023 06:35:40 GMT")
print(result.delay_seconds)  # seconds from now until that date
print(result.date)           # absolute timestamp, or None for delta form
```

## Why

When a service returns 429 or 503 with `Retry-After`, a client needs a concrete delay. Handling both the integer-seconds and HTTP-date variants inline gets repetitive and error-prone, especially around past dates and zero values. This library does that one job and nothing else.

The parser accepts a `clock` callable so tests (and offline environments) are deterministic; by default it uses `time.time`.

## Edge cases

- A past HTTP-date clamps to a zero delay — retry immediately.
- `"0"` is accepted and yields a zero delay.
- Fractional seconds (`"120.5"`) are rejected. RFC 7231 specifies integer delta-seconds, and accepting floats would imply a precision the protocol does not guarantee.
- Only the IMF-fixdate date format (the RFC 7231 preferred form) is reliably supported via Python's `email.utils.parsedate_to_datetime`.
