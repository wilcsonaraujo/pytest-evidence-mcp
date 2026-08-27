from pytest_evidence_mcp.prompts._template import build_instruction


def get_test_failure_prompt(test_name: str, path: str) -> str:
    """Prompt template for investigating one specific failing test."""
    return build_instruction(
        tool_name="get_test_failure",
        purpose=(
            f"You want the full evidence pytest already collected for the "
            f"failing test '{test_name}' in the project at '{path}' - the "
            f"error, traceback and captured output, no diagnosis."
        ),
        test_name=test_name,
        path=path,
    )