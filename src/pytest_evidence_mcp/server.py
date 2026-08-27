from functools import partial

from mcp.server import MCPServer
from mcp.server.mcpserver.resources import FunctionResource

from pytest_evidence_mcp.resources.tools_documentation import build_tool_documentation
from pytest_evidence_mcp.tools.get_test_failure import get_test_failure
from pytest_evidence_mcp.tools.inspect_fixture import inspect_fixture
from pytest_evidence_mcp.tools.list_failed_tests import list_failed_tests
from pytest_evidence_mcp.tools.parse_pytest_output import parse_pytest_output

mcp = MCPServer("pytest-evidence-mcp", version="0.1.0")

mcp.add_tool(list_failed_tests)
mcp.add_tool(get_test_failure)
mcp.add_tool(inspect_fixture)
mcp.add_tool(parse_pytest_output)

TOOL_NAMES = [
    "list_failed_tests",
    "get_test_failure",
    "inspect_fixture",
    "parse_pytest_output",
]

for tool_name in TOOL_NAMES:
    mcp.add_resource(
        FunctionResource.from_function(
            partial(build_tool_documentation, mcp, tool_name),
            uri=f"docs://tools/{tool_name}",
            name=f"{tool_name}_documentation",
            description=f"Machine-readable contract for the {tool_name} tool.",
        )
    )
