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
"""

import sys
import discord
from discord.ext import commands
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

    return config, logger, bot


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

    Exits with code 1 on unrecoverable errors.
    """
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
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
