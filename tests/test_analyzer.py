from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from crash_summarizer.analyzer import render_markdown, summarize_report


SAMPLE_SUMMARY = {
    "headline": "Null dereference in request worker",
    "severity": "high",
    "confidence": 0.9,
    "incident_summary": "The request worker crashed while dereferencing a null value.",
    "fingerprint": "SIGSEGV:request_worker",
    "affected_components": ["request worker"],
    "evidence": ["SIGSEGV is present in the report"],
    "likely_root_causes": [
        {"cause": "Unchecked null value", "evidence": "Top frame dereferences ptr", "confidence": 0.85}
    ],
    "recommended_actions": [
        {"priority": "immediate", "action": "Add a null guard and reproduce with the same input."}
    ],
    "missing_information": ["Build identifier"],
}


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text=json.dumps(SAMPLE_SUMMARY))


class AnalyzerTests(unittest.TestCase):
    def test_uses_responses_api_with_strict_schema_and_no_storage(self):
        responses = FakeResponses()
        client = SimpleNamespace(responses=responses)

        result = summarize_report("SIGSEGV at request_worker", client=client)

        self.assertEqual(SAMPLE_SUMMARY, result)
        self.assertFalse(responses.kwargs["store"])
        self.assertTrue(responses.kwargs["text"]["format"]["strict"])
        self.assertEqual("json_schema", responses.kwargs["text"]["format"]["type"])

    def test_rejects_empty_report(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            summarize_report("  ", client=SimpleNamespace())

    def test_markdown_contains_core_sections(self):
        rendered = render_markdown(SAMPLE_SUMMARY)
        self.assertIn("# Null dereference", rendered)
        self.assertIn("**Severity:** HIGH", rendered)
        self.assertIn("## Likely root causes", rendered)
        self.assertIn("## Recommended actions", rendered)


if __name__ == "__main__":
    unittest.main()

