from pytest_evidence_mcp.prompts._template import build_instruction


def parse_pytest_output_prompt(raw_text: str) -> str:
    """Prompt template for extracting evidence from pasted pytest terminal output."""
    return build_instruction(
        tool_name="parse_pytest_output",
        purpose=(
            "You have raw pytest terminal output pasted by hand (pytest cannot "
            "be run again) and want to extract structured failure evidence from "
            "it. This is a last-resort fallback, less reliable than the other "
            "tools."
        ),
        raw_text=raw_text,
    )
