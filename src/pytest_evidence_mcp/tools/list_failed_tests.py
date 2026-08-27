from pytest_evidence_mcp.sources.resolver import resolve_test_run


def list_failed_tests(path: str):
    """Summarise the most recent pytest run for a project.

    Start here: use it to find which tests failed before investigating any
    single one. `path` is the root of the project under investigation.
    """
    test_run, metadata = resolve_test_run(path)
    return {
        "source": metadata["source"],
        "generated_at": metadata["generated_at"],
        "age_seconds": metadata["age_seconds"],
        "total": test_run.total,
        "passed": test_run.passed,
        "failed": test_run.failed,
        "skipped": test_run.skipped,
        "failed_tests": [
            {
                "nodeid": t.nodeid,
                "name": t.name,
                "error_type": t.failure.error_type if t.failure else None,
            }
            for t in test_run.failed_tests()
        ],
    }
