from pytest_evidence_mcp.prompts._template import build_instruction


def inspect_fixture_prompt(path: str) -> str:
    """Prompt template for checking whether a fixture/payload file is valid."""
    return build_instruction(
        tool_name="inspect_fixture",
        purpose=(
            f"You want to check whether the fixture/payload file at '{path}' is "
            f"valid and inspect its fields - useful when a test failure might be "
            f"caused by the input data itself, not the code."
        ),
        path=path,
    )
