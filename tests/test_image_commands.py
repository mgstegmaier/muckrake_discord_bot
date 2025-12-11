"""
Tests for the image commands module (slash command registration).

This module tests the dynamic registration and syncing of Discord slash commands
based on server configurations.
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from discord.ext import commands
from discord import app_commands
import discord

from app.config import Config, ServerConfig
from app.commands.image_commands import ImageCommands, setup_commands, sync_commands
from app.utils.permissions import check_permission


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot with command tree."""
    bot = Mock(spec=commands.Bot)
    bot.tree = Mock(spec=app_commands.CommandTree)
    bot.tree.add_command = Mock()
    bot.tree.sync = AsyncMock(return_value=[])
    bot.get_cog = Mock()
    return bot


@pytest.fixture
def mock_config():
    """Create a mock Config with test server configurations."""
    config = Mock(spec=Config)
    config.base_image_url = "https://heckatron.xyz/images/"

    # Server 1: Two commands
    server1 = ServerConfig(
        name="Test Server 1",
        allowed_roles=["Admin"],
        images={
            "tapsign": {"url": "tapsign.jpg", "title": "Tap Sign"},
            "heartbreaking": {"url": "heartbreaking.jpg", "title": "Heartbreaking"}
        }
    )

    # Server 2: One command
    server2 = ServerConfig(
        name="Test Server 2",
        allowed_roles=["Moderator"],
        images={
            "tapsign": {"url": "tapsign.jpg", "title": "Tap Sign"}
        }
    )

    config.servers = {
        "123456789": server1,
        "987654321": server2
    }
    config.get_server_config = Mock(side_effect=lambda sid: config.servers.get(sid))

    return config


class TestImageCommandsCog:
    """Tests for the ImageCommands cog class."""

    def test_cog_initialization(self, mock_bot, mock_config):
        """Test that ImageCommands cog initializes with bot and config."""
        cog = ImageCommands(mock_bot, mock_config)

        assert cog.bot == mock_bot
        assert cog.config == mock_config

    @pytest.mark.asyncio
    async def test_handle_image_command_authorized_user_gets_embed(self, mock_bot, mock_config):
        """Test that authorized user gets embed response with image."""
        cog = ImageCommands(mock_bot, mock_config)

        # Create mock interaction with authorized user
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 123456789
        interaction.user = Mock()
        interaction.user.id = 12345
        # Create role mock with proper name attribute
        admin_role = Mock()
        admin_role.name = "Admin"
        interaction.user.roles = [admin_role]
        interaction.response.send_message = AsyncMock()

        # Call handler with valid image key
        await cog._handle_image_command(interaction, "tapsign")

        # Verify embed was sent
        interaction.response.send_message.assert_called_once()
        call_kwargs = interaction.response.send_message.call_args[1]

        assert "embed" in call_kwargs
        embed = call_kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert embed.title == "Tap Sign"
        assert embed.image.url == "https://heckatron.xyz/images/tapsign.jpg"

    @pytest.mark.asyncio
    async def test_handle_image_command_unauthorized_user_denied(self, mock_bot, mock_config):
        """Test that unauthorized user gets ephemeral permission denied message."""
        cog = ImageCommands(mock_bot, mock_config)

        # Create mock interaction with unauthorized user (no Admin role)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 123456789
        interaction.user = Mock()
        interaction.user.id = 12345
        # Create role mock with non-admin role
        member_role = Mock()
        member_role.name = "Member"
        interaction.user.roles = [member_role]
        interaction.response.send_message = AsyncMock()

        # Call handler
        await cog._handle_image_command(interaction, "tapsign")

        # Verify permission denied message
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        message = call_args[0][0]
        kwargs = call_args[1]

        assert "don't have permission" in message
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_handle_image_command_embed_has_correct_title_and_url(self, mock_bot, mock_config):
        """Test that embed has correct title and image URL from config."""
        cog = ImageCommands(mock_bot, mock_config)

        # Create mock interaction with authorized user
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 123456789
        interaction.user = Mock()
        interaction.user.id = 12345
        # Create role mock with proper name attribute
        admin_role = Mock()
        admin_role.name = "Admin"
        interaction.user.roles = [admin_role]
        interaction.response.send_message = AsyncMock()

        # Test heartbreaking command
        await cog._handle_image_command(interaction, "heartbreaking")

        # Verify embed details
        call_kwargs = interaction.response.send_message.call_args[1]
        embed = call_kwargs["embed"]

        assert embed.title == "Heartbreaking"
        assert embed.image.url == "https://heckatron.xyz/images/heartbreaking.jpg"

    @pytest.mark.asyncio
    @patch('app.commands.image_commands.check_permission')
    async def test_handle_image_command_checks_permission_before_posting(self, mock_check_permission, mock_bot, mock_config):
        """Test that permission check is called before sending response."""
        mock_check_permission.return_value = True
        cog = ImageCommands(mock_bot, mock_config)

        # Create mock interaction
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 123456789
        interaction.user = Mock()
        interaction.user.id = 12345
        interaction.response.send_message = AsyncMock()

        # Call handler
        await cog._handle_image_command(interaction, "tapsign")

        # Verify permission check was called
        mock_check_permission.assert_called_once_with(interaction, mock_config)

    @pytest.mark.asyncio
    async def test_handle_image_command_invalid_server(self, mock_bot, mock_config):
        """Test that _handle_image_command handles unconfigured server."""
        cog = ImageCommands(mock_bot, mock_config)

        # Create mock interaction with unknown server
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 999999999
        interaction.user = Mock()
        # Create role mock with proper name attribute
        admin_role = Mock()
        admin_role.name = "Admin"
        interaction.user.roles = [admin_role]
        interaction.response.send_message = AsyncMock()

        # Call handler
        await cog._handle_image_command(interaction, "tapsign")

        # Verify permission denied (server not configured means no permission)
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        message = call_args[0][0]
        kwargs = call_args[1]

        assert "don't have permission" in message
        assert kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_handle_image_command_invalid_image(self, mock_bot, mock_config):
        """Test that _handle_image_command handles unknown image key."""
        cog = ImageCommands(mock_bot, mock_config)

        # Create mock interaction with valid server, invalid image
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild_id = 123456789
        interaction.user = Mock()
        # Create role mock with proper name attribute
        admin_role = Mock()
        admin_role.name = "Admin"
        interaction.user.roles = [admin_role]
        interaction.response.send_message = AsyncMock()

        # Call handler with invalid image key (even with permission, image doesn't exist)
        await cog._handle_image_command(interaction, "unknown_image")

        # Verify permission denied (image not found means can't post)
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        message = call_args[0][0]
        kwargs = call_args[1]

        assert "don't have permission" in message
        assert kwargs.get("ephemeral") is True


class TestSetupCommands:
    """Tests for the setup_commands function."""

    @pytest.mark.asyncio
    async def test_setup_registers_commands_for_all_servers(self, mock_bot, mock_config):
        """Test that setup_commands registers commands for each server."""
        await setup_commands(mock_bot, mock_config)

        # Server 1 has 2 images, Server 2 has 1 image = 3 total commands
        assert mock_bot.tree.add_command.call_count == 3

    @pytest.mark.asyncio
    async def test_setup_commands_uses_guild_objects(self, mock_bot, mock_config):
        """Test that setup_commands creates guild-specific commands."""
        await setup_commands(mock_bot, mock_config)

        # Verify add_command was called with guild parameter
        calls = mock_bot.tree.add_command.call_args_list

        # All calls should have guild parameter
        for call in calls:
            kwargs = call[1]
            assert "guild" in kwargs
            assert isinstance(kwargs["guild"], discord.Object)

    @pytest.mark.asyncio
    async def test_setup_commands_names_match_image_keys(self, mock_bot, mock_config):
        """Test that command names match image keys from config."""
        await setup_commands(mock_bot, mock_config)

        # Extract command names from calls
        calls = mock_bot.tree.add_command.call_args_list
        command_names = [call[0][0].name for call in calls]

        # Should have tapsign and heartbreaking for server 1, tapsign for server 2
        assert command_names.count("tapsign") == 2
        assert command_names.count("heartbreaking") == 1


class TestSyncCommands:
    """Tests for the sync_commands function."""

    @pytest.mark.asyncio
    async def test_sync_calls_sync_for_each_guild(self, mock_bot, mock_config):
        """Test that sync_commands syncs to each configured guild."""
        mock_bot.tree.sync = AsyncMock(return_value=["cmd1", "cmd2"])

        await sync_commands(mock_bot, mock_config)

        # Should sync to 2 guilds
        assert mock_bot.tree.sync.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_uses_guild_objects(self, mock_bot, mock_config):
        """Test that sync_commands uses discord.Object for guild IDs."""
        mock_bot.tree.sync = AsyncMock(return_value=[])

        await sync_commands(mock_bot, mock_config)

        # Verify sync was called with guild parameter
        calls = mock_bot.tree.sync.call_args_list
        for call in calls:
            kwargs = call[1]
            assert "guild" in kwargs
            assert isinstance(kwargs["guild"], discord.Object)

    @pytest.mark.asyncio
    async def test_sync_handles_errors_gracefully(self, mock_bot, mock_config):
        """Test that sync_commands continues on error and doesn't raise."""
        # Make first sync fail, second succeed
        mock_bot.tree.sync = AsyncMock(side_effect=[
            Exception("Discord API error"),
            ["cmd1"]
        ])

        # Should not raise exception
        await sync_commands(mock_bot, mock_config)

        # Both guilds should have been attempted
        assert mock_bot.tree.sync.call_count == 2
