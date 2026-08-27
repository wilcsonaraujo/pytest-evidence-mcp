from pathlib import Path

from pytest_evidence_mcp.sources.fixture_loader import load_fixture

FIXTURES = Path(__file__).parent.parent / "fixtures" / "inspect"


def test_loads_valid_json():
    data, error = load_fixture(FIXTURES / "valid.json")

    assert error is None
    assert data["user"]["name"] == "Alice"


def test_loads_valid_yaml():
    data, error = load_fixture(FIXTURES / "valid.yaml")

    assert error is None
    assert data["name"] == "Bob"


def test_malformed_json_returns_descriptive_error():
    data, error = load_fixture(FIXTURES / "malformed.json")

    assert data is None
    assert "Invalid JSON" in error


def test_missing_file_returns_descriptive_error(tmp_path):
    data, error = load_fixture(tmp_path / "does_not_exist.json")

    assert data is None
    assert "not found" in error.lower()


def test_unsupported_extension_returns_descriptive_error():
    data, error = load_fixture(FIXTURES / "unsupported.txt")

    assert data is None
    assert "Unsupported file extension" in error
