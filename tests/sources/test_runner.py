import logging
import subprocess
from pathlib import Path

import pytest

from pytest_evidence_mcp.core.errors import (
    NoTestsCollectedError,
    PytestExecutionError,
    PytestNotFoundError,
    PytestTimeoutError,
)
from pytest_evidence_mcp.core.models import SourceKind
from pytest_evidence_mcp.sources.runner import (
    _build_clean_env,
    _resolve_interpreter,
    run_pytest,
)

SAMPLE_PROJECT = Path(__file__).parent / "fixtures" / "sample_project"
EMPTY_PROJECT = Path(__file__).parent / "fixtures" / "empty_project"


# --- _resolve_interpreter: pure filesystem logic, no subprocess ------------


def test_explicit_interpreter_wins(tmp_path):
    explicit = tmp_path / "python"
    explicit.write_text("")
    assert _resolve_interpreter(tmp_path, explicit) == explicit


def test_finds_venv_bin_python(tmp_path):
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("")
    assert _resolve_interpreter(tmp_path) == venv_python


def test_falls_back_to_server_interpreter_with_warning(tmp_path, caplog):
    """No .venv anywhere - must still resolve (to sys.executable), but has
    to warn loudly: this means pytest runs with the SERVER's own
    dependencies, not the target project's.
    """
    with caplog.at_level(logging.WARNING):
        result = _resolve_interpreter(tmp_path)

    assert result is not None
    assert any("falling back" in record.message.lower() for record in caplog.records)


# --- _build_clean_env: pure function, no I/O beyond os.environ -------------


def test_clean_env_strips_python_env_vars(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "/something")
    monkeypatch.setenv("VIRTUAL_ENV", "/somewhere/.venv")
    monkeypatch.setenv("HOME", "/home/whoever")

    env = _build_clean_env()

    assert "PYTHONPATH" not in env
    assert "VIRTUAL_ENV" not in env
    assert env.get("HOME") == "/home/whoever"  # untouched, not rebuilt


# --- run_pytest control flow: subprocess.run mocked, no real execution ----


def test_timeout_raises_pytest_timeout_error(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "pytest_evidence_mcp.sources.runner._check_pytest_installed",
        lambda python_path: True,
    )

    with pytest.raises(PytestTimeoutError):
        run_pytest(tmp_path, interpreter=Path("/usr/bin/python3"), timeout=1)


def test_no_xml_generated_raises_execution_error(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="unrecognized arguments"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "pytest_evidence_mcp.sources.runner._check_pytest_installed",
        lambda python_path: True,
    )

    with pytest.raises(PytestExecutionError, match="unrecognized arguments"):
        run_pytest(tmp_path, interpreter=Path("/usr/bin/python3"))


def test_pytest_not_installed_raises_before_running(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "pytest_evidence_mcp.sources.runner._check_pytest_installed",
        lambda python_path: False,
    )
    with pytest.raises(PytestNotFoundError):
        run_pytest(tmp_path, interpreter=Path("/usr/bin/python3"))


# --- real end-to-end: actually spawns pytest against sample_project -------


def test_real_run_against_sample_project():
    test_run = run_pytest(SAMPLE_PROJECT, timeout=30)

    assert test_run.source == SourceKind.JUNITXML_SUBPROCESS
    assert test_run.total == 2
    assert test_run.passed == 1
    assert test_run.failed == 1
    assert test_run.find("test_fails").outcome == "failed"


def test_temp_dir_is_cleaned_up_after_real_run(tmp_path):
    import tempfile

    before = set(Path(tempfile.gettempdir()).glob("pytest_evidence_*"))
    run_pytest(SAMPLE_PROJECT, timeout=30)
    after = set(Path(tempfile.gettempdir()).glob("pytest_evidence_*"))

    assert after == before  # nothing new left behind


def test_real_run_against_empty_project_raises_no_tests_collected():
    with pytest.raises(NoTestsCollectedError):
        run_pytest(EMPTY_PROJECT, timeout=30)
