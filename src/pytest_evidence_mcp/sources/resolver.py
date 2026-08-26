import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from pytest_evidence_mcp.sources.config import (
    get_config_paths,
    get_default_junit_path,
    get_default_json_report_path,
)
from pytest_evidence_mcp.sources.json_report import (
    parse_json_report,
    SourceKind as JSONSourceKind,
)
from pytest_evidence_mcp.sources.junitxml import (
    parse_junit_xml,
    SourceKind as JUnitSourceKind,
)
from pytest_evidence_mcp.sources.runner import run_pytest
from pytest_evidence_mcp.core.errors import ResolverError

from pytest_evidence_mcp.core.models import TestRun

logger = logging.getLogger(__name__)


def _calculate_age(generated_at: Optional[datetime]) -> Optional[float]:
    """Calcula a idade do relatório em segundos."""
    if generated_at is None:
        return None
    now = datetime.now()
    return (now - generated_at).total_seconds()


def _resolve_json_report(project_path: Path) -> Tuple[TestRun, Dict[str, Any]]:
    """Branch 1: Attempts to load .report.json."""
    config_paths = get_config_paths(project_path)
    json_report_path = config_paths.json_report_path

    if json_report_path:
        if not json_report_path.is_absolute():
            json_report_path = project_path / json_report_path
        logger.debug(f"Declareds JSON report path: {json_report_path}")

        if json_report_path.exists():
            try:
                test_run = parse_json_report(
                    json_report_path, source=JSONSourceKind.JSON_REPORT
                )
                generated_at = test_run.generated_at
                age = _calculate_age(generated_at)

                logger.info(f"Resolved JSON report: {json_report_path} (age: {age}s)")

                metadata = {
                    "source": "json_resport",
                    "generated_at": generated_at,
                    "age_seconds": age,
                    "resolved_path": json_report_path,
                }
                return test_run, metadata
            except Exception as e:
                logger.warning(f"Failed to parse declared JSON report: {e}")

    default_json_path = project_path / get_default_json_report_path()
    logger.debug(f"Checking default JSON report: {default_json_path}")

    if default_json_path.exists():
        try:
            test_run = parse_json_report(
                default_json_path, source=JSONSourceKind.JSON_REPORT
            )
            generated_at = test_run.generated_at
            age = _calculate_age(generated_at)

            logger.info(f"Resolved JSON report: {default_json_path} (age: {age}s)")

            metadata = {
                "source": "json_resport",
                "generated_at": generated_at,
                "age_seconds": age,
                "resolved_path": default_json_path,
            }
            return test_run, metadata
        except Exception as e:
            logger.warning(f"Failed to parse default JSON report: {e}")

    raise ResolverError("JSON report not found or invalid")


def _resolve_junit_xml(project_path: Path) -> Tuple[TestRun, Dict[str, Any]]:
    """Branch 2: Attempts to load junit.xml."""
    config_paths = get_config_paths(project_path)
    junit_path = config_paths.junitxml_path

    if junit_path:
        if not junit_path.is_absolute():
            junit_path = project_path / junit_path
        logger.debug(f"Declared JUnit path: {junit_path}")

        if junit_path.exists():
            try:
                test_run = parse_junit_xml(junit_path, source=JUnitSourceKind.JUNITXML)
                generated_at = test_run.generated_at
                age = _calculate_age(generated_at)

                logger.info(f"Resolved JUnit XML: {junit_path} (age: {age}s)")
                metadata = {
                    "source": "junitxml",
                    "generated_at": generated_at,
                    "age_seconds": age,
                    "resolved_path": junit_path,
                }
                return test_run, metadata
            except Exception as e:
                logger.warning(f"Failed to parse declared JUnit XML: {e}")

    default_junit_path = project_path / get_default_junit_path()
    logger.debug(f"Checking default JUnit path: {default_junit_path}")

    if default_junit_path.exists():
        try:
            test_run = parse_junit_xml(
                default_junit_path, source=JUnitSourceKind.JUNITXML
            )
            generated_at = test_run.generated_at
            age = _calculate_age(generated_at)

            logger.info(
                f"Resolved default JUnit XML: {default_junit_path} (age: {age}s)"
            )
            metadata = {
                "source": "junitxml",
                "generated_at": generated_at,
                "age_seconds": age,
                "resolved_path": default_junit_path,
            }
            return test_run, metadata
        except Exception as e:
            logger.warning(f"Failed to parse default JUnit XML: {e}")

    raise ResolverError("JUnit XML not found or invalid")


def _resolve_subprocess(
    project_path: Path, explicit_interpreter: Optional[str], timeout: int
) -> Tuple[TestRun, Dict[str, Any]]:
    """Branch 3: Runs pytest via subprocess."""
    interpreter_path = Path(explicit_interpreter) if explicit_interpreter else None

    try:
        test_run = run_pytest(
            project_path=project_path, interpreter=interpreter_path, timeout=timeout
        )
        generated_at = test_run.generated_at
        age = _calculate_age(generated_at)
        logger.info(f"Resolved via subprocess (age: {age}s)")
        metadata = {
            "source": "junitxml_subprocess",
            "generated_at": generated_at,
            "age_seconds": age,
            "resolved_path": None,
        }
        return test_run, metadata
    except ResolverError as e:
        logger.debug(f"Subprocess failed: {e}")
        raise ResolverError("All resolution attempts failed") from e


def resolve_test_run(
    project_path: str,
    explicit_interpreter: Optional[str] = None,
    timeout: int = 60,
    force: Optional[str] = None,
) -> Tuple[TestRun, Dict[str, Any]]:
    """
    Resolves a TestRun following the priority chain.
    Order (Branch 1 → 2 → 3):
        1. .report.json (declared or by convention)
        2. junit.xml (declared or by convention)
        3. Run pytest via subprocess (run_pytest)
    Args:
        project_path: Path to the project
        explicit_interpreter: Explicit path to the interpreter (branch 3)
        timeout: Timeout for the subprocess (seconds)
        force: Force a specific source ("json", "junit", "subprocess")

    Returns:
        Tuple (TestRun, metadata) where metadata contains:
            - source: "json_report" | "junitxml" | "junitxml_subprocess"
    """
    project_path = Path(project_path)
    logger.info(f"Resolving test run for: {project_path}")

    if force:
        logger.debug(f"Force mode: {force}")
        if force == "json":
            return _resolve_json_report(project_path)
        elif force == "junit":
            return _resolve_junit_xml(project_path)
        elif force == "subprocess":
            return _resolve_subprocess(project_path, explicit_interpreter, timeout)
        else:
            raise ResolverError(f"Invalid force value: {force}")

    # 1. Try JSON report
    try:
        logger.debug("Attempting JSON report (Ramo 1)")
        return _resolve_json_report(project_path)
    except ResolverError as e:
        logger.debug(f"JSON report failed: {e}")

    # 2. Try JUnit XML
    try:
        logger.debug("Attempting JUnit XML (Ramo 2)")
        return _resolve_junit_xml(project_path)
    except ResolverError as e:
        logger.debug(f"JUnit XML failed: {e}")

    # 3. Execute pytest
    try:
        logger.debug("Attempting subprocess (Ramo 3)")
        return _resolve_subprocess(project_path, explicit_interpreter, timeout)
    except ResolverError as e:
        logger.debug(f"Subprocess failed: {e}")
        raise ResolverError("All resolution attempts failed") from e
