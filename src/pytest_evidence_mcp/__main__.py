import logging
import sys

from pytest_evidence_mcp.server import mcp

logger = logging.getLogger(__name__)

def main() -> None:
    """Inicialize the MCP server"""
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logger.info("Starting MCP Server.")
    try:
        mcp.run(transport="stdio")

    except Exception:
        logger.exception("MCP Server Fatal Error.")
        sys.exit(1)


if __name__ == "__main__":
    main()
