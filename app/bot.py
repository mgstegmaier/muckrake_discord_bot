"""
Discord bot connection and initialization for Muckraker Discord Bot.

This module creates and configures the Discord bot instance, sets up logging,
loads configuration, and handles connection to Discord servers.

Key Features:
- Uses discord.py commands.Bot for slash command support
- Configures required intents (guilds for server awareness)
- Loads configuration from environment and servers.json
- Implements on_ready event for connection logging
- Handles ConfigError and Discord connection errors gracefully
- Graceful shutdown handling for SIGTERM and SIGINT signals
"""

import sys
import signal
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from app.config import Config, ConfigError
from app.logging_setup import setup_logging


def create_bot_instance():
    """
    Create and configure the Discord bot instance.

    Returns:
        Tuple of (config, logger, bot) instances

    Raises:
        ConfigError: If configuration loading fails
    """
    # Load configuration
    config = Config()
    logger = setup_logging(config.log_level)

    # Configure Discord intents
    # Guilds intent required for basic server information
    intents = discord.Intents.default()
    intents.guilds = True

    # Create bot instance
    # Using "!" prefix but slash commands will be primary interface
    bot = commands.Bot(command_prefix="!", intents=intents)

    # Register event handlers
    @bot.event
    async def on_ready():
        """
        Event handler called when bot successfully connects to Discord.

        Logs bot username, ID, and number of connected servers.
        This provides confirmation that the bot is running and where it's active.
        """
        logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} servers")

    # Register global error handler for slash commands
    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """
        Global error handler for all slash commands.

        Handles different error types appropriately:
        - Forbidden: Bot lacks permissions
        - NotFound: Message/channel deleted (logged, no response)
        - CommandOnCooldown: Command used too quickly
        - MissingPermissions: User lacks permissions
        - General exceptions: Unexpected errors

        All error messages are ephemeral (visible only to user).
        Errors are logged with full context including user ID, server ID, and command name.

        Args:
            interaction: The interaction that triggered the error
            error: The error that occurred
        """
        try:
            # Extract context for logging
            user_id = interaction.user.id if interaction.user else "unknown"
            guild_id = interaction.guild_id if interaction.guild_id else "DM"
            command_name = interaction.command.name if interaction.command else "unknown"

            # Handle specific error types
            if isinstance(error, discord.errors.Forbidden):
                # Bot doesn't have permission to perform action
                logger.warning(
                    f"Permission denied for command '{command_name}' "
                    f"(user: {user_id}, guild: {guild_id}): {error}"
                )
                message = "I don't have permission to do that in this server."

            elif isinstance(error, discord.errors.NotFound):
                # Message or channel was deleted - log but don't respond
                logger.warning(
                    f"Resource not found for command '{command_name}' "
                    f"(user: {user_id}, guild: {guild_id}): {error}"
                )
                return  # Don't send message to user

            elif isinstance(error, app_commands.CommandOnCooldown):
                # Command used too quickly
                message = "This command is on cooldown. Try again later."

            elif isinstance(error, app_commands.MissingPermissions):
                # User doesn't have permission
                message = "You don't have permission to use this command."

            else:
                # Unexpected error - log with full traceback
                logger.error(
                    f"Unexpected error in command '{command_name}' "
                    f"(user: {user_id}, guild: {guild_id}): {error}",
                    exc_info=True
                )
                message = "Something went wrong. Please try again later."

            # Send error message to user
            # Use followup if interaction already responded, otherwise use response
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)

        except Exception as e:
            # Error handler itself failed - log but don't crash bot
            logger.error(f"Error in error handler: {e}", exc_info=True)

    return config, logger, bot


async def shutdown_handler(bot, logger):
    """
    Handle graceful shutdown of the Discord bot.

    Logs shutdown initiation, closes the Discord connection cleanly,
    and logs shutdown completion.

    Args:
        bot: The Discord bot instance to shut down
        logger: Logger instance for shutdown messages

    This function is called by signal handlers (SIGTERM, SIGINT) and ensures
    the bot disconnects cleanly from Discord before the process exits.
    """
    logger.info("Shutting down bot...")
    await bot.close()
    logger.info("Shutdown complete")


# Initialize bot on module import
# Wrapped in try-except for graceful config error handling
try:
    config, logger, bot = create_bot_instance()
except ConfigError as e:
    # Log to stderr since logging isn't set up yet
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    """
    Main entry point for the bot application.

    Attempts to connect to Discord using the configured token.
    Handles common connection errors with clear error messages.
    Sets up signal handlers for graceful shutdown on SIGTERM and SIGINT.

    Exits with code 1 on unrecoverable errors.
    """
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        """Handle SIGTERM and SIGINT signals for graceful shutdown."""
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        # Run the async shutdown handler in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule shutdown
                asyncio.create_task(shutdown_handler(bot, logger))
            else:
                # If loop is not running, run shutdown directly
                loop.run_until_complete(shutdown_handler(bot, logger))
        except Exception as e:
            logger.error(f"Error during signal handler shutdown: {e}")
        finally:
            sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        logger.info("Starting Discord bot...")
        bot.run(config.discord_token)
    except discord.LoginFailure as e:
        logger.error(f"Failed to log in to Discord: Invalid token - {e}")
        sys.exit(1)
    except discord.HTTPException as e:
        logger.error(f"Discord HTTP error occurred: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested via keyboard interrupt")
        # Run shutdown handler for clean disconnect
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(shutdown_handler(bot, logger))
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        logger.info("Bot process ending")


if __name__ == "__main__":
    main()
