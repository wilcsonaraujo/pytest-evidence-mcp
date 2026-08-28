from pathlib import Path

from pytest_evidence_mcp.tools.parse_pytest_output import parse_pytest_output

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pytest_output" / "sample.txt"


def test_wraps_failures_with_low_confidence():
    result = parse_pytest_output(FIXTURE.read_text())

    assert result["confidence"] == "low"
    assert len(result["failures"]) == 3
    assert result["failures"][1]["test_name"] == "test_assert_fails"


def test_max_output_chars_truncates_large_traceback():
    result = parse_pytest_output(FIXTURE.read_text(), max_output_chars=10)

    tracebacks = [f["traceback"] for f in result["failures"] if f["traceback"]]
    assert tracebacks  # sanity check the fixture actually produced tracebacks
    assert all("chars omitted" in t for t in tracebacks)


def test_default_max_output_chars_does_not_truncate_sample_fixture():
    result = parse_pytest_output(FIXTURE.read_text())

    text_fields = ("traceback", "actual", "expected", "captured_stdout", "captured_stderr", "captured_log")
    for failure in result["failures"]:
        for field in text_fields:
            value = failure[field]
            if value:
                assert "chars omitted" not in value
