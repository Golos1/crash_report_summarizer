"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from . import __version__
from .analyzer import DEFAULT_MODEL, render_markdown, summarize_report
from .redaction import redact_secrets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crash-summarizer",
        description="Summarize crash reports with the OpenAI Responses API.",
    )
    parser.add_argument(
        "reports",
        nargs="*",
        metavar="REPORT",
        help="Crash report file(s). Use '-' for stdin.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        help=f"OpenAI model (default: OPENAI_MODEL or {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write output to this file.")
    parser.add_argument(
        "--max-chars",
        type=positive_int,
        default=120_000,
        help="Maximum combined input characters (default: 120000).",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable local best-effort credential redaction.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def read_reports(paths: Sequence[str]) -> str:
    if not paths:
        if sys.stdin.isatty():
            raise ValueError("Provide at least one report path, or pipe a report to stdin.")
        paths = ["-"]

    chunks: list[str] = []
    used_stdin = False
    for name in paths:
        if name == "-":
            if used_stdin:
                raise ValueError("stdin ('-') may only be specified once.")
            used_stdin = True
            content = sys.stdin.read()
            label = "stdin"
        else:
            path = Path(name)
            if not path.is_file():
                raise ValueError(f"Report not found or not a file: {path}")
            content = path.read_text(encoding="utf-8", errors="replace")
            label = str(path)
        chunks.append(f"===== {label} =====\n{content}")
    return "\n\n".join(chunks)


def truncate_middle(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    marker = "\n\n[... middle of report omitted by crash-summarizer ...]\n\n"
    if limit <= len(marker):
        return text[:limit], True
    available = max(0, limit - len(marker))
    head = int(available * 0.6)
    tail = available - head
    return text[:head] + marker + (text[-tail:] if tail else ""), True


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = read_reports(args.reports)
        if not args.no_redact:
            report = redact_secrets(report)
        report, truncated = truncate_middle(report, args.max_chars)
        if truncated:
            print(
                f"warning: input exceeded {args.max_chars} characters; kept the beginning and end",
                file=sys.stderr,
            )
        summary = summarize_report(report, model=args.model)
        output = (
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json"
            else render_markdown(summary)
        )
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # OpenAI SDK exceptions derive from Exception; keep normal CLI output concise.
        print(f"error: OpenAI request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
