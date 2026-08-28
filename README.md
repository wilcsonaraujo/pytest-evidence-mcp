# pytest-evidence-mcp

MCP server that gives an AI agent access to structured evidence about pytest test failures.

The server delivers deterministic data — it does not diagnose. Diagnosis is the agent's job. It exposes four tools (`list_failed_tests`, `get_test_failure`, `inspect_fixture`, `parse_pytest_output`), one documentation resource per tool, and one prompt template per tool.

## Prerequisites

- Python 3.10+ to run this MCP server itself.
- pytest installed in the **target project's own environment** (the project being investigated), not in this server's environment. This server does not depend on pytest as a package — it locates and calls the pytest already installed where the code under investigation lives (its `.venv`, by default). If pytest isn't installed there, `list_failed_tests`/`get_test_failure` raise `PytestNotFoundError` with a clean message instead of crashing.
- An MCP client that supports stdio transport (Claude Code, VS Code with the Copilot Chat MCP integration, or any other MCP-compatible client).

## Installation

```bash
git clone <repo-url>
cd pytest-evidence-mcp
python -m venv .venv
.venv/bin/pip install -e ".[dev]"      # Linux/macOS
.venv\Scripts\pip install -e ".[dev]"  # Windows
```

To confirm it starts correctly:

```bash
.venv/bin/python -m pytest_evidence_mcp
```

It should log `Starting MCP Server.` to stderr and wait on stdin (this is a stdio server — it isn't meant to be run standalone in a terminal for regular use, only to sanity-check the install). Stop it with Ctrl+C.

## Registering with an MCP client

The server is started with `python -m pytest_evidence_mcp`, using the interpreter from the `.venv` created above.

**Claude Code:**

```bash
claude mcp add --transport stdio --scope project pytest-evidence-mcp -- "/absolute/path/to/pytest-evidence-mcp/.venv/bin/python" -m pytest_evidence_mcp
```

On Windows, point to `.venv\Scripts\python.exe` instead. Claude Code only loads MCP servers when a session starts — if you register the server while a session is already open, restart the session (or run `/mcp`) before using the tools.

**VS Code (Copilot Chat), `.vscode/mcp.json` in the workspace you'll investigate:**

```json
{
  "servers": {
    "pytest-evidence-mcp": {
      "type": "stdio",
      "command": "/absolute/path/to/pytest-evidence-mcp/.venv/bin/python",
      "args": ["-m", "pytest_evidence_mcp"]
    }
  }
}
```

Any other MCP client that supports a generic stdio server definition (`command` + `args`) can be registered the same way.

## How it decides where the data comes from

`list_failed_tests` and `get_test_failure` resolve the most recent test run for a project through a priority chain, tried in order:

1. **`.report.json`** (pytest-json-report) — read if it exists, at the path declared in the project's own pytest config (`addopts` in `pytest.ini`, `pyproject.toml`, `tox.ini` or `setup.cfg`, in that precedence order) or at the default `.report.json`.
2. **`junit.xml`** — same lookup, falling back to the default `junit.xml`.
3. **Run pytest now**, via subprocess, if neither report exists. This is a real, fresh execution every time — the temporary report it generates is deleted right after parsing, so there is no caching in this branch, and a repeated call without a persisted report re-runs the whole suite from scratch.

The `source` field in `list_failed_tests`' output tells you which branch was used, and `age_seconds` tells you how old that data is.

## The four tools

### `list_failed_tests(path: str)`

Summarizes the most recent pytest run for a project. Always the starting point of an investigation.

Input:
```json
{ "path": "/home/dev/my-project" }
```

Output:
```json
{
  "source": "json_report",
  "generated_at": "2026-08-28T14:35:30.180000",
  "age_seconds": 12.4,
  "total": 42,
  "passed": 40,
  "failed": 2,
  "skipped": 0,
  "failed_tests": [
    {
      "nodeid": "tests/test_checkout.py::test_apply_discount",
      "name": "test_apply_discount",
      "error_type": "AssertionError"
    },
    {
      "nodeid": "tests/test_checkout.py::test_apply_discount_negative",
      "name": "test_apply_discount_negative",
      "error_type": "AssertionError"
    }
  ]
}
```

A project where nothing fails returns `failed_tests: []`, not an error.

### `get_test_failure(test_name: str, path: str, max_output_chars: int = 10000)`

Returns the full evidence pytest already collected for one failing test: error, traceback, captured output. No diagnosis.

Input:
```json
{ "test_name": "test_apply_discount", "path": "/home/dev/my-project" }
```

Output:
```json
{
  "error_type": "AssertionError",
  "message": "assert 90 == 9.0",
  "traceback": "def test_apply_discount():\n>       assert apply_discount(100, 10) == 9.0\nE       AssertionError: assert 90 == 9.0\n\ntests/test_checkout.py:14: AssertionError",
  "actual": "90",
  "expected": "9.0",
  "stdout": null,
  "stderr": null,
  "log": null,
  "duration_ms": 3
}
```

`test_name` accepts either the short name (`test_apply_discount`) or a full nodeid (`tests/test_checkout.py::test_apply_discount`). If the short name matches more than one test, the call raises `AmbiguousTestNameError` listing every matching nodeid — retry with the full nodeid from that list.

Large fields (`traceback`, `actual`, `expected`, `stdout`, `stderr`, `log`) are truncated to `max_output_chars`, keeping the tail (where the relevant part usually is) and prefixing a `...[N chars omitted]...` note.

### `inspect_fixture(path: str)`

Inspects a JSON or YAML fixture file used by a test, to check whether a failure comes from the input data itself rather than the code. `path` points to the fixture file, not to the project root.

Input:
```json
{ "path": "/home/dev/my-project/fixtures/orders.json" }
```

Output:
```json
{
  "valid": true,
  "field_count": 6,
  "null_fields": [],
  "types": {
    "orders[].id": "integer",
    "orders[].customer": "string",
    "orders[].total": "float",
    "orders[23].id": "integer",
    "orders[23].customer": "string",
    "orders[23].total": "string"
  },
  "collapsed_lists": {
    "orders": 49
  }
}
```

Lists longer than 10 items get their majority shape collapsed into a single `path[]` entry (`collapsed_lists` records how many items share that shape), so the output stays bounded on large fixtures. Any item whose shape doesn't match the majority — like `orders[23]` above, where `total` is a string instead of a float — is still reported individually, in full, by its real index. That is usually the actual cause of the failure.

An invalid or unparsable file returns `{"valid": false, "message": "..."}` instead of raising.

### `parse_pytest_output(raw_text: str, max_output_chars: int = 10000)`

Last-resort fallback: extracts failure evidence directly from raw pytest terminal output, for when pytest can't be run again and no `.report.json`/`junit.xml` is available (e.g. output pasted from a CI log).

Input:
```json
{ "raw_text": "=================== FAILURES ===================\n_____ test_apply_discount _____\n\n    def test_apply_discount():\n>       assert apply_discount(100, 10) == 9.0\nE       AssertionError: assert 90 == 9.0\n\ntests/test_checkout.py:14: AssertionError\n=============== 1 failed, 41 passed in 0.42s ===============" }
```

Output:
```json
{
  "confidence": "low",
  "failures": [
    {
      "test_name": "test_apply_discount",
      "outcome": "failed",
      "error_type": "AssertionError",
      "message": "assert 90 == 9.0",
      "traceback": "...",
      "actual": "90",
      "expected": "9.0",
      "captured_stdout": null,
      "captured_stderr": null,
      "captured_log": null,
      "duration_ms": null
    }
  ]
}
```

**Known limitation:** this parser recognizes pytest's own default output format (the `=== FAILURES ===` / `==== ERRORS ====` sections and their `----- Captured stdout call -----` subsections). It does not understand output reformatted by a different plugin — most commonly **pytest-sugar**, which changes the layout enough that these sections stop being recognizable. If the target project has pytest-sugar (or a similar output plugin) installed and active, either disable it for the run you're capturing (`pytest -p no:sugar`) or use one of the structured sources (branches 1/2 above) instead. `confidence: "low"` on every response from this tool is a permanent reminder that, unlike the other three tools, this one is reconstructing evidence from free text rather than reading a structured report — treat it as a fallback, not a primary source.

## Error handling

Every domain error (`PytestNotFoundError`, `TestNotFoundError`, `AmbiguousTestNameError`, `IncompleteEvidenceError`, and others in `core/errors.py`) reaches the calling agent as a clean MCP tool error with a descriptive message, not as a crash or a silently swallowed exception. If a tool call fails, the message itself usually says exactly what to do next (e.g. "install pytest", "use one of these full nodeids").

## Resources and prompts

Each tool also has a matching documentation resource (`docs://tools/<tool_name>`) with its machine-readable contract, and a prompt template (`<tool_name>_prompt`) that fills in a ready-to-send instruction for that tool given the same arguments. These exist so a client can introspect a tool's real input/output shape, or start an investigation, without leaving the chat.

## Development

```bash
pip install -e ".[dev]"
mcp dev src/pytest_evidence_mcp/server.py
```

Run the test suite and checks:

```bash
pytest
mypy src/
ruff check .
```
