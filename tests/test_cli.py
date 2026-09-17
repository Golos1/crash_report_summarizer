from __future__ import annotations

import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from crash_summarizer.cli import read_reports, truncate_middle
from crash_summarizer.redaction import redact_secrets


class CliTests(unittest.TestCase):
    def test_reads_multiple_reports_with_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "one.log"
            second = Path(directory) / "two.log"
            first.write_text("first crash", encoding="utf-8")
            second.write_text("second crash", encoding="utf-8")

            result = read_reports([str(first), str(second)])

        self.assertIn("one.log", result)
        self.assertIn("first crash", result)
        self.assertIn("two.log", result)

    def test_reads_stdin(self):
        fake_stdin = io.StringIO("trace from stdin")
        with patch("sys.stdin", fake_stdin):
            result = read_reports(["-"])
        self.assertIn("trace from stdin", result)

    def test_truncation_preserves_start_and_end(self):
        text = "A" * 100 + "B" * 100
        result, truncated = truncate_middle(text, 100)
        self.assertTrue(truncated)
        self.assertLessEqual(len(result), 100)
        self.assertTrue(result.startswith("A"))
        self.assertTrue(result.endswith("B"))

    def test_redacts_common_credentials(self):
        text = "Authorization: Bearer secret-token api_key=abc123 password: hunter2"
        redacted = redact_secrets(text)
        self.assertNotIn("secret-token", redacted)
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("hunter2", redacted)
        self.assertIn("[REDACTED]", redacted)


if __name__ == "__main__":
    unittest.main()

