"""
Tests for graceful shutdown functionality.

This module tests that the Discord bot handles shutdown signals (SIGTERM, SIGINT)
gracefully by:
- Logging shutdown initiation
- Closing the Discord connection cleanly
- Logging shutdown completion
- Exiting within reasonable time
"""

import asyncio
import logging
import os
from unittest.mock import AsyncMock, Mock, patch
import pytest


# Load test environment before importing bot
os.environ['DISCORD_TOKEN'] = 'test-token-value'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['BASE_IMAGE_URL'] = 'https://example.com/images/'

from app.bot import create_bot_instance


class TestGracefulShutdown:
    """Tests for graceful shutdown signal handling."""

    @pytest.mark.asyncio
    async def test_shutdown_handler_logs_and_closes_bot(self):
        """Test that shutdown handler logs messages and closes bot connection."""
        # Arrange
        config, logger, bot = create_bot_instance()

        # Create mock logger to capture log calls
        mock_logger = Mock(spec=logging.Logger)

        # Mock bot.close() to verify it's called
        bot.close = AsyncMock()

        # Import the shutdown handler (will fail initially - not implemented yet)
        from app.bot import shutdown_handler

        # Act
        await shutdown_handler(bot, mock_logger)

        # Assert - verify shutdown was logged
        assert mock_logger.info.call_count >= 1
        shutdown_log_calls = [
            call for call in mock_logger.info.call_args_list
            if 'shutdown' in str(call).lower() or 'shutting down' in str(call).lower()
        ]
        assert len(shutdown_log_calls) >= 1, "Expected shutdown initiation to be logged"

        # Assert - verify bot.close() was called
        bot.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_handler_completes_within_timeout(self):
        """Test that shutdown completes within reasonable time (10 seconds)."""
        # Arrange
        config, logger, bot = create_bot_instance()
        bot.close = AsyncMock()

        # Import shutdown handler
        from app.bot import shutdown_handler

        # Act & Assert - shutdown should complete within 10 seconds
        try:
            await asyncio.wait_for(
                shutdown_handler(bot, logger),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Shutdown did not complete within 10 seconds")

    def test_main_handles_keyboard_interrupt(self):
        """Test that KeyboardInterrupt (Ctrl+C) is handled gracefully."""
        # This test verifies the existing KeyboardInterrupt handling
        # We'll check that it's present in the code
        import inspect
        from app.bot import main

        source = inspect.getsource(main)
        assert 'KeyboardInterrupt' in source, "main() should handle KeyboardInterrupt"
        assert 'logger.info' in source or 'logger' in source, "Should log shutdown"
