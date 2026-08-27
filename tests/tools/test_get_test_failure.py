import shutil
from pathlib import Path

import pytest

from pytest_evidence_mcp.core.errors import TestDidNotFailError, TestNotFoundError
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
