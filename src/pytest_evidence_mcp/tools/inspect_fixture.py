from pathlib import Path
from typing import Literal

from typing_extensions import TypedDict

from pytest_evidence_mcp.core.fixture_inspection import inspect
from pytest_evidence_mcp.sources.fixture_loader import load_fixture


class InspectFixtureValid(TypedDict):
    valid: Literal[True]
    field_count: int
    null_fields: list[str]
    types: dict[str, str]
    collapsed_lists: dict[str, int]


class InspectFixtureInvalid(TypedDict):
    valid: Literal[False]
    message: str


def inspect_fixture(path: str) -> InspectFixtureValid | InspectFixtureInvalid:
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
        "collapsed_lists": result["collapsed_lists"],
    }
