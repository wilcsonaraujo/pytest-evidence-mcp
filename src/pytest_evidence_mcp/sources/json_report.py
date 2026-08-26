import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from pytest_evidence_mcp.core.assertion import extract_actual_expected_safe
from pytest_evidence_mcp.core.models import (
    CapturedOutput,
    FailureDetail,
    SourceKind,
    TestCaseResult,
    TestRun,
)


def _extract_name_from_nodeid(nodeid: str) -> str:
    """Extracts the short name from the node ID."""
    parts = nodeid.split("::")
    return parts[-1] if parts else nodeid


def _flatten_log_records(log_data: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Flattens a list of LogRecords into text."""
    if not log_data:
        return None

    lines = []
    for entry in log_data:
        # The log can be in "record" or in entry
        record = entry.get("record", entry)
        levelname = record.get("levelname", "INFO")
        name = record.get("name", "")
        msg = record.get("msg", "")

        if name:
            lines.append(f"{levelname} {name}: {msg}")
        else:
            lines.append(f"{levelname}: {msg}")

    return "\n".join(lines) if lines else None


def _parse_timestamp(timestamp: Optional[float]) -> Optional[datetime]:
    """Parse timestamp from JSON report to datetime."""
    if not timestamp:
        return None

    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(timestamp)
    except (TypeError, ValueError, OSError) as e:
        return None


def _parse_test_case(test_data: Dict[str, Any]) -> Optional[TestCaseResult]:
    """Parses a test from the JSON report into a TestCaseResult."""
    nodeid = test_data.get("nodeid", "unknown")
    name = _extract_name_from_nodeid(nodeid)
    outcome = test_data.get("outcome", "")

    call = test_data.get("call", {})
    duration = call.get("duration", 0.0)
    duration_ms = int(duration * 1000) if duration > 0 else None

    captured = CapturedOutput(
        stdout=call.get("stdout"),
        stderr=call.get("stderr"),
        log=_flatten_log_records(call.get("log")),
    )

    phase = call if call.get("crash") else test_data.get("setup", {})
    if not phase.get("crash"):
        phase = test_data.get("teardown", {})

    failure = None

    if phase.get("crash") and outcome in ("failed", "error"):
        crash = phase["crash"]
        message = crash.get("message", "")
        traceback = phase.get("longrepr")

        if ":" in message and not message.startswith("assert"):
            error_type = message.split(":", 1)[0].strip()
        else:
            error_type = "AssertionError"

        actual, expected = extract_actual_expected_safe(message, error_type)

        failure = FailureDetail(
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
        failure=failure,
        captured=captured,
    )


def parse_json_report(
    file_path: Path, source: SourceKind = SourceKind.JSON_REPORT
) -> TestRun:
    """Parses a .report.json file into a TestRun object."""

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {file_path}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(f"JSON report file not found: {file_path}") from e

    summary = data.get("summary", {})
    total_tests = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)

    created = data.get("created")
    generated_at = _parse_timestamp(created) if created else None

    tests_data = data.get("tests", [])
    test_cases = []

    for test_data in tests_data:
        test_case = _parse_test_case(test_data)
        if test_case:
            test_cases.append(test_case)

    return TestRun(
        source=source,
        generated_at=generated_at,
        total=total_tests,
        passed=passed,
        failed=failed,
        skipped=skipped,
        tests=test_cases,
    )


def parse_json_report_safe(
    file_path: Path, source: SourceKind = SourceKind.JSON_REPORT
) -> Optional[TestRun]:
    """Safe version of parse_json_report that does not raise an exception"""
    try:
        return parse_json_report(file_path, source)
    except Exception as e:
        return None
