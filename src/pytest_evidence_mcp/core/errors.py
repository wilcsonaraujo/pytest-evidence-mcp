class EvidenceError(Exception):
    """Base for every domain error this server raises."""


class ConfigParseError(EvidenceError):
    """A pytest config file exists but could not be parsed."""


class InterpreterNotFoundError(EvidenceError):
    """Python interpreter not found."""


class PytestNotFoundError(EvidenceError):
    """Pytest not found in the interpreter."""


class PytestTimeoutError(EvidenceError):
    """The pytest execution exceeded the timeout."""


class PytestExecutionError(EvidenceError):
    """Error during pytest execution."""


class ResolverError(EvidenceError):
    """Erro base para falhas no resolver."""


class NoTestsCollectedError(EvidenceError):
    """No tests were collected by pytest."""


class TestNotFoundError(EvidenceError):
    "Test not found"


class TestDidNotFailError(EvidenceError):
    "Exists tests but is not failed or error"


class UnrecognizedOutputFormatError(EvidenceError):
    """The pytest output format is not recognized by the server."""


class ProjectPathNotFoundError(EvidenceError):
    """The project path is not found."""


class IncompleteEvidenceError(EvidenceError):
    """Report claims a test failed/errored but carries no failure detail for it."""
