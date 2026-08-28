from typing import Literal

from typing_extensions import TypedDict

from pytest_evidence_mcp.core.pytest_output_parser import ParsedFailure, parse_raw_text
from pytest_evidence_mcp.core.truncate import DEFAULT_MAX_OUTPUT_CHARS, truncate_tail


class ParsePytestOutputOutput(TypedDict):
    confidence: Literal["low"]
    failures: list[ParsedFailure]


def parse_pytest_output(raw_text: str, max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS) -> ParsePytestOutputOutput:
    """Extract failure evidence from raw pytest terminal output.

    Last-resort fallback for when pytest can't be run again and no
    structured report is available. Large text fields per failure are
    truncated to `max_output_chars` (keeping the tail) to avoid blowing up
    the caller's context.
    """
    failures = parse_raw_text(raw_text)

    for failure in failures:
        failure["traceback"] = truncate_tail(failure["traceback"], max_output_chars)
        failure["actual"] = truncate_tail(failure["actual"], max_output_chars)
        failure["expected"] = truncate_tail(failure["expected"], max_output_chars)
        failure["captured_stdout"] = truncate_tail(failure["captured_stdout"], max_output_chars)
        failure["captured_stderr"] = truncate_tail(failure["captured_stderr"], max_output_chars)
        failure["captured_log"] = truncate_tail(failure["captured_log"], max_output_chars)

    return {
        "confidence": "low",
        "failures": failures,
    }
