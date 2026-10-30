"""Unit tests for http_retry_after_parser.core.

Deterministic: a fake clock replaces time.time so no test depends
on wall-clock time.
"""

import unittest

from http_retry_after_parser.core import (
    RetryAfterError,
    RetryAfterParser,
    RetryAfterResult,
)

FIXED_NOW = 1_700_000_000.0


def fake_clock() -> float:
    return FIXED_NOW


class TestDeltaSeconds(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = RetryAfterParser(clock=fake_clock)

    def test_positive_integer(self) -> None:
        result = self.parser.parse("120")
        self.assertEqual(result.delay_seconds, 120.0)
        self.assertIsNone(result.date)

    def test_zero_clamps_to_zero(self) -> None:
        result = self.parser.parse("0")
        self.assertEqual(result.delay_seconds, 0.0)
        self.assertIsNone(result.date)

    def test_large_value(self) -> None:
        result = self.parser.parse("2147483647")
        self.assertEqual(result.delay_seconds, 2147483647.0)
        self.assertIsNone(result.date)


class TestHttpDate(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = RetryAfterParser(clock=fake_clock)

    def test_future_date(self) -> None:
        result = self.parser.parse("Tue, 14 Nov 2023 22:26:00 GMT")
        self.assertGreater(result.delay_seconds, 0)
        self.assertAlmostEqual(
            result.delay_seconds, 760.0, places=1
        )

    def test_past_date_clamps_to_zero(self) -> None:
        result = self.parser.parse("Wed, 15 Nov 2017 06:25:24 GMT")
        self.assertEqual(result.delay_seconds, 0.0)
        self.assertIsNotNone(result.date)

    def test_date_is_returned_as_timestamp(self) -> None:
        result = self.parser.parse("Tue, 14 Nov 2023 22:26:00 GMT")
        self.assertEqual(result.date, 1_700_000_760.0)


class TestErrors(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = RetryAfterParser(clock=fake_clock)

    def test_empty_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("")

    def test_whitespace_only_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("   ")

    def test_non_numeric_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("abc")

    def test_float_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("120.5")

    def test_negative_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("-10")

    def test_garbage_with_digits_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("120 seconds")

    def test_unparseable_date_raises(self) -> None:
        with self.assertRaises(RetryAfterError):
            self.parser.parse("not a date")


class TestWhitespace(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = RetryAfterParser(clock=fake_clock)

    def test_seconds_with_padding(self) -> None:
        result = self.parser.parse("  120  ")
        self.assertEqual(result.delay_seconds, 120.0)
        self.assertIsNone(result.date)

    def test_date_with_padding(self) -> None:
        padded = "  Tue, 14 Nov 2023 22:26:00 GMT  "
        result = self.parser.parse(padded)
        self.assertGreater(result.delay_seconds, 0)


if __name__ == "__main__":
    unittest.main()
