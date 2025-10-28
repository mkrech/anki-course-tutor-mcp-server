"""MCP server entry point."""

import logging
import sys
from pathlib import Path

from anki_course_tutor.config import ConfigLoader
from anki_course_tutor.mcp_server import run_server

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the MCP server."""
    try:
        # Load configuration
        config = ConfigLoader.load()

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, config.logging.level),
            format=config.logging.format,
        )

        logger.info("Anki Course Tutor MCP Server starting...")
        logger.info("Configuration loaded (in-memory mode)")

        logger.info("Starting MCP server...")

        # Run MCP server with config
        run_server(config=config)

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Creating default configuration...")
        ConfigLoader.create_default()
        logger.info("Default config.yaml created. Please review and restart.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
