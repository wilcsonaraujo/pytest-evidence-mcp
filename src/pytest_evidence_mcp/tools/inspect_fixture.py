from pathlib import Path

from pytest_evidence_mcp.core.fixture_inspection import inspect
from pytest_evidence_mcp.sources.fixture_loader import load_fixture


def inspect_fixture(path: str):
    """Inspect a JSON or YAML fixture file used by a test.

    Use to check whether the failure comes from the input data itself.
    `path` points to the fixture file, not to the project.
    """
    data, error = load_fixture(Path(path))

    if error:
        return {"valid": False, "message": error}

    result = inspect(data)

    return {
        "valid": True,
        "field_count": result["field_count"],
        "null_fields": result["null_fields"],
        "types": result["types"],
    }
