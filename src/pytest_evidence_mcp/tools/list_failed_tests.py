from datetime import datetime
from typing import Literal

from typing_extensions import TypedDict

from pytest_evidence_mcp.sources.resolver import resolve_test_run


class FailedTestEntry(TypedDict):
    nodeid: str
    name: str
    error_type: str | None


class ListFailedTestsOutput(TypedDict):
    source: Literal["json_report", "junitxml", "junitxml_subprocess"]
    generated_at: datetime | None
    age_seconds: float | None
    total: int
    passed: int
    failed: int
    skipped: int
    failed_tests: list[FailedTestEntry]


def list_failed_tests(path: str) -> ListFailedTestsOutput:
    """Summarise the most recent pytest run for a project.

    Start here: use it to find which tests failed before investigating any
    single one. `path` is the root of the project under investigation.

    `source` tells you where this data came from, and whether it's fresh:
    - "json_report": an existing pytest-json-report file was found and read.
    - "junitxml": an existing junit.xml file was found and read.
    - "junitxml_subprocess": no report existed, so this call just ran
      pytest for you, live, right now. This is a fresh execution, not a
      cached result - there is no caching in this branch. The report it
      generates is deleted right after parsing, so a repeated call without
      a persisted report re-runs pytest from scratch every time, at the
      same cost as the first call.
    """
    test_run, metadata = resolve_test_run(path)
    return {
        "source": metadata["source"],
        "generated_at": metadata["generated_at"],
        "age_seconds": metadata["age_seconds"],
        "total": test_run.total,
        "passed": test_run.passed,
        "failed": test_run.failed,
        "skipped": test_run.skipped,
        "failed_tests": [
            {
                "nodeid": t.nodeid,
                "name": t.name,
                "error_type": t.failure.error_type if t.failure else None,
            }
            for t in test_run.failed_tests()
        ],
    }
