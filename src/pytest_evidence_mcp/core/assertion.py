import re
from typing import Optional, Tuple

_ASSERT_EQ = re.compile(r"^assert\s+(.+?)\s*==\s*(.+)$", re.MULTILINE)


def extract_actual_expected(
    message: str, error_type: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Extract (expected, actual) from an AssertionError message, when safe."""
    if error_type != "AssertionError" or not message:
        return None, None

    match = _ASSERT_EQ.search(message)
    if not match:
        return None, None

    actual, expected = match.group(1).strip(), match.group(2).strip()

    if not actual or not expected:
        return None, None

    return actual, expected


def extract_actual_expected_safe(
    message: str, error_type: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Same as extract_expected_actual, but never raises."""
    try:
        return extract_actual_expected(message, error_type)
    except Exception:
        return None, None


def derive_error_type_from_traceback(traceback_text: Optional[str]) -> Optional[str]:
    """Derive the exception class name from a pytest traceback block."""
    if not traceback_text:
        return None

    lines = [line for line in traceback_text.strip().splitlines() if line.strip()]
    if not lines:
        return None

    last_line = lines[-1]
    if ":" not in last_line:
        return None

    error_type = last_line.rsplit(":", 1)[-1].strip()
    return error_type or None
