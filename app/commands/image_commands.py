"""
Discord slash command registration for image posting.

This module handles dynamic registration of slash commands based on the server
configuration. Each image defined in servers.json becomes a guild-specific
slash command that can be invoked by authorized users.

Key Features:
- Dynamic command registration from config
- Guild-specific commands (fast updates)
- Command syncing with Discord API
- Generic handler for all image commands

Example:
    >>> from app.commands.image_commands import ImageCommands, setup_commands, sync_commands
    >>> config = Config()
    >>> bot = commands.Bot(...)
    >>> await bot.add_cog(ImageCommands(bot, config))
    >>> await setup_commands(bot, config)
    >>> await sync_commands(bot, config)
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging

from app.config import Config
from app.utils.permissions import check_permission

logger = logging.getLogger("app.commands.image")


class ImageCommands(commands.Cog):
    """
    Cog for handling image posting slash commands.

    This cog provides a generic handler for all image commands. The actual
    command registration is done dynamically via setup_commands() based on
    the server configuration.

    Attributes:
        bot: The Discord bot instance
        config: Configuration object with server and image definitions
    """

    def __init__(self, bot: commands.Bot, config: Config):
        """
        Initialize the ImageCommands cog.

        Args:
            bot: Discord bot instance
            config: Configuration object
        """
        self.bot = bot
        self.config = config
        logger.info("ImageCommands cog initialized")

    async def _handle_image_command(self, interaction: discord.Interaction, image_key: str):
        """
        Generic handler for all image commands.

        This method is called by dynamically registered slash commands.
        It checks permissions, validates the command configuration, and
        posts the image as a Discord embed if authorized.

        Permission Flow:
        1. Check if user has permission via check_permission()
        2. If denied: Send ephemeral "permission denied" message
        3. If allowed: Validate image exists in server config
        4. Create and send Discord embed with image

        Args:
            interaction: Discord interaction from slash command
            image_key: The image identifier (command name)
        """
        server_id = str(interaction.guild_id)
        server_config = self.config.get_server_config(server_id)

        # Check permissions first
        if not check_permission(interaction, self.config):
            await interaction.response.send_message(
                "You don't have permission to use this command",
                ephemeral=True
            )
            return

        # Verify image exists in server config
        if not server_config or image_key not in server_config.images:
            # This shouldn't happen since commands are registered from config,
            # but handle it gracefully just in case
            await interaction.response.send_message(
                "You don't have permission to use this command",
                ephemeral=True
            )
            return

        # Get image data
        image_data = server_config.images[image_key]
        title = image_data["title"]
        # Ensure proper URL construction with slash separator
        base_url = self.config.base_image_url.rstrip('/')
        image_url = f"{base_url}/{image_data['url']}"

        # Create embed with image
        embed = discord.Embed(title=title)
        embed.set_image(url=image_url)

        # Send embed
        await interaction.response.send_message(embed=embed)

        # Log successful command execution
        logger.info(
            f"Image command '{image_key}' executed by "
            f"user {interaction.user.id} in server {server_id}"
        )


async def setup_commands(bot: commands.Bot, config: Config):
    """
    Register image commands for all configured servers.

    This function dynamically creates slash commands based on the images
    defined in each server's configuration. Commands are registered as
    guild-specific commands for faster updates.

    The command callback uses a closure to capture the image_key, allowing
    a single handler function to service all commands.

    Args:
        bot: Discord bot instance with command tree
        config: Configuration object with server definitions

    Example:
        >>> await setup_commands(bot, config)
        # INFO: Registered 2 commands for server Test Server (123456789)
    """
    for server_id, server_config in config.servers.items():
        guild = discord.Object(id=int(server_id))

        for image_name, image_data in server_config.images.items():
            # Get the title for the command description
            title = image_data.get("title", image_name)

            # Create command callback with closure to capture image_name
            # Using default argument to avoid late binding issues
            async def image_callback(
                interaction: discord.Interaction,
                img_key: str = image_name
            ):
                """Dynamically generated image command callback."""
                cog = bot.get_cog("ImageCommands")
                if cog:
                    await cog._handle_image_command(interaction, img_key)

            # Create app_command with proper name and description
            command = app_commands.Command(
                name=image_name,
                description=f"Post the {title} image",
                callback=image_callback
            )

            # Add to bot's tree for this guild
            bot.tree.add_command(command, guild=guild)

        logger.info(
            f"Registered {len(server_config.images)} commands for "
            f"server {server_config.name} ({server_id})"
        )


async def sync_commands(bot: commands.Bot, config: Config):
    """
    Sync commands with Discord for all configured guilds.

    This function pushes the registered commands to Discord's API, making
    them visible in the Discord client. Commands are synced per-guild for
    faster propagation (guild commands update instantly vs global commands
    which can take up to 1 hour).

    Errors during sync are logged but don't prevent other guilds from syncing.

    Args:
        bot: Discord bot instance with command tree
        config: Configuration object with server definitions

    Example:
        >>> await sync_commands(bot, config)
        # INFO: Synced 2 commands to guild 123456789
        # INFO: Synced 1 commands to guild 987654321
    """
    for server_id in config.servers.keys():
        guild = discord.Object(id=int(server_id))

        try:
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands to guild {server_id}")
        except Exception as e:
            logger.error(
                f"Failed to sync commands to guild {server_id}: {e}",
                exc_info=True
            )
