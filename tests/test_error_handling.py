"""
Tests for bot-level error handling in app/bot.py.

This module tests the global error handler for the bot's command tree,
including handling of Discord-specific errors, permission errors, and
unexpected exceptions.

Test Coverage:
- Discord permission errors (Forbidden)
- Discord not found errors (NotFound)
- Command cooldown errors
- Missing permissions errors
- General unexpected exceptions
- Error context logging (user ID, server ID, command name)
- Bot resilience after errors
"""

import pytest
import discord
from discord import app_commands
from unittest.mock import AsyncMock, MagicMock, patch
import logging
import os

# Set up test environment before importing bot
os.environ['DISCORD_TOKEN'] = 'test-token-value'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['BASE_IMAGE_URL'] = 'https://example.com/images/'

from app.bot import create_bot_instance


class TestErrorHandling:
    """Tests for global error handler on bot.tree."""

    @pytest.fixture
    def bot_setup(self):
        """Create bot instance for testing."""
        config, logger, bot = create_bot_instance()

        # Mock interaction object
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild_id = 123456789
        interaction.user = MagicMock()
        interaction.user.id = 987654321
        interaction.command = MagicMock()
        interaction.command.name = "test_command"
        interaction.response = MagicMock()
        interaction.response.is_done = MagicMock(return_value=False)
        interaction.response.send_message = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        return {
            "bot": bot,
            "logger": logger,
            "config": config,
            "interaction": interaction
        }

    @pytest.mark.asyncio
    async def test_forbidden_error_sends_user_message(self, bot_setup, caplog):
        """Test Forbidden error sends appropriate message to user."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]

        # Verify error handler is registered
        assert bot.tree.on_error is not None, "Error handler not registered on bot.tree"

        # Create Forbidden error
        error = discord.errors.Forbidden(
            response=MagicMock(status=403),
            message="Missing Permissions"
        )

        # Call error handler
        with caplog.at_level(logging.WARNING):
            await bot.tree.on_error(interaction, error)

        # Verify user message sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "permission" in call_args[0][0].lower()
        assert call_args[1]["ephemeral"] is True

        # Verify logged at WARNING level
        assert any(record.levelname == "WARNING" for record in caplog.records)
        warning_log = next(r.message for r in caplog.records if r.levelname == "WARNING")
        assert "987654321" in warning_log  # User ID
        assert "123456789" in warning_log  # Guild ID
        assert "test_command" in warning_log  # Command name

    @pytest.mark.asyncio
    async def test_not_found_error_logs_but_no_response(self, bot_setup, caplog):
        """Test NotFound error logs warning but doesn't respond to user."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]

        assert bot.tree.on_error is not None

        # Create NotFound error
        error = discord.errors.NotFound(
            response=MagicMock(status=404),
            message="Unknown Message"
        )

        # Call error handler
        with caplog.at_level(logging.WARNING):
            await bot.tree.on_error(interaction, error)

        # Verify NO response sent to user
        interaction.response.send_message.assert_not_called()
        interaction.followup.send.assert_not_called()

        # Verify logged at WARNING level
        assert any(record.levelname == "WARNING" for record in caplog.records)
        warning_log = next(r.message for r in caplog.records if r.levelname == "WARNING")
        assert "not found" in warning_log.lower()
        assert "987654321" in warning_log  # User ID
        assert "123456789" in warning_log  # Guild ID

    @pytest.mark.asyncio
    async def test_command_on_cooldown_error(self, bot_setup):
        """Test CommandOnCooldown error sends cooldown message."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]
        logger = bot_setup["logger"]

        assert bot.tree.on_error is not None

        # Create CommandOnCooldown error
        cooldown = MagicMock()
        cooldown.retry_after = 45.5
        error = app_commands.CommandOnCooldown(cooldown, 45.5)

        # Call error handler
        await bot.tree.on_error(interaction, error)

        # Verify cooldown message sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "cooldown" in call_args[0][0].lower()
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_missing_permissions_error(self, bot_setup):
        """Test MissingPermissions error sends permission message."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]

        assert bot.tree.on_error is not None

        # Create MissingPermissions error
        error = app_commands.MissingPermissions(["manage_messages"])

        # Call error handler
        await bot.tree.on_error(interaction, error)

        # Verify permission message sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "permission" in call_args[0][0].lower()
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_general_exception_sends_generic_error(self, bot_setup, caplog):
        """Test unexpected exception sends generic error message."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]

        assert bot.tree.on_error is not None

        # Create unexpected error
        error = ValueError("Something broke internally")

        # Call error handler
        with caplog.at_level(logging.ERROR):
            await bot.tree.on_error(interaction, error)

        # Verify generic message sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "something went wrong" in call_args[0][0].lower()
        assert call_args[1]["ephemeral"] is True

        # Verify logged at ERROR level with exc_info
        assert any(record.levelname == "ERROR" for record in caplog.records)
        error_log = next(r.message for r in caplog.records if r.levelname == "ERROR")
        assert "987654321" in error_log  # User ID
        assert "123456789" in error_log  # Guild ID
        assert "test_command" in error_log  # Command name

    @pytest.mark.asyncio
    async def test_error_after_response_uses_followup(self, bot_setup):
        """Test error handler uses followup if interaction already responded."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]

        # Simulate already-responded interaction
        interaction.response.is_done.return_value = True

        assert bot.tree.on_error is not None

        # Create error
        error = discord.errors.Forbidden(
            response=MagicMock(status=403),
            message="Missing Permissions"
        )

        # Call error handler
        await bot.tree.on_error(interaction, error)

        # Verify followup used instead of response
        interaction.response.send_message.assert_not_called()
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_error_handler_is_resilient(self, bot_setup, caplog):
        """Test error handler doesn't crash if sending message fails."""
        bot = bot_setup["bot"]
        interaction = bot_setup["interaction"]

        # Make send_message raise exception
        interaction.response.send_message.side_effect = Exception("Discord API down")

        assert bot.tree.on_error is not None

        # Create error
        error = ValueError("Original error")

        # Call error handler - should not raise
        with caplog.at_level(logging.ERROR):
            await bot.tree.on_error(interaction, error)

        # Verify handler failure was logged
        # Should have two error logs: one for original, one for handler failure
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) >= 2

        # Verify one is about the error handler failure
        assert any("Error in error handler" in r.message for r in error_records)
