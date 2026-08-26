import pytest

from pytest_evidence_mcp.core.errors import ConfigParseError
from pytest_evidence_mcp.sources.config import get_config_paths


def test_no_config_files_returns_none_none(tmp_path):
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path is None
    assert paths.json_report_path is None


def test_pyproject_with_addopts(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\n'
        'addopts = "--junitxml=reports/junit.xml --json-report-file=reports/report.json"\n'
    )
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path == tmp_path / "reports" / "junit.xml"
    assert paths.json_report_path == tmp_path / "reports" / "report.json"


def test_pyproject_without_pytest_section_falls_through(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "whatever"\n')
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path is None
    assert paths.json_report_path is None


def test_malformed_pyproject_raises_config_parse_error(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options\naddopts = 1")
    with pytest.raises(ConfigParseError):
        get_config_paths(tmp_path)


def test_pytest_ini_with_addopts(tmp_path):
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\naddopts = --junitxml=out/junit.xml\n"
    )
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path == tmp_path / "out" / "junit.xml"


def test_tox_ini_with_addopts(tmp_path):
    (tmp_path / "tox.ini").write_text(
        "[testenv]\ncommands = pytest --junitxml=out/junit.xml\n"
    )
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path == tmp_path / "out" / "junit.xml"


def test_setup_cfg_with_addopts(tmp_path):
    (tmp_path / "setup.cfg").write_text(
        "[tool:pytest]\naddopts = --junitxml=out/junit.xml\n"
    )
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path == tmp_path / "out" / "junit.xml"


def test_absolute_path_in_addopts_is_kept_as_is(tmp_path):
    abs_path = tmp_path / "elsewhere" / "junit.xml"
    (tmp_path / "pyproject.toml").write_text(
        # TOML literal string (single quotes) - a basic string ("...") would
        # treat the path's backslashes as escape sequences on Windows (e.g.
        # "\Users" starts a \UXXXXXXXX unicode escape) and fail to parse.
        f"[tool.pytest.ini_options]\naddopts = '--junitxml={abs_path}'\n"
    )
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path == abs_path


def test_pyproject_takes_priority_over_pytest_ini(tmp_path):
    """Search order: pyproject.toml before pytest.ini - only the first
    match found should be used."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "--junitxml=from_pyproject.xml"\n'
    )
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\naddopts = --junitxml=from_pytest_ini.xml\n"
    )
    paths = get_config_paths(tmp_path)
    assert paths.junitxml_path == tmp_path / "from_pyproject.xml"
