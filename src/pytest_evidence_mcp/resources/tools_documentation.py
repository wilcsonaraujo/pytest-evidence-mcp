from typing import Any

from mcp.server.mcpserver import MCPServer


async def build_tool_documentation(server: MCPServer, tool_name: str) -> dict[str, Any]:
    """Builds a machine-readable contract for every tool registered on
    `server`: name, description, required inputs and expected output -
    derived from the SDK's own tool registry, never written by hand.
    """
    tools = await server.list_tools()
    for t in tools:
        if t.name == tool_name:
            return {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
            }
    raise ValueError(f"No tool named {tool_name!r} is registered")
