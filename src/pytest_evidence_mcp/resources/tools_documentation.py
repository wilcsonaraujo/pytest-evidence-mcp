from mcp.server.mcpserver import MCPServer


async def build_tools_documentation(server: MCPServer) -> list[dict]:
    """Builds a machine-readable contract for every tool registered on
    `server`: name, description, required inputs and expected output -
    derivado do próprio registro de tools do SDK, nunca escrito à mão.
    """
    tools = await server.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "output_schema": t.output_schema,
        }
        for t in tools
    ]
