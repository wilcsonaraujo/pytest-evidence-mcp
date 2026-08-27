from pathlib import Path

import pytest

from pytest_evidence_mcp.core.errors import NoTestsCollectedError
from pytest_evidence_mcp.tools.list_failed_tests import list_failed_tests

SAMPLE_PROJECT = Path(__file__).parent.parent / "fixtures" / "sample_project"
EMPTY_PROJECT = Path(__file__).parent.parent / "fixtures" / "empty_project"


def test_summarises_a_real_run_with_one_failure():
    result = list_failed_tests(str(SAMPLE_PROJECT))

    assert result["total"] == 2
    assert result["passed"] == 1
    assert result["failed"] == 1
    assert result["skipped"] == 0
    assert result["source"] == "junitxml_subprocess"
    assert result["generated_at"] is not None
    assert result["age_seconds"] is not None

    assert len(result["failed_tests"]) == 1
    failed = result["failed_tests"][0]
    assert failed["name"] == "test_fails"
    assert failed["nodeid"].endswith("::test_fails")
    assert failed["error_type"] == "AssertionError"


def test_empty_project_raises_no_tests_collected():
    with pytest.raises(NoTestsCollectedError):
        list_failed_tests(str(EMPTY_PROJECT))
