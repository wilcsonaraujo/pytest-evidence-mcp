from typing_extensions import TypedDict

from pytest_evidence_mcp.core.errors import (
    AmbiguousTestNameError,
    IncompleteEvidenceError,
    TestDidNotFailError,
    TestNotFoundError,
)
from pytest_evidence_mcp.core.truncate import DEFAULT_MAX_OUTPUT_CHARS, truncate_tail
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

def get_test_failure(test_name: str, path: str,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,) -> GetTestFailureOutput:
    """Return the full evidence pytest already collected for one failing test.

    Use after list_failed_tests. Delivers the error, the traceback and the
    output captured during that test — no diagnosis, only raw evidence.
    Large text fields (traceback, captured output, actual/expected) are
    truncated to `max_output_chars` (keeping the tail, where the relevant
    part usually is) to avoid blowing up the caller's context.
    """
    test_run, _metadata= resolve_test_run(path)
    test_case = test_run.find(test_name)

    if test_case is None:
        candidates = [t.nodeid for t in test_run.tests if t.name == test_name]
        if len(candidates) > 1:
            raise AmbiguousTestNameError(
                f"'{test_name}' matches {len(candidates)} tests in the last "
                f"run of {path} - use one of the full nodeids to "
                f"disambiguate: {', '.join(candidates)}"
            )
        raise TestNotFoundError(
            f"Test '{test_name}' not found in the last run of {path}"
        )

    if test_case.outcome not in ("failed", "error"):
        raise TestDidNotFailError(
            f"Test '{test_name}' did not fail (outcome: {test_case.outcome}) - nothing to report"
        )

    if test_case.failure is None:
        raise IncompleteEvidenceError(
            f"Test '{test_name}' has outcome={test_case.outcome!r} but the "
            f"report contains no failure details for it (possibly an "
            f"incomplete or partial report)"
        )

    return {
        "error_type": test_case.failure.error_type,
        "message": test_case.failure.message,
        "traceback": truncate_tail(test_case.failure.traceback, max_output_chars),
        "actual": truncate_tail(test_case.failure.actual, max_output_chars),
        "expected": truncate_tail(test_case.failure.expected, max_output_chars),
        "stdout": truncate_tail(test_case.captured.stdout, max_output_chars),
        "stderr": truncate_tail(test_case.captured.stderr, max_output_chars),
        "log": truncate_tail(test_case.captured.log, max_output_chars),
        "duration": test_case.duration_ms,
    }
