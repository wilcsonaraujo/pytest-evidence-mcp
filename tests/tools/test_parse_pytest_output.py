from pathlib import Path

from pytest_evidence_mcp.tools.parse_pytest_output import parse_pytest_output

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pytest_output" / "sample.txt"


def test_wraps_failures_with_low_confidence():
    result = parse_pytest_output(FIXTURE.read_text())

    assert result["confidence"] == "low"
    assert len(result["failures"]) == 3
    assert result["failures"][1]["test_name"] == "test_assert_fails"
