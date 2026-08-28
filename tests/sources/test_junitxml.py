from datetime import datetime
from pathlib import Path

import pytest

from pytest_evidence_mcp.core.models import SourceKind
from pytest_evidence_mcp.sources.junitxml import (
    _parse_timestamp,
    parse_junit_xml,
    parse_junit_xml_safe,
)

FIXTURE = Path(__file__).parent.parent / "fixtures" / "junit" / "sample.xml"


@pytest.fixture
def test_run():
    return parse_junit_xml(FIXTURE)


def test_counters_and_source(test_run):
    assert test_run.source == SourceKind.JUNITXML
    assert test_run.total == 4
    assert test_run.passed == 1
    assert test_run.failed == 3  # 2 <failure> + 1 <error>
    assert test_run.skipped == 0


def test_generated_at_is_extracted(test_run):
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
    assert tc.failure.traceback  # full block present


def test_raised_exception_gets_error_type_without_expected_actual(test_run):
    tc = test_run.find("test_raises")
    assert tc.outcome == "failed"
    assert tc.failure.error_type == "ValueError"
    assert tc.failure.expected is None
    assert tc.failure.actual is None


def test_setup_error_is_captured_as_error_outcome(test_run):
    """The case that broke the original parser: a fixture that raises has
    no <failure>, only <error>, and pytest 9.x puts no `type=` attribute
    on either - error_type has to come from the traceback text.
    """
    tc = test_run.find("test_setup_error")
    assert tc.outcome == "error"
    assert tc.failure is not None
    assert tc.failure.error_type == "RuntimeError"


def test_captured_output_is_none_not_empty_string(test_run):
    """JUnit XML doesn't carry stdout/stderr/log unless junit_logging is
    configured on the target project - must be None, not "".
    """
    tc = test_run.find("test_assert_fails")
    assert tc.captured.stdout is None
    assert tc.captured.stderr is None
    assert tc.captured.log is None


def test_unknown_test_name_returns_none(test_run):
    assert test_run.find("does_not_exist") is None


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_junit_xml(Path("/no/such/file.xml"))


def test_malformed_xml_raises(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<not-even-closed>")
    with pytest.raises(ValueError):
        parse_junit_xml(bad)


def test_safe_variant_returns_none_instead_of_raising():
    assert parse_junit_xml_safe(Path("/no/such/file.xml")) is None


def test_same_instant_different_utc_offsets_produce_same_local_time():
    """Regression test for finding #7: the original code stripped tzinfo
    without converting first (`parsed.replace(tzinfo=None)`), so two
    timestamps representing the exact same instant but written with
    different UTC offsets produced two different naive datetimes - whichever
    offset happened to be in the file leaked straight through as if it were
    already local time. The fix calls `.astimezone()` before stripping, so
    the same instant must always produce the same naive local datetime,
    regardless of which offset the source used - and regardless of what the
    machine running this test considers "local", which is why this doesn't
    need to mock the timezone to be deterministic.
    """
    utc_offset = _parse_timestamp("2024-01-01T12:00:00+00:00")
    minus_three_offset = _parse_timestamp("2024-01-01T09:00:00-03:00")  # same instant

    assert utc_offset == minus_three_offset


def test_naive_timestamp_passes_through_unchanged():
    result = _parse_timestamp("2024-01-01T12:00:00")

    assert result == datetime(2024, 1, 1, 12, 0, 0)
    assert result.tzinfo is None


def test_none_and_malformed_timestamp_return_none():
    assert _parse_timestamp(None) is None
    assert _parse_timestamp("") is None
    assert _parse_timestamp("not-a-timestamp") is None
