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
