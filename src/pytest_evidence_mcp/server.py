from mcp.server import MCPServer

from pytest_evidence_mcp.core.errors import EvidenceError
from pytest_evidence_mcp.tools.get_test_failure import get_test_failure
from pytest_evidence_mcp.tools.list_failed_tests import list_failed_tests

mcp = MCPServer("pytest-evidence-mcp", version="0.1.0")

mcp.add_tool(list_failed_tests)
mcp.add_tool(get_test_failure)


@mcp.tool()
def inspect_fixture(path: str):
    """Inspect a JSON or YAML fixture file used by a test.

    Use to check whether the failure comes from the input data itself.
    `path` points to the fixture file, not to the project.
    """

    raise EvidenceError("inspect_fixture is not implemented yet")


@mcp.tool()
def parse_pytest_output(raw_text: str):
    """Extract failure evidence from raw pytest terminal output.

    Last-resort fallback for when pytest cannot be run again and the output
    was pasted by hand. Less reliable than the other tools.
    """

    raise EvidenceError("parse_pytest_output is not implemented yet")
