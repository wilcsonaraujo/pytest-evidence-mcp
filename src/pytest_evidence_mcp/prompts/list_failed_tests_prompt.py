from pytest_evidence_mcp.prompts._template import build_instruction


def list_failed_tests_prompt(path: str) -> str:
    """Prompt template for summarising the most recent pytest run of a project."""
    return build_instruction(
        tool_name="list_failed_tests",
        purpose=(
            f"You want a summary of the most recent pytest run for the project "
            f"at '{path}' - which tests failed, passed or were skipped. Start "
            f"here before investigating any single test."
        ),
        path=path,
    )
