from datetime import datetime
from pathlib import Path

import pytest

from pytest_evidence_mcp.core.models import SourceKind
from pytest_evidence_mcp.sources.json_report import (
    parse_json_report,
    parse_json_report_safe,
)

FIXTURE = Path(__file__).parent.parent / "fixtures" / "json_report" / "sample.json"


@pytest.fixture
def test_run():
    return parse_json_report(FIXTURE)


def test_counters_and_source(test_run):
    assert test_run.source == SourceKind.JSON_REPORT
    assert test_run.total == 4
    assert test_run.passed == 1
    assert test_run.failed == 3
    assert test_run.skipped == 0


def test_generated_at_is_extracted_from_unix_timestamp(test_run):
    """`created` in this format is a Unix epoch float, not a string -
    confirmed by generating a real report, not assumed."""
    assert isinstance(test_run.generated_at, datetime)


def test_passing_test_has_no_failure(test_run):
    tc = test_run.find("test_passes")
    assert tc.outcome == "passed"
    assert tc.failure is None


def test_assertion_failure_extracts_expected_actual(test_run):
    tc = test_run.find("test_assert_fails")
    assert tc.outcome == "failed"
    assert tc.failure.error_type == "AssertionError"
    assert tc.failure.message == "assert 500 == 201"
    assert tc.failure.expected == "201"
    assert tc.failure.actual == "500"
    # longrepr, not the raw list of frames under "traceback"
    assert isinstance(tc.failure.traceback, str)
    assert "assert 500 == 201" in tc.failure.traceback


def test_captured_stdout_and_log_are_present(test_run):
    """Unlike JUnit XML, the JSON report carries stdout/log for free."""
    tc = test_run.find("test_assert_fails")
    assert tc.captured.stdout == "some captured stdout\n"
    assert tc.captured.log is not None
    assert "about to fail" in tc.captured.log


def test_raised_exception_gets_error_type_without_expected_actual(test_run):
    tc = test_run.find("test_raises")
    assert tc.outcome == "failed"
    assert tc.failure.error_type == "ValueError"
    assert tc.failure.expected is None
    assert tc.failure.actual is None


def test_setup_error_has_no_call_phase_but_is_still_captured(test_run):
    """The worst bug found in this file: a fixture that raises has no
    "call" phase at all - the crash lives in "setup" instead."""
    tc = test_run.find("test_setup_error")
    assert tc.outcome == "error"
    assert tc.failure is not None
    assert tc.failure.error_type == "RuntimeError"
    assert "fixture setup blew up" in tc.failure.message


def test_unknown_test_name_returns_none(test_run):
    assert test_run.find("does_not_exist") is None


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_json_report(Path("/no/such/file.json"))


def test_malformed_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(ValueError):
        parse_json_report(bad)


def test_safe_variant_returns_none_instead_of_raising():
    assert parse_json_report_safe(Path("/no/such/file.json")) is None
