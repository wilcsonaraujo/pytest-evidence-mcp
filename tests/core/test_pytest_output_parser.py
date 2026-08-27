from pathlib import Path

import pytest

from pytest_evidence_mcp.core.errors import UnrecognizedOutputFormatError
from pytest_evidence_mcp.core.pytest_output_parser import parse_raw_text

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pytest_output" / "sample.txt"


def _load_fixture_text() -> str:
    return FIXTURE.read_text()


def test_finds_all_three_failures_and_errors():
    results = parse_raw_text(_load_fixture_text())

    assert len(results) == 3
    assert [r["test_name"] for r in results] == [
        "test_setup_error",
        "test_assert_fails",
        "test_raises",
    ]


def test_setup_error_has_error_outcome_and_correct_name():
    setup_error = parse_raw_text(_load_fixture_text())[0]

    assert setup_error["outcome"] == "error"
    assert setup_error["test_name"] == "test_setup_error"
    assert setup_error["error_type"] == "RuntimeError"
    assert setup_error["actual"] is None
    assert setup_error["expected"] is None


def test_assertion_failure_extracts_expected_and_actual():
    assertion_failure = parse_raw_text(_load_fixture_text())[1]

    assert assertion_failure["outcome"] == "failed"
    assert assertion_failure["error_type"] == "AssertionError"
    assert assertion_failure["actual"] == "500"
    assert assertion_failure["expected"] == "201"


def test_assertion_failure_captures_stdout_and_log():
    assertion_failure = parse_raw_text(_load_fixture_text())[1]

    assert assertion_failure["captured_stdout"] == "some captured stdout"
    assert "about to fail" in assertion_failure["captured_log"]
    assert assertion_failure["captured_stderr"] is None


def test_raised_exception_has_no_expected_actual():
    raised = parse_raw_text(_load_fixture_text())[2]

    assert raised["outcome"] == "failed"
    assert raised["error_type"] == "ValueError"
    assert raised["actual"] is None
    assert raised["expected"] is None


def test_duration_ms_is_always_none():
    results = parse_raw_text(_load_fixture_text())

    assert all(r["duration_ms"] is None for r in results)


def test_unrecognized_text_raises():
    with pytest.raises(UnrecognizedOutputFormatError):
        parse_raw_text("this is not pytest output at all")
