from mcp.server import MCPServer

from pytest_evidence_mcp.tools.errors import EvidenceError

mcp = MCPServer("pytest-evidence-mcp")


@mcp.tool()
def list_failed_tests(path: str = "."):
    """Summarise the most recent pytest run for a project.

    Start here: use it to find which tests failed before investigating any
    single one. `path` is the root of the project under investigation.
    """

    raise EvidenceError("list_failed_tests is not implemented yet")


@mcp.tool()
def get_test_failure(test_name: str, path: str = "."):
    """Return the full evidence pytest already collected for one failing test.

    Use after list_failed_tests. Delivers the error, the traceback and the
    output captured during that test — no diagnosis, only raw evidence.
    """

    raise EvidenceError("list_failed_tests is not implemented yet")


@mcp.tool()
def inspect_fixture(path: str):
    """Inspect a JSON or YAML fixture file used by a test.

    Use to check whether the failure comes from the input data itself.
    `path` points to the fixture file, not to the project.
    """

    raise EvidenceError("list_failed_tests is not implemented yet")


@mcp.tool()
def parse_pytest_output(raw_text: str):
    """Extract failure evidence from raw pytest terminal output.

    Last-resort fallback for when pytest cannot be run again and the output
    was pasted by hand. Less reliable than the other tools.
    """

    raise EvidenceError("list_failed_tests is not implemented yet")
