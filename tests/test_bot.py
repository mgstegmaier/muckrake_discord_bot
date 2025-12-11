"""
Tests for Discord bot connection and initialization.

These are integration-style tests that verify the bot module works correctly
with minimal mocking. We use a test environment file to provide required config.
"""

import pytest
import discord
from discord.ext import commands
from unittest.mock import Mock, patch
import os
import sys


# Load test environment before importing bot
os.environ['DISCORD_TOKEN'] = 'test-token-value'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['BASE_IMAGE_URL'] = 'https://example.com/images/'


class TestBotModule:
    """Test bot module imports and initializes correctly."""

    def test_bot_module_can_be_imported(self):
        """Bot module should import without errors when env vars are set."""
        # Import should work with our test environment
        import app.bot
        assert app.bot is not None

    def test_bot_instance_exists(self):
        """Bot module should have a bot instance."""
        import app.bot
        assert hasattr(app.bot, 'bot')
        assert app.bot.bot is not None

    def test_bot_is_commands_bot(self):
        """Bot instance should be a commands.Bot."""
        import app.bot
        assert isinstance(app.bot.bot, commands.Bot)

    def test_bot_has_guilds_intent(self):
        """Bot should have guilds intent enabled."""
        import app.bot
        assert app.bot.bot.intents.guilds is True

    def test_config_instance_exists(self):
        """Bot module should have a config instance."""
        import app.bot
        assert hasattr(app.bot, 'config')
        assert app.bot.config is not None

    def test_logger_instance_exists(self):
        """Bot module should have a logger instance."""
        import app.bot
        assert hasattr(app.bot, 'logger')
        assert app.bot.logger is not None


class TestCreateBotInstance:
    """Test the create_bot_instance function."""

    def test_create_bot_instance_returns_tuple(self):
        """create_bot_instance should return (config, logger, bot)."""
        from app.bot import create_bot_instance

        config, logger, bot = create_bot_instance()

        assert config is not None
        assert logger is not None
        assert bot is not None

    def test_create_bot_instance_bot_type(self):
        """create_bot_instance should return commands.Bot instance."""
        from app.bot import create_bot_instance

        _, _, bot = create_bot_instance()

        assert isinstance(bot, commands.Bot)

    def test_create_bot_instance_bot_has_intents(self):
        """Bot from create_bot_instance should have guilds intent."""
        from app.bot import create_bot_instance

        _, _, bot = create_bot_instance()

        assert bot.intents.guilds is True


class TestMainFunction:
    """Test the main entry point."""

    @patch('app.bot.bot')
    def test_main_calls_bot_run(self, mock_bot):
        """main() should call bot.run() with the discord token."""
        from app.bot import main
        import app.bot

        # Mock the bot.run method to avoid actual connection
        mock_bot.run = Mock()

        # Mock the module-level config to provide token
        with patch.object(app.bot, 'config') as mock_config:
            mock_config.discord_token = 'test-token-123'

            # Call main
            main()

            # Verify bot.run was called with the token
            mock_bot.run.assert_called_once_with('test-token-123')

    @patch('app.bot.bot')
    def test_main_handles_keyboard_interrupt(self, mock_bot):
        """main() should handle KeyboardInterrupt gracefully."""
        from app.bot import main
        import app.bot

        # Mock bot.run to raise KeyboardInterrupt
        mock_bot.run = Mock(side_effect=KeyboardInterrupt())

        with patch.object(app.bot, 'config') as mock_config:
            mock_config.discord_token = 'test-token'

            # Should exit with code 0 on KeyboardInterrupt
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    @patch('app.bot.bot')
    def test_main_handles_login_failure(self, mock_bot):
        """main() should handle Discord LoginFailure."""
        from app.bot import main
        import app.bot

        # Mock bot.run to raise LoginFailure
        mock_bot.run = Mock(side_effect=discord.LoginFailure('Invalid token'))

        with patch.object(app.bot, 'config') as mock_config:
            mock_config.discord_token = 'invalid-token'

            # Should exit with code 1 on LoginFailure
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
