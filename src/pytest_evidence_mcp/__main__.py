import logging
import sys

from pytest_evidence_mcp.server import mcp


def main() -> None:
    """Inicialize the MCP server"""
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logging.info("Starting MCP Server.")
    try:
        mcp.run(transport="stdio")

    except Exception:
        logging.exception("MCP Server Fatal Error.")
        sys.exit(1)


if __name__ == "__main__":
    main()
