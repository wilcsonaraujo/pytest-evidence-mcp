from pathlib import Path

from pytest_evidence_mcp.tools.inspect_fixture import inspect_fixture

FIXTURES = Path(__file__).parent.parent / "fixtures" / "inspect"


def test_valid_fixture_returns_valid_true_with_counts():
    result = inspect_fixture(str(FIXTURES / "valid.json"))

    assert result["valid"] is True
    assert result["field_count"] == 6
    assert result["null_fields"] == ["user.email"]
    assert result["types"]["active"] == "boolean"


def test_malformed_fixture_returns_valid_false_with_message():
    result = inspect_fixture(str(FIXTURES / "malformed.json"))

    assert result["valid"] is False
    assert "Invalid JSON" in result["message"]


def test_missing_fixture_returns_valid_false_with_message(tmp_path):
    result = inspect_fixture(str(tmp_path / "does_not_exist.json"))

    assert result["valid"] is False
    assert "not found" in result["message"].lower()
