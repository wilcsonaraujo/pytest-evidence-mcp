import functools
import logging

from mcp.server.mcpserver.exceptions import ToolError

from pytest_evidence_mcp.core.errors import EvidenceError

logger = logging.getLogger(__name__)


def translate_evidence_errors(fn):
    """Wraps a tool function so any EvidenceError raised by the domain
    layers reaches the agent as a clean message, instead of being treated
    as a crash and silently discarded by the MCP SDK.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except EvidenceError as e:
            logger.warning(f"{fn.__name__} raised {type(e).__name__}: {e}")
            raise ToolError(str(e)) from e

    return wrapper
