import sys

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED_TOOLS = {
    "list_failed_tests",
    "get_test_failure",
    "inspect_fixture",
    "parse_pytest_output",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def session():
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "pytest_evidence_mcp"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.mark.anyio
async def test_handshake_reports_server_identity(session):
    info = session.initialize_result.server_info
    assert info.name == "pytest-evidence-mcp"
    assert info.version == "0.1.0"


@pytest.mark.anyio
async def test_all_tools_are_registered(session):
    tools = await session.list_tools()
    assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS


@pytest.mark.anyio
async def test_every_tool_is_documented(session):
    tools = await session.list_tools()
    for tool in tools.tools:
        assert tool.description, f"{tool.name} has no description"


@pytest.mark.anyio
async def test_tool_failure_does_not_kill_the_server(session):
    result = await session.call_tool("list_failed_tests", {"path": "."})
    assert result.is_error

    tools = await session.list_tools()
    assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS
