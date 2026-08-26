from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SourceKind(str, Enum):
    """Which branch of the priority chain produced this TestRun."""

    JSON_REPORT = "json_report"
    JUNITXML = "junitxml"
    JUNITXML_SUBPROCESS = "junitxml_subprocess"


class FailureDetail(BaseModel):
    """Present only when a test's outcome is failed or error."""

    error_type: str | None = None
    message: str | None = None
    traceback: str | None = None
    actual: str | None = None
    expected: str | None = None


class CapturedOutput(BaseModel):
    """Each field is None when the source format doesn't provide it —
    never "" for "provided but empty". See TestRun.source to know what
    a given source is capable of carrying.
    """

    stdout: str | None = None
    stderr: str | None = None
    log: str | None = None


class TestCaseResult(BaseModel):
    nodeid: str = Field(
        description="Full pytest nodeid, e.g. 'tests/test_api.py::test_foo'."
    )
    name: str = Field(
        description="Short name, e.g. 'test_foo'. Convenience for display/matching."
    )
    outcome: Literal["passed", "failed", "error", "skipped"]
    duration_ms: int | None = None
    failure: FailureDetail | None = None
    captured: CapturedOutput = Field(default_factory=CapturedOutput)


class TestRun(BaseModel):
    """Internal, normalized result of one pytest execution.
    Every source parser (json_report.py, junitxml.py) produces this.
    Tools never see the raw XML/JSON — only this.
    """

    source: SourceKind
    generated_at: datetime | None = Field(
        default=None,
        description="When the underlying report was generated. None if unknown "
        "(shouldn't happen in practice, but parsers must not fabricate a value).",
    )
    total: int
    passed: int
    failed: int
    skipped: int
    tests: list[TestCaseResult] = Field(default_factory=list)

    def failed_tests(self) -> list[TestCaseResult]:
        return [test for test in self.tests if test.outcome in ("failed", "error")]

    def get_parse_passed(test_run: TestRun) -> list[TestCaseResult]:
        """Returns only the test cases that passed."""
        return [tc for tc in test_run.tests if tc.outcome == "passed"]

    def get_parse_skipped(test_run: TestRun) -> list[TestCaseResult]:
        """Returns only the skipped test cases."""
        return [tc for tc in test_run.tests if tc.outcome == "skipped"]

    def find(self, nodeid_or_name: str) -> TestCaseResult | None:
        """Look up by full nodeid first, then by short name. Returns None,
        never raises — callers decide what "not found" means for them.
        """
        for test in self.tests:
            if test.nodeid == nodeid_or_name:
                return test
        matches = [test for test in self.tests if test.name == nodeid_or_name]
        return matches[0] if len(matches) == 1 else None
