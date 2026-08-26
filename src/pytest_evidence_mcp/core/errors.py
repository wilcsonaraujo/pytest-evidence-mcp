class EvidenceError(Exception):
    """Base for every domain error this server raises."""

    pass


class ConfigParseError(EvidenceError):
    """A pytest config file exists but could not be parsed."""

    pass


class InterpreterNotFoundError(EvidenceError):
    """Python interpreter not found."""

    pass


class PytestNotFoundError(EvidenceError):
    """Pytest not found in the interpreter."""

    pass


class PytestTimeoutError(EvidenceError):
    """The pytest execution exceeded the timeout."""

    pass


class PytestExecutionError(EvidenceError):
    """Error during pytest execution."""

    pass


class ResolverError(EvidenceError):
    """Erro base para falhas no resolver."""

    pass
