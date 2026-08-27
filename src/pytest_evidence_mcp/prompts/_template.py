def build_instruction(tool_name: str, purpose: str, **arguments: str) -> str:
    """Builds a plain instruction template pointing the agent at one tool.

    `purpose` explains why to call the tool; `arguments` are the values
    already provided by whoever invoked the prompt, shown pre-filled so
    the agent can copy the call directly.
    """
    args_text = ", ".join(f"{name}='{value}'" for name, value in arguments.items())
    return f"{purpose}\n\nCall the `{tool_name}` tool with: {args_text}"