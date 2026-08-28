import sys

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server.mcpserver.exceptions import ToolError

from pytest_evidence_mcp.core.errors import EvidenceError
from pytest_evidence_mcp.tools._error_handling import translate_evidence_errors


def test_evidence_error_is_translated_to_tool_error():
    @translate_evidence_errors
    def boom():
        raise EvidenceError("something went wrong")

    with pytest.raises(ToolError, match="something went wrong"):
        boom()


def test_unrelated_exception_is_not_translated():
    """A real bug shouldn't be disguised as a clean domain error - it must
    keep crashing loudly, not get silently wrapped into a ToolError."""

    @translate_evidence_errors
    def boom():
        raise ValueError("a real bug, not a domain error")

    with pytest.raises(ValueError, match="a real bug"):
        boom()


def test_wrapped_function_keeps_its_signature_and_docstring():
    """functools.wraps must preserve enough for the MCP SDK to still derive
    input_schema/output_schema correctly through the wrapper (US-13 depends
    on this)."""

    @translate_evidence_errors
    def sample(test_name: str, path: str) -> str:
        """Sample docstring."""
        return test_name

    assert sample.__name__ == "sample"
    assert sample.__doc__ == "Sample docstring."
    assert sample("a", "b") == "a"


# --- end-to-end: real MCP client, o mesmo cenário que vimos quebrado ao vivo


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_real_call_with_nonexistent_path_preserves_message(tmp_path):
    missing = str(tmp_path / "does_not_exist")

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "pytest_evidence_mcp"]
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("list_failed_tests", {"path": missing})

        assert result.is_error
        text = result.content[0].text
        assert "does not exist" in text
        assert missing in text
