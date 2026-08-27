import re
from typing import Literal

from typing_extensions import TypedDict

from pytest_evidence_mcp.core.assertion import (
    derive_error_type_from_traceback,
    extract_actual_expected_safe,
)
from pytest_evidence_mcp.core.errors import UnrecognizedOutputFormatError

_ANY_BAR_HEADER = re.compile(r"^=+\s*.+?\s*=+$", re.MULTILINE)
_SECTION_HEADER = re.compile(r"^=+\s*(FAILURES|ERRORS)\s*=+$", re.MULTILINE)
_TEST_SEPARATOR = re.compile(r"^_+\s*(.+?)\s*_+$", re.MULTILINE)
_CAPTURED_HEADER = re.compile(
    r"^-+\s*Captured (stdout|stderr|log) call\s*-+$", re.MULTILINE
)
_ERROR_AT_PREFIX = re.compile(r"^ERROR at (setup|teardown) of\s+")
_MESSAGE_LINE = re.compile(r"^E\s+(.*)$", re.MULTILINE)


class ParsedFailure(TypedDict):
    test_name: str
    outcome: Literal["failed", "error"]
    error_type: str | None
    message: str | None
    traceback: str | None
    actual: str | None
    expected: str | None
    captured_stdout: str | None
    captured_stderr: str | None
    captured_log: str | None
    duration_ms: int | None


def parse_raw_text(raw_text: str) -> list[ParsedFailure]:
    """Parses raw pytest terminal output into a list of failure/error dicts.

    Covers both the "=== FAILURES ===" and "==== ERRORS ====" sections -
    the latter is where fixture setup/teardown failures show up, under a
    different per-test header ("ERROR at setup of <test>").
    """
    results: list[ParsedFailure] = []

    for section_match in _SECTION_HEADER.finditer(raw_text):
        section_name = section_match.group(1)
        section_body = _slice_section_body(raw_text, section_match.end())
        outcome: Literal["failed", "error"] = ("failed" if section_name == "FAILURES" else "error")
        results.extend(_parse_section(section_body, outcome))

    if not results:
        raise UnrecognizedOutputFormatError(
            "Could not find any recognizable '=== FAILURES ===' or "
            "'==== ERRORS ====' block in the given text"
        )

    return results


def _slice_section_body(raw_text: str, start: int) -> str:
    """Returns the text between one section header and the next bar-style
    header (another section, "short test summary info", or the final
    summary line) - or the end of the text, whichever comes first."""
    next_header = _ANY_BAR_HEADER.search(raw_text, pos=start)
    end = next_header.start() if next_header else len(raw_text)
    return raw_text[start:end]


def _parse_section(section_body: str, outcome: Literal["failed", "error"]) -> list[ParsedFailure]:
    matches = list(_TEST_SEPARATOR.finditer(section_body))
    tests = []

    for index, match in enumerate(matches):
        title = match.group(1)
        chunk_start = match.end()
        chunk_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(section_body)
        )
        chunk = section_body[chunk_start:chunk_end]

        test_name = _ERROR_AT_PREFIX.sub("", title) if outcome == "error" else title
        tests.append(_parse_test_chunk(test_name, outcome, chunk))

    return tests


def _parse_test_chunk(test_name: str, outcome: Literal["failed", "error"], chunk: str) -> ParsedFailure:
    traceback_text, captured = _split_captured_sections(chunk)

    error_type = derive_error_type_from_traceback(traceback_text)
    message = _extract_message(traceback_text)
    actual, expected = extract_actual_expected_safe(message, error_type)

    return {
        "test_name": test_name,
        "outcome": outcome,
        "error_type": error_type,
        "message": message,
        "traceback": traceback_text.strip(),
        "actual": actual,
        "expected": expected,
        "captured_stdout": captured.get("stdout"),
        "captured_stderr": captured.get("stderr"),
        "captured_log": captured.get("log"),
        "duration_ms": None,
    }


def _split_captured_sections(chunk: str) -> tuple[str, dict[str, str]]:
    """Splits a per-test chunk into (traceback_text, {stdout/stderr/log})."""
    headers = list(_CAPTURED_HEADER.finditer(chunk))
    captured: dict[str, str] = {}

    if not headers:
        return chunk, captured

    traceback_text = chunk[: headers[0].start()]

    for index, header in enumerate(headers):
        kind = header.group(1)
        start = header.end()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(chunk)
        captured[kind] = chunk[start:end].strip()

    return traceback_text, captured


def _extract_message(traceback_text: str) -> str | None:
    """Returns the text of the last "E   ..." line, without the "E" prefix."""
    matches = _MESSAGE_LINE.findall(traceback_text)
    return matches[-1].strip() if matches else None
