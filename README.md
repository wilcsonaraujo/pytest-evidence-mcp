# pytest-evidence-mcp

MCP server that gives an AI agent access to structured evidence about pytest test failures.

The server delivers deterministic data — it does not diagnose. Diagnosis is the agent's job.

> Work in progress. Full installation and usage documentation is tracked in US-08.

## Development

```bash
pip install -e ".[dev]"
mcp dev src/pytest_evidence_mcp/server.py
```
