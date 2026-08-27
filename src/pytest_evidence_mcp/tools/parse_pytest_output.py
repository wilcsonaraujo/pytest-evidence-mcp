from typing import Literal

from typing_extensions import TypedDict

from pytest_evidence_mcp.core.pytest_output_parser import ParsedFailure, parse_raw_text


class ParsePytestOutputOutput(TypedDict):
    confidence: Literal["low"]
    failures: list[ParsedFailure]


def parse_pytest_output(raw_text: str) -> ParsePytestOutputOutput:
    """Extract failure evidence from raw pytest terminal output.

    Last-resort fallback for when pytest cannot be run again and the output
    was pasted by hand. Less reliable than the other tools.
    """
    failures = parse_raw_text(raw_text)

    return {"confidence": "low", "failures": failures}
