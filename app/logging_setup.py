"""
Logging setup module for Muckraker Discord Bot.

Provides centralized logging configuration with support for different log levels
and special handling for discord.py library logging.
"""

import logging
import sys

# Log format string as specified in requirements
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging for the application.

    Sets up logging with a standardized format and configures both the app logger
    and discord.py logger appropriately based on the requested log level.

    Args:
        log_level: Desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to INFO if not specified.

    Returns:
        Logger instance configured for the application with name 'app'.

    Format:
        %(asctime)s - %(name)s - %(levelname)s - %(message)s

    Special behavior:
        - Discord.py logger is set to WARNING by default to avoid noise
        - When app log level is DEBUG, discord.py logger also uses DEBUG
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicate logs
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter with specified format
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Get or create app logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(numeric_level)

    # Configure discord.py logger
    # Set to WARNING unless we're in DEBUG mode, to reduce noise
    discord_logger = logging.getLogger("discord")
    if numeric_level == logging.DEBUG:
        discord_logger.setLevel(logging.DEBUG)
    else:
        discord_logger.setLevel(logging.WARNING)

    return app_logger
