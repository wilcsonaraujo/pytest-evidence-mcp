DEFAULT_MAX_OUTPUT_CHARS = 10_000


def truncate_tail(text: str | None, max_chars: int) -> str | None:
    """Keeps the tail of text - where the actual error/exception usually
    shows up (last line of a traceback, most recent captured output before
    a crash, the tail of a large object repr in an assertion message) -
    and prefixes a note of how much was cut, so the agent knows this isn't
    the full picture.
    """
    if text is None or max_chars <= 0 or len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return f"...[{omitted} chars omitted]...\n{text[-max_chars:]}"
