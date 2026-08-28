import xml.etree.ElementTree as ET  # only for the Element type hint below
from datetime import datetime
from pathlib import Path
from typing import Literal

import defusedxml.ElementTree as DefusedET  # actual parsing goes through here

from pytest_evidence_mcp.core.assertion import (
    derive_error_type_from_traceback,
    extract_actual_expected_safe,
)
from pytest_evidence_mcp.core.models import (
    CapturedOutput,
    FailureDetail,
    SourceKind,
    TestCaseResult,
    TestRun,
)


def _safe_int(value: str | None, default: int = 0) -> int:
    """Converts string to int with a safe fallback."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_float(value: str | None, default: float = 0.0) -> float:
    """Converts string to float with a safe fallback."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_timestamp(timestamp: str | None) -> datetime | None:
    """Parse JUnit XML timestamp to datetime.

    Real pytest output includes a UTC offset (e.g. '...T14:35:30.18-03:00'),
    which fromisoformat handles directly. Normalized to naive to match
    json_report.py's timestamps, so callers can compare against
    datetime.now() without worrying about timezones.
    """
    if not timestamp:
        return None

    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed


def _parse_testcase(element: ET.Element) -> TestCaseResult | None:
    """Parses a <testcase> element into a TestCaseResult."""
    outcome: Literal["passed", "failed", "error", "skipped"]
    
    name = element.get("name", "unknown")
    classname = element.get("classname", "")

    # KNOWN LIMITATION: junit's classname is dot-separated (JUnit/Java
    # convention, e.g. "tests.test_api.TestFoo") and doesn't preserve where
    # the file path ends and the class name begins - so this can't be
    # reliably converted back to pytest's real nodeid format
    # ("tests/test_api.py::TestFoo::test_bar"). For a bare function this
    # happens to be close ("tests.test_api::test_foo" vs the real
    # "tests/test_api.py::test_foo"), but for class-based tests it's wrong.
    # A disk-based reconstruction (probe candidate file paths) was
    # considered and rejected: it would couple this pure parser to the
    # project's filesystem, cost a stat() per dot-segment per test case on
    # every call (no caching, by design - see PRD section 6), and can fail
    # or pick the wrong candidate if files were moved/renamed between the
    # pytest run and this call - a realistic timing window given the
    # agent-driven workflow this MCP is built for. See PRD section 10 and
    # TestCaseResult.nodeid's docstring. Only affects the junit.xml-only
    # branch - nodeid from pytest-json-report is exact, straight from
    # pytest itself.
    nodeid = f"{classname}::{name}" if classname else name
    time_sec = _safe_float(element.get("time"), 0.0)
    duration_ms = int(time_sec * 1000) if time_sec > 0 else None

    # Checks children to decide the outcome.
    failure = element.find("failure")
    error = element.find("error")
    skipped = element.find("skipped")

    if failure is not None:
        outcome = "failed"
        # <failure> has no `type` attribute in real pytest output - derive
        # error_type from the traceback instead.
        traceback = failure.text
        message = failure.get("message", "") or (traceback or "")
        error_type = derive_error_type_from_traceback(traceback)

        actual, expected = extract_actual_expected_safe(message, error_type)

        failure_detail = FailureDetail(
            error_type=error_type,
            message=message,
            traceback=traceback,
            actual=actual,
            expected=expected,
        )

        return TestCaseResult(
            nodeid=nodeid,
            name=name,
            outcome=outcome,
            duration_ms=duration_ms,
            failure=failure_detail,
            captured=CapturedOutput(),
        )

    elif error is not None:
        outcome = "error"
        traceback = error.text
        message = error.get("message", "") or (traceback or "")
        error_type = derive_error_type_from_traceback(traceback)

        actual, expected = extract_actual_expected_safe(message, error_type)

        error_detail = FailureDetail(
            error_type=error_type,
            message=message,
            traceback=traceback,
            actual=actual,
            expected=expected,
        )

        return TestCaseResult(
            nodeid=nodeid,
            name=name,
            outcome=outcome,
            duration_ms=duration_ms,
            failure=error_detail,
            captured=CapturedOutput(),
        )

    elif skipped is not None:
        outcome = "skipped"
        skip_text = skipped.text or ""
        message = skip_text or skipped.get("message", "")

        return TestCaseResult(
            nodeid=nodeid,
            name=name,
            outcome=outcome,
            duration_ms=duration_ms,
            failure=None,
            captured=CapturedOutput(),
        )

    else:
        return TestCaseResult(
            nodeid=nodeid,
            name=name,
            outcome="passed",
            duration_ms=duration_ms,
            failure=None,
            captured=CapturedOutput(),
        )


def parse_junit_xml(
    file_path: Path, source: SourceKind = SourceKind.JUNITXML
) -> TestRun:
    """Parses a JUnit XML file into a TestRun object."""
    try:
        tree = DefusedET.parse(file_path)
        root = tree.getroot()
    except DefusedET.ParseError as e:
        raise ValueError(f"Invalid XML file: {file_path}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(f"JUnit XML file not found: {file_path}") from e

    if root is None:
        raise ValueError(f"Invalid JUnit XML: no root element in {file_path}")

    testsuite = root if root.tag == "testsuite" else root.find("testsuite")

    if testsuite is None:
        raise ValueError("Invalid JUnit XML: no <testsuite> element")

    total_tests = _safe_int(testsuite.get("tests"), 0)
    failures = _safe_int(testsuite.get("failures"), 0)
    errors = _safe_int(testsuite.get("errors"), 0)
    skipped = _safe_int(testsuite.get("skipped"), 0)

    generated_at = _parse_timestamp(testsuite.get("timestamp"))

    test_cases = []
    for testcase in testsuite.findall("testcase"):
        result = _parse_testcase(testcase)
        if result:
            test_cases.append(result)

    # Real pytest counts are always consistent, but a hand-edited or
    # truncated junit.xml could make this go negative - clamp defensively.
    passed = max(0, total_tests - failures - errors - skipped)

    return TestRun(
        source=source,
        generated_at=generated_at,
        total=total_tests,
        passed=passed,
        failed=failures + errors,
        skipped=skipped,
        tests=test_cases,
    )


def parse_junit_xml_safe(
    file_path: Path, source: SourceKind = SourceKind.JUNITXML
) -> TestRun | None:
    """Safe version of parse_junit_xml that does not raise an exception."""
    try:
        return parse_junit_xml(file_path, source)
    except (OSError, ValueError):
        return None
