import shutil
from pathlib import Path

import pytest

from pytest_evidence_mcp.core.errors import ResolverError
from pytest_evidence_mcp.core.models import SourceKind, TestRun
from pytest_evidence_mcp.sources import resolver

FIXTURE_JSON = Path(__file__).parent.parent / "fixtures" / "json_report" / "sample.json"
FIXTURE_JUNIT = Path(__file__).parent.parent / "fixtures" / "junit" / "sample.xml"


def _fake_test_run(source: SourceKind) -> TestRun:
    return TestRun(source=source, total=1, passed=1, failed=0, skipped=0, tests=[])


# --- branches 1 and 2: real files, by convention (no config at all) -------


def test_resolves_json_report_by_convention(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")

    test_run, metadata = resolver.resolve_test_run(str(tmp_path))

    assert metadata["source"] == "json_report"
    assert test_run.source == SourceKind.JSON_REPORT


def test_falls_back_to_junit_xml_when_no_json_report(tmp_path):
    shutil.copy(FIXTURE_JUNIT, tmp_path / "junit.xml")

    test_run, metadata = resolver.resolve_test_run(str(tmp_path))

    assert metadata["source"] == "junitxml"
    assert test_run.source == SourceKind.JUNITXML


def test_json_report_takes_priority_over_junit_xml(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")
    shutil.copy(FIXTURE_JUNIT, tmp_path / "junit.xml")

    _, metadata = resolver.resolve_test_run(str(tmp_path))

    assert metadata["source"] == "json_report"


def test_respects_declared_path_over_convention(tmp_path):
    (tmp_path / "reports").mkdir()
    shutil.copy(FIXTURE_JSON, tmp_path / "reports" / "custom.json")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "--json-report-file=reports/custom.json"\n'
    )

    _test_run, metadata = resolver.resolve_test_run(str(tmp_path))

    assert metadata["source"] == "json_report"
    assert metadata["resolved_path"] == tmp_path / "reports" / "custom.json"


def test_malformed_config_does_not_abort_the_chain(tmp_path, monkeypatch):
    """A broken pyproject.toml shouldn't prevent falling back to a real
    junit.xml sitting right there - branch 2 doesn't depend on config
    parsing succeeding.
    """
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options\nbroken")
    shutil.copy(FIXTURE_JUNIT, tmp_path / "junit.xml")

    _, metadata = resolver.resolve_test_run(str(tmp_path))

    assert metadata["source"] == "junitxml"


# --- branch 3: mocked - run_pytest's own correctness is covered elsewhere -


def test_falls_back_to_subprocess_when_nothing_else_available(tmp_path, monkeypatch):
    monkeypatch.setattr(
        resolver, "run_pytest", lambda **kwargs: _fake_test_run(
            SourceKind.JUNITXML_SUBPROCESS
        )
    )

    test_run, metadata = resolver.resolve_test_run(str(tmp_path))

    assert metadata["source"] == "junitxml_subprocess"
    assert test_run.source == SourceKind.JUNITXML_SUBPROCESS


def test_subprocess_failure_propagates_unwrapped(tmp_path, monkeypatch):
    """The real reason (e.g. PytestNotFoundError) must reach the caller as
    the specific EvidenceError subclass, not a generic ResolverError."""
    from pytest_evidence_mcp.core.errors import PytestNotFoundError

    def boom(**kwargs):
        raise PytestNotFoundError("pytest not installed in interpreter: x")

    monkeypatch.setattr(resolver, "run_pytest", boom)

    with pytest.raises(PytestNotFoundError):
        resolver.resolve_test_run(str(tmp_path))

def test_no_tests_collected_propagates_unwrapped(tmp_path, monkeypatch):
    """Testing an empty project cannot result in '0 failures'—
    it must appear as an error that the agent recognizes as
    distinct from a genuine execution of an empty project.
    """
    from pytest_evidence_mcp.core.errors import NoTestsCollectedError

    def boom(**kwargs):
        raise NoTestsCollectedError("No tests were collected by pytest in path x")

    monkeypatch.setattr(resolver, "run_pytest", boom)

    with pytest.raises(NoTestsCollectedError):
        resolver.resolve_test_run(str(tmp_path))


# --- force= -----------------------------------------------------------


def test_force_json_bypasses_the_chain(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")
    shutil.copy(FIXTURE_JUNIT, tmp_path / "junit.xml")

    _, metadata = resolver.resolve_test_run(str(tmp_path), force="json")

    assert metadata["source"] == "json_report"


def test_force_junit_when_json_not_even_present(tmp_path):
    shutil.copy(FIXTURE_JUNIT, tmp_path / "junit.xml")

    _, metadata = resolver.resolve_test_run(str(tmp_path), force="junit")

    assert metadata["source"] == "junitxml"


def test_force_subprocess(tmp_path, monkeypatch):
    monkeypatch.setattr(
        resolver, "run_pytest", lambda **kwargs: _fake_test_run(
            SourceKind.JUNITXML_SUBPROCESS
        )
    )
    _, metadata = resolver.resolve_test_run(str(tmp_path), force="subprocess")
    assert metadata["source"] == "junitxml_subprocess"


def test_force_json_raises_when_not_found(tmp_path):
    with pytest.raises(ResolverError):
        resolver.resolve_test_run(str(tmp_path), force="json")


def test_invalid_force_value_raises(tmp_path):
    with pytest.raises(ResolverError):
        resolver.resolve_test_run(str(tmp_path), force="not-a-real-source")


# --- metadata consistency --------------------------------------------


def test_metadata_source_matches_test_run_source(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")
    test_run, metadata = resolver.resolve_test_run(str(tmp_path))
    assert metadata["source"] == test_run.source.value


def test_metadata_includes_age_when_generated_at_known(tmp_path):
    shutil.copy(FIXTURE_JSON, tmp_path / ".report.json")
    _, metadata = resolver.resolve_test_run(str(tmp_path))
    assert metadata["generated_at"] is not None
    assert isinstance(metadata["age_seconds"], float)
