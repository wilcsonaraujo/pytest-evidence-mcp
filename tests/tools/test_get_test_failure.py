import json
import shutil
from pathlib import Path

import pytest

from pytest_evidence_mcp.core.errors import (
    AmbiguousTestNameError,
    IncompleteEvidenceError,
    TestDidNotFailError,
    TestNotFoundError,
)
from pytest_evidence_mcp.tools.get_test_failure import get_test_failure

FIXTURE_JSON = Path(__file__).parent.parent / "fixtures" / "json_report" / "sample.json"


def test_assertion_failure_returns_expected_and_actual(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    result = get_test_failure("test_assert_fails", str(tmp_path))

    assert result["error_type"] == "AssertionError"
    assert result["expected"] == "201"
    assert result["actual"] == "500"


def test_raised_exception_has_no_expected_actual(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    result = get_test_failure("test_raises", str(tmp_path))

    assert result["error_type"] == "ValueError"
    assert result["expected"] is None
    assert result["actual"] is None


def test_setup_error_is_reported(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    result = get_test_failure("test_setup_error", str(tmp_path))

    assert result["error_type"] == "RuntimeError"


def test_unknown_test_name_raises(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    with pytest.raises(TestNotFoundError):
        get_test_failure("test_that_does_not_exist", str(tmp_path))


def test_passing_test_raises_did_not_fail(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    with pytest.raises(TestDidNotFailError):
        get_test_failure("test_passes", str(tmp_path))


def test_max_output_chars_truncates_large_traceback(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    result = get_test_failure("test_assert_fails", str(tmp_path), max_output_chars=30)

    assert result["traceback"] is not None
    assert "chars omitted" in result["traceback"]
    assert result["traceback"].endswith("AssertionError")


def test_default_max_output_chars_does_not_truncate_small_fields(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    result = get_test_failure("test_assert_fails", str(tmp_path))

    assert result["traceback"] is not None
    assert "chars omitted" not in result["traceback"]


def test_ambiguous_short_name_raises_with_candidates(tmp_path):
    report = {
        "created": 1700000000.0,
        "summary": {"total": 2, "failed": 2},
        "tests": [
            {
                "nodeid": "tests/test_a.py::test_duplicate",
                "outcome": "failed",
                "call": {
                    "crash": {"message": "assert 1 == 2"},
                    "longrepr": "tests/test_a.py:2: AssertionError",
                    "duration": 0.01,
                },
                "setup": {},
                "teardown": {},
            },
            {
                "nodeid": "tests/test_b.py::test_duplicate",
                "outcome": "failed",
                "call": {
                    "crash": {"message": "assert 3 == 4"},
                    "longrepr": "tests/test_b.py:2: AssertionError",
                    "duration": 0.01,
                },
                "setup": {},
                "teardown": {},
            },
        ],
    }
    (tmp_path / ".report.json").write_text(json.dumps(report))

    with pytest.raises(AmbiguousTestNameError) as exc_info:
        get_test_failure("test_duplicate", str(tmp_path))

    assert "tests/test_a.py::test_duplicate" in str(exc_info.value)
    assert "tests/test_b.py::test_duplicate" in str(exc_info.value)


def test_ambiguous_short_name_resolved_by_full_nodeid(tmp_path):
    report = {
        "created": 1700000000.0,
        "summary": {"total": 2, "failed": 2},
        "tests": [
            {
                "nodeid": "tests/test_a.py::test_duplicate",
                "outcome": "failed",
                "call": {
                    "crash": {"message": "assert 1 == 2"},
                    "longrepr": "tests/test_a.py:2: AssertionError",
                    "duration": 0.01,
                },
                "setup": {},
                "teardown": {},
            },
            {
                "nodeid": "tests/test_b.py::test_duplicate",
                "outcome": "failed",
                "call": {
                    "crash": {"message": "assert 3 == 4"},
                    "longrepr": "tests/test_b.py:2: AssertionError",
                    "duration": 0.01,
                },
                "setup": {},
                "teardown": {},
            },
        ],
    }
    (tmp_path / ".report.json").write_text(json.dumps(report))

    result = get_test_failure("tests/test_a.py::test_duplicate", str(tmp_path))

    assert result["actual"] == "1"
    assert result["expected"] == "2"


def test_failed_outcome_without_crash_block_raises_incomplete_evidence(tmp_path):
    """Regression test for finding #5: a test can be reported with
    outcome='failed'/'error' but no 'crash' in any of its call/setup/teardown
    phases - e.g. a truncated or partially-written report. This must surface
    as a clean, specific IncompleteEvidenceError, not a None `failure` field
    silently treated as if the test had evidence to show.
    """
    report = {
        "created": 1700000000.0,
        "summary": {"total": 1, "failed": 1},
        "tests": [
            {
                "nodeid": "tests/test_x.py::test_incomplete",
                "outcome": "failed",
                "call": {},
                "setup": {},
                "teardown": {},
            },
        ],
    }
    (tmp_path / ".report.json").write_text(json.dumps(report))

    with pytest.raises(IncompleteEvidenceError):
        get_test_failure("test_incomplete", str(tmp_path))
