from pytest_evidence_mcp.core.truncate import truncate_tail


def test_text_within_limit_is_returned_unchanged():
    assert truncate_tail("short text", 100) == "short text"


def test_exact_length_is_not_truncated():
    text = "a" * 20
    assert truncate_tail(text, 20) == text


def test_text_over_limit_keeps_the_tail():
    long_text = "x" * 50 + "IMPORTANT_TAIL"
    result = truncate_tail(long_text, 20)

    assert result is not None
    assert result.endswith("IMPORTANT_TAIL")
    assert "chars omitted" in result


def test_omitted_count_matches_actual_cut():
    text = "a" * 100
    result = truncate_tail(text, 20)

    assert result is not None
    assert "[80 chars omitted]" in result


def test_none_passes_through_unchanged():
    assert truncate_tail(None, 20) is None


def test_zero_or_negative_limit_disables_truncation():
    """max_chars <= 0 is treated as "no limit", not "cut everything" - a
    caller passing a nonsensical value shouldn't silently get an empty
    field."""
    text = "a" * 100
    assert truncate_tail(text, 0) == text
    assert truncate_tail(text, -5) == text
