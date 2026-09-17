# Crash Summarizer

A small Python CLI that turns stack traces, crash dumps, and error logs into structured
triage summaries using the OpenAI Responses API.

It provides:

- Markdown output for humans and JSON output for automation
- strict structured output for predictable results
- multiple input files or stdin
- local best-effort redaction of common credentials
- explicit evidence, ranked root-cause hypotheses, next actions, and missing context
- `store=False` on API requests

## Install

Python 3.10 or newer is required.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Set your API key in the environment:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

On macOS or Linux:

```bash
export OPENAI_API_KEY="your-api-key"
```

## Use

Summarize one report:

```bash
crash-summarizer crash.log
```

Combine related reports and save a Markdown summary:

```bash
crash-summarizer app.log system.log -o summary.md
```

Pipe a report and produce JSON:

```bash
cat crash.log | crash-summarizer --format json
```

PowerShell equivalent:

```powershell
Get-Content crash.log -Raw | crash-summarizer --format json
```

Choose a different model or input limit:

```bash
crash-summarizer crash.log --model gpt-5.4 --max-chars 200000
```

The default model is `gpt-5.4-mini`. `OPENAI_MODEL` can set another default.

Redaction is intentionally conservative and cannot guarantee removal of every secret or piece
of personal data. Review sensitive crash reports before sending them to any external service.
Use `--no-redact` only when you intentionally want the original text sent.

## Develop and test

The test suite uses only the Python standard library and does not make API requests:

```bash
python -m unittest discover -s tests -v
```

The API layer is isolated in `src/crash_summarizer/analyzer.py`, so it is easy to inject a
fake client or add organization-specific preprocessing.
