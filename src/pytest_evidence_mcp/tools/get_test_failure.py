from typing_extensions import TypedDict

from pytest_evidence_mcp.core.errors import TestDidNotFailError, TestNotFoundError
from pytest_evidence_mcp.sources.resolver import resolve_test_run


class GetTestFailureOutput(TypedDict):
    error_type: str | None
    message: str | None
    traceback: str | None
    actual: str | None
    expected: str | None
    stdout: str | None
    stderr: str | None
    log: str | None
    duration: int | None

def get_test_failure(test_name: str, path: str) -> GetTestFailureOutput:
    """Return the full evidence pytest already collected for one failing test.

    Use after list_failed_tests. Delivers the error, the traceback and the
    output captured during that test — no diagnosis, only raw evidence.
    """
    test_run, _metadata= resolve_test_run(path)
    test_case = test_run.find(test_name)

    if test_case is None:
        raise TestNotFoundError(
            f"Test '{test_name}' not found in the last run of {path}"
        )

    if test_case.outcome not in ("failed", "error"):
        raise TestDidNotFailError(
            f"Test '{test_name}' did not fail (outcome: {test_case.outcome}) - nothing to report"
        )

    assert test_case.failure is not None, (
        f"outcome={test_case.outcome!r} but failure is None - parser bug in "
        f"json_report.py/junitxml.py, they should always populate both together"
    )

    return {
        "error_type": test_case.failure.error_type,
        "message": test_case.failure.message,
        "traceback": test_case.failure.traceback,
        "actual": test_case.failure.actual,
        "expected": test_case.failure.expected,
        "stdout": test_case.captured.stdout,
        "stderr": test_case.captured.stderr,
        "log": test_case.captured.log,
        "duration": test_case.duration_ms,
    }
