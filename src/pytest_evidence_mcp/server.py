from mcp.server import MCPServer

from pytest_evidence_mcp.tools.get_test_failure import get_test_failure
from pytest_evidence_mcp.tools.inspect_fixture import inspect_fixture
from pytest_evidence_mcp.tools.list_failed_tests import list_failed_tests
from pytest_evidence_mcp.tools.parse_pytest_output import parse_pytest_output

mcp = MCPServer("pytest-evidence-mcp", version="0.1.0")

mcp.add_tool(list_failed_tests)
mcp.add_tool(get_test_failure)
mcp.add_tool(inspect_fixture)
mcp.add_tool(parse_pytest_output)
