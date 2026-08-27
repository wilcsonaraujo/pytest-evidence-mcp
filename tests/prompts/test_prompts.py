from pytest_evidence_mcp.prompts._template import build_instruction
from pytest_evidence_mcp.prompts.get_test_failure_prompt import get_test_failure_prompt
from pytest_evidence_mcp.prompts.inspect_fixture_prompt import inspect_fixture_prompt
from pytest_evidence_mcp.prompts.list_failed_tests_prompt import (
    list_failed_tests_prompt,
)
from pytest_evidence_mcp.prompts.parse_pytest_output_prompt import (
    parse_pytest_output_prompt,
)


def test_build_instruction_formats_tool_name_and_arguments():
    text = build_instruction("some_tool", "Do something.", a="1", b="2")

    assert "Do something." in text
    assert "`some_tool`" in text
    assert "a='1'" in text
    assert "b='2'" in text


def test_list_failed_tests_prompt_mentions_tool_and_path():
    text = list_failed_tests_prompt("/path/to/project")

    assert "list_failed_tests" in text
    assert "/path/to/project" in text


def test_get_test_failure_prompt_mentions_tool_and_both_arguments():
    text = get_test_failure_prompt("test_create_customer", "/path/to/project")

    assert "get_test_failure" in text
    assert "test_create_customer" in text
    assert "/path/to/project" in text


def test_inspect_fixture_prompt_mentions_tool_and_path():
    text = inspect_fixture_prompt("/path/to/fixture.json")

    assert "inspect_fixture" in text
    assert "/path/to/fixture.json" in text


def test_parse_pytest_output_prompt_mentions_tool_and_raw_text():
    text = parse_pytest_output_prompt("=== FAILURES ===")

    assert "parse_pytest_output" in text
    assert "=== FAILURES ===" in text
