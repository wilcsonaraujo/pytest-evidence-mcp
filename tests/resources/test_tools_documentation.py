import pytest
from mcp.server.mcpserver import MCPServer

from pytest_evidence_mcp.resources.tools_documentation import build_tool_documentation


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def server_with_tools():
    server = MCPServer("test-server", version="0.0.0")

    @server.tool()
    def sample_tool(x: str) -> str:
        """A sample tool for testing."""
        return x

    return server


@pytest.mark.anyio
async def test_returns_contract_for_existing_tool(server_with_tools):
    result = await build_tool_documentation(server_with_tools, "sample_tool")

    assert result["name"] == "sample_tool"
    assert result["description"] == "A sample tool for testing."
    assert "x" in result["input_schema"]["properties"]
    assert result["input_schema"]["required"] == ["x"]


@pytest.mark.anyio
async def test_raises_for_unknown_tool(server_with_tools):
    with pytest.raises(ValueError, match="unknown_tool"):
        await build_tool_documentation(server_with_tools, "unknown_tool")
