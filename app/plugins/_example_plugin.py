"""
Example plugin demonstrating the plugin system.

This file is disabled by default (starts with underscore).
To enable it, rename to 'example_plugin.py' (remove the leading underscore).

This plugin demonstrates:
1. How to create a simple slash command
2. How to access the bot instance
3. How to return a plugin name from setup()
4. Proper documentation structure

For more complex plugins, you can:
- Use the Plugin base class for structured plugins
- Access bot.tree for command registration
- Register event handlers
- Add configuration
- Import utilities from app.utils
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger("app.plugins.example")


async def setup(bot: commands.Bot) -> str:
    """
    Initialize the example plugin.

    This is the entry point for the plugin. The bot will call this function
    during startup to register the plugin's functionality.

    Args:
        bot: The Discord bot instance

    Returns:
        str: Plugin name for logging (optional but recommended)

    Example:
        To create a plugin, define an async setup() function that:
        1. Registers slash commands using bot.tree.command()
        2. Registers event handlers using @bot.event
        3. Returns a plugin name string

    Note:
        - Commands registered here are global by default
        - Use guild=discord.Object(id=...) for server-specific commands
        - Errors in setup() will be logged but won't crash the bot
    """
    # Example 1: Simple slash command
    @bot.tree.command(
        name="example",
        description="An example command from a plugin"
    )
    async def example_command(interaction: discord.Interaction):
        """
        Example slash command handler.

        This command demonstrates how to create a basic slash command
        that responds to user interactions.

        Args:
            interaction: The Discord interaction from the slash command
        """
        await interaction.response.send_message(
            "Hello from the example plugin! This command was added dynamically.",
            ephemeral=True
        )
        logger.info(f"Example command used by {interaction.user.id}")

    # Example 2: Command with parameters
    @bot.tree.command(
        name="greet",
        description="Greet someone"
    )
    @app_commands.describe(
        name="The name of the person to greet",
        message="Optional custom message"
    )
    async def greet_command(
        interaction: discord.Interaction,
        name: str,
        message: str = "Hello"
    ):
        """
        Example command with parameters.

        This demonstrates how to create commands that accept user input.

        Args:
            interaction: The Discord interaction
            name: Required parameter - the person to greet
            message: Optional parameter with default value
        """
        greeting = f"{message}, {name}!"
        await interaction.response.send_message(greeting, ephemeral=True)
        logger.info(f"Greet command used by {interaction.user.id} for {name}")

    # Example 3: Event handler
    @bot.event
    async def on_message(message: discord.Message):
        """
        Example event handler.

        This shows how to register event handlers from a plugin.
        Note: This will override any existing on_message handler!

        For non-overriding behavior, use bot.add_listener() instead.

        Args:
            message: The message that was sent
        """
        # Don't respond to ourselves
        if message.author == bot.user:
            return

        # Example: Log messages starting with "!"
        if message.content.startswith("!"):
            logger.debug(f"Command-like message: {message.content}")

    logger.info("Example plugin initialized")
    return "example_plugin"


# Alternative approach: Using the Plugin base class
# This is more structured for complex plugins
#
# from app.plugins import Plugin
#
# class ExamplePlugin(Plugin):
#     name = "example_plugin"
#     description = "Demonstrates the plugin system"
#
#     async def setup(self, bot: commands.Bot):
#         """Initialize the plugin."""
#         @bot.tree.command(name="example")
#         async def example_command(interaction: discord.Interaction):
#             await interaction.response.send_message("Hello!", ephemeral=True)
#
#         logger.info("Example plugin initialized")
#
# async def setup(bot: commands.Bot) -> str:
#     """Setup function using Plugin class."""
#     plugin = ExamplePlugin()
#     await plugin.setup(bot)
#     return plugin.name
