import configparser
import re

try:
    import tomllib
except ImportError:  # Python 3.10 doesn't ship tomllib
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from pathlib import Path
from typing import NamedTuple

from pytest_evidence_mcp.core.errors import ConfigParseError


class PytestPaths(NamedTuple):
    """Extracted paths from pytest configuration."""

    junitxml_path: Path | None
    json_report_path: Path | None


DEFAULT_JUNIT_PATH = Path("junit.xml")
DEFAULT_JSON_REPORT_PATH = Path(".report.json")


def parse_pytest_config(project_path: Path | None = None) -> PytestPaths:
    """
    Parses pytest configurations from project files.
    Search order:
        1. pyproject.toml ([tool.pytest.ini_options] → addopts)
        2. pytest.ini ([pytest] → addopts)
        3. tox.ini ([testenv] → commands → addopts)
        4. setup.cfg ([tool:pytest] → addopts)
    Args:
        project_path: Project path (default: current directory)

    Returns:
        PytestPaths with the extracted paths (or None if not found)

    Never raises an exception. If no config file exists,
    returns PytestPaths(None, None).
    """
    project_path = project_path or Path.cwd()

    config_files: list[tuple[str, Path]] = [
        ("pyproject.toml", project_path / "pyproject.toml"),
        ("pytest.ini", project_path / "pytest.ini"),
        ("tox.ini", project_path / "tox.ini"),
        ("setup.cfg", project_path / "setup.cfg"),
    ]

    for filename, file_path in config_files:
        if file_path.exists():
            # dispatch on the filename string, not file_path (a Path never
            # equal to the literals below)
            addopts = _parse_addopts_from_file(file_path, filename)
            if addopts:
                return _extract_paths_from_addopts(addopts, project_path)
    return PytestPaths(None, None)


def _parse_addopts_from_file(file_path: Path, parser_type: str) -> str | None:
    """Extracts addopts from a configuration file."""
    if parser_type == "pyproject.toml":
        return _parse_pyproject_addopts(file_path)
    elif parser_type == "tox.ini":
        return _parse_tox_addopts(file_path)
    else:
        return _parse_ini_addopts(file_path)


def _parse_pyproject_addopts(file_path: Path) -> str | None:
    """Extracts addopts from pyproject.toml."""
    try:
        with open(file_path, "rb") as file:
            data = tomllib.load(file)

    except tomllib.TOMLDecodeError as e:
        raise ConfigParseError(f"Malformed {file_path}: {e}") from e
    except OSError as e:
        raise ConfigParseError(f"Could not read {file_path}: {e}") from e

    if "tool" in data and "pytest" in data["tool"]:
        pytest_config = data["tool"]["pytest"]

        if isinstance(pytest_config, dict):
            if "ini_options" in pytest_config and isinstance(
                pytest_config["ini_options"], dict
            ):
                return pytest_config["ini_options"].get("addopts")
            elif "addopts" in pytest_config:
                return pytest_config["addopts"]
    return None


def _parse_tox_addopts(file_path: Path) -> str | None:
    """Extracts options from tox.ini (pytest command)."""
    try:
        config = configparser.ConfigParser()
        config.read(file_path)

    except configparser.Error as e:
        raise ConfigParseError(f"Malformed {file_path}: {e}") from e

    if not config.has_section("testenv") or not config.has_option(
        "testenv", "commands"
    ):
        return None

    commands = config.get("testenv", "commands")

    # Command-line search with pytest
    # Example: "pytest --junitxml=reports/junit.xml --json-report-file=reports/report.json"
    for line in commands.splitlines():
        line = line.strip()
        if line.startswith("pytest"):
            args = line[6:].strip()  # len("pytest") = 6 characters
            args = re.sub(
                r"\{[^}]+\}", "", args
            )  # Remove {posargs} or others variables
            return args.strip() if args else None

    return None


def _parse_ini_addopts(file_path: Path) -> str | None:
    """Extracts addopts from pytest.ini or setup.cfg."""
    config = configparser.ConfigParser()
    try:
        config.read(file_path)

    except configparser.Error as e:
        raise ConfigParseError(f"Malformed {file_path}: {e}") from e

    if config.has_section("pytest") and config.has_option("pytest", "addopts"):
        return config.get("pytest", "addopts")

    if config.has_section("tool:pytest") and config.has_option(
        "tool:pytest", "addopts"
    ):
        return config.get("tool:pytest", "addopts")

    return None


def _extract_paths_from_addopts(addopts: str, project_path: Path) -> PytestPaths:
    """Extracts paths from --junitxml= and --json-report-file= from the addopts string."""

    def _resolve(raw: str) -> Path:
        path = Path(raw)
        return path if path.is_absolute() else project_path / path

    junitxml_path = None
    json_report_path = None

    # Extract --junitxml=
    match = re.search(r"--junitxml[=\s]+([^\s]+)", addopts)
    if match:
        junitxml_path = _resolve(match.group(1))

    # Extract --pytest-json-report
    match = re.search(r"--json-report-file[=\s]+([^\s]+)", addopts)
    if match:
        json_report_path = _resolve(match.group(1))

    return PytestPaths(junitxml_path, json_report_path)


def get_config_paths(project_path: Path | None = None) -> PytestPaths:
    """Retrieves the configured paths for reports."""
    return parse_pytest_config(project_path)


def get_default_junit_path() -> Path:
    """Return the JUnit XML default path"""
    return DEFAULT_JUNIT_PATH


def get_default_json_report_path() -> Path:
    """Return the JSON report default path"""
    return DEFAULT_JSON_REPORT_PATH
