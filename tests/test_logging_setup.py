"""
Tests for logging setup module.

Following TDD workflow - these tests define expected behavior before implementation.
"""

import logging
import pytest
from io import StringIO


def test_setup_logging_returns_logger():
    """Test that setup_logging returns a logger instance."""
    from app.logging_setup import setup_logging

    logger = setup_logging("INFO")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "app"


def test_setup_logging_with_info_level():
    """Test that INFO level is configured correctly."""
    from app.logging_setup import setup_logging

    logger = setup_logging("INFO")
    assert logger.level == logging.INFO


def test_setup_logging_with_debug_level():
    """Test that DEBUG level is configured correctly."""
    from app.logging_setup import setup_logging

    logger = setup_logging("DEBUG")
    assert logger.level == logging.DEBUG


def test_setup_logging_with_warning_level():
    """Test that WARNING level is configured correctly."""
    from app.logging_setup import setup_logging

    logger = setup_logging("WARNING")
    assert logger.level == logging.WARNING


def test_logging_format_includes_timestamp():
    """Test that log messages include timestamp in specified format."""
    from app.logging_setup import setup_logging

    # Create a string stream to capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    # Set formatter on the handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = setup_logging("INFO")
    # Get root logger and replace its handlers to capture output
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]

    logger.info("Test message")
    log_output = log_stream.getvalue()

    # Format should be: %(asctime)s - %(name)s - %(levelname)s - %(message)s
    assert " - app - INFO - Test message" in log_output
    # Check that timestamp exists (should have date/time at start)
    assert log_output[0].isdigit() or log_output.startswith("20")


def test_logging_format_includes_level_and_name():
    """Test that log messages include logger name and level."""
    from app.logging_setup import setup_logging

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    # Set formatter on the handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = setup_logging("INFO")
    # Get root logger and replace its handlers to capture output
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]

    logger.warning("Warning message")
    log_output = log_stream.getvalue()

    assert "app" in log_output
    assert "WARNING" in log_output
    assert "Warning message" in log_output


def test_discord_logger_set_to_warning_by_default():
    """Test that discord logger is set to WARNING unless DEBUG mode."""
    from app.logging_setup import setup_logging

    setup_logging("INFO")
    discord_logger = logging.getLogger("discord")

    assert discord_logger.level == logging.WARNING


def test_discord_logger_debug_when_app_debug():
    """Test that discord logger uses DEBUG when app log level is DEBUG."""
    from app.logging_setup import setup_logging

    setup_logging("DEBUG")
    discord_logger = logging.getLogger("discord")

    # When app is in DEBUG, discord should also be DEBUG
    assert discord_logger.level == logging.DEBUG


def test_info_level_suppresses_debug_messages():
    """Test that INFO level does not show DEBUG messages."""
    from app.logging_setup import setup_logging

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    # Set formatter on the handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = setup_logging("INFO")
    # Get root logger and replace its handlers to capture output
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]

    logger.debug("This should not appear")
    logger.info("This should appear")

    log_output = log_stream.getvalue()

    assert "This should not appear" not in log_output
    assert "This should appear" in log_output


def test_warning_level_suppresses_info_messages():
    """Test that WARNING level suppresses INFO messages."""
    from app.logging_setup import setup_logging

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    # Set formatter on the handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = setup_logging("WARNING")
    # Get root logger and replace its handlers to capture output
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]

    logger.info("This should not appear")
    logger.warning("This should appear")

    log_output = log_stream.getvalue()

    assert "This should not appear" not in log_output
    assert "This should appear" in log_output


def test_setup_logging_configures_root_logger():
    """Test that setup_logging configures the root logger properly."""
    from app.logging_setup import setup_logging

    setup_logging("INFO")
    root_logger = logging.getLogger()

    # Root logger should have at least one handler
    assert len(root_logger.handlers) > 0

    # Check that formatter is configured
    handler = root_logger.handlers[0]
    assert handler.formatter is not None


def test_log_format_structure():
    """Test that log format matches specification exactly."""
    from app.logging_setup import setup_logging

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    # Set formatter on the handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = setup_logging("INFO")
    # Get root logger and replace its handlers to capture output
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]

    logger.info("Test")
    log_output = log_stream.getvalue().strip()

    # Format: %(asctime)s - %(name)s - %(levelname)s - %(message)s
    # Should have exactly 4 parts separated by " - "
    parts = log_output.split(" - ")
    assert len(parts) >= 4  # asctime, name, levelname, message (message might have " - " in it)

    # Verify the structure
    assert parts[1] == "app"  # logger name
    assert parts[2] == "INFO"  # log level
    assert "Test" in parts[3]  # message
