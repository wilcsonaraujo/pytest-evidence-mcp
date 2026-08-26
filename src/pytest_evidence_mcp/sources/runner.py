import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pytest_evidence_mcp.core.errors import (
    InterpreterNotFoundError,
    NoTestsCollectedError,
    PytestExecutionError,
    PytestNotFoundError,
    PytestTimeoutError,
)
from pytest_evidence_mcp.core.models import SourceKind, TestRun
from pytest_evidence_mcp.sources.junitxml import parse_junit_xml

logger = logging.getLogger(__name__)


def _resolve_interpreter(
    project_path: Path, explicit: Path | None = None
) -> Path | None:
    """The Python interpreter resolves it in the defined order."""

    if explicit and explicit.exists() and explicit.is_file():
        logger.debug(f"Using explicit interpreter: {explicit}")
        return explicit

    venv_bin = project_path / ".venv" / "bin" / "python"
    if venv_bin.exists() and venv_bin.is_file():
        logger.debug(f"Found .venv/bin/python: {venv_bin}")
        return venv_bin

    venv_scripts = project_path / ".venv" / "Scripts" / "python.exe"
    if venv_scripts.exists() and venv_scripts.is_file():
        logger.debug(f"Found .venv/Scripts/python: {venv_scripts}")
        return venv_scripts

    fallback = Path(sys.executable)
    if fallback.exists() and fallback.is_file():
        logger.warning(
            f"No .venv found for {project_path}; falling back to the MCP "
            f"server's own interpreter ({fallback}). Results may be wrong "
            f"if the target project has its own dependencies."
        )
        return fallback

    return None


def _check_pytest_installed(python_path: Path) -> bool:
    """Checks if pytest is installed in the interpreter."""
    try:
        result = subprocess.run(
            [str(python_path), "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug(f"Failed to check pytest installation: {e}")
        return False


def _build_clean_env() -> dict[str, str]:
    """
    Environment for the pytest subprocess: a copy of this process's own
    environment, with only PYTHONPATH/VIRTUAL_ENV/PYTHONHOME stripped.
    """
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHONHOME", None)
    env["PATH"] = _get_clean_path()
    return env


def _get_clean_path() -> str:
    """Returns a clean PATH, removing any references to the server's venv."""
    path = os.environ.get("PATH", "")
    parts = path.split(os.pathsep)
    clean_parts = [
        p for p in parts if ".venv" not in p.lower() and "virtualenv" not in p.lower()
    ]

    return os.pathsep.join(clean_parts)


def run_pytest(
    project_path: Path,
    interpreter: Path | None = None,
    timeout: int = 60,
    extra_args: list[str] | None = None,
) -> TestRun:
    """
    Runs pytest on the target project.

    Interpreter resolution order:
        1. Explicit parameter (interpreter)
        2. <path>/.venv/{bin,Scripts}/python
        3. sys.executable (last resort)
    Note:
        - Does not inherit PYTHONPATH or VIRTUAL_ENV from the server
        - CWD is the project_path
        - Temporary directory is always removed, even on timeout/error
        - Source is JUNITXML_SUBPROCESS
    """
    # 1. Resolves the interpreter
    logger.info(f"Running pytest in: {project_path}")

    python_path = _resolve_interpreter(project_path, interpreter)
    if not python_path:
        raise InterpreterNotFoundError(
            f"Python interpreter not found in {project_path}"
        )
    logger.debug(f"Using interpreter: {python_path}")

    # 2. Check if pytest is installed
    if not _check_pytest_installed(python_path):
        raise PytestNotFoundError(f"pytest not installed in interpreter: {python_path}")

    # 3. Creates a temporary file for the JUnit XML
    with tempfile.TemporaryDirectory(prefix="pytest_evidence_") as temp_dir:
        temp_file = Path(temp_dir) / "report.xml"

        cmd = [str(python_path), "-m", "pytest"]
        if extra_args:
            cmd.extend(extra_args)

        cmd.extend([f"--junitxml={temp_file}", "-p", "no:sugar"])

        logger.debug(f"Running: {' '.join(cmd)}")
        env = _build_clean_env()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"Pytest timeout after {timeout}s")
            raise PytestTimeoutError(
                f"Pytest execution exceeded {timeout} seconds timeout"
            ) from e

        if result.returncode == 5:
            raise NoTestsCollectedError(
                f"No tests were collected by pytest in path {project_path}"
            )

        if not temp_file.exists():
            error_msg = result.stderr or result.stdout or "Unknown error"
            logger.error(f"Pytest failed: {error_msg}")
            raise PytestExecutionError(f"Pytest execution failed: {error_msg}")

        logger.info(f"Parsing JUnit XML from subprocess: {temp_file}")
        test_run = parse_junit_xml(temp_file, source=SourceKind.JUNITXML_SUBPROCESS)

        logger.info(
            f"Pytest completed: {test_run.total} tests, "
            f"{test_run.passed} passed, {test_run.failed} failed"
        )
        return test_run
