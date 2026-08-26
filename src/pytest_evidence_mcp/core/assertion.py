import re
from typing import Optional, Tuple

_ASSERT_EQ = re.compile(r"^assert\s+(.+?)\s*==\s*(.+)$", re.MULTILINE)


def extract_actual_expected(
    message: str, error_type: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Extract (expected, actual) from an AssertionError message, when safe.

    Only extracts for `==` comparisons on `AssertionError`. Any other shape
    (custom exceptions, `!=`/`in`/`<`, unrecognised text) returns (None, None)
    — failing to recognise the pattern is the normal path, not an error.

    Convention: `assert <actual> == <expected>` (the author's variable comes
    first). This is a convention, not something pytest tells us — swapped
    assertions (`assert 201 == status`) will mislabel the pair.
    """
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
