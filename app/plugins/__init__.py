"""
Plugin system for extensible bot functionality.

This module provides the base Plugin class and plugin loading infrastructure
for dynamically extending bot functionality through code-based plugins.

Key Features:
- Abstract Plugin base class for defining plugins
- Plugin discovery (scans app/plugins/ for modules)
- Plugin loading with error handling
- Graceful handling of invalid plugins

Example:
    Creating a plugin:

    from app.plugins import Plugin

    class MyPlugin(Plugin):
        name = "my_plugin"
        description = "My custom plugin"

        async def setup(self, bot):
            # Register commands, event handlers, etc.
            pass

    Loading plugins:

    from app.plugins import load_plugins

    bot = commands.Bot(...)
    loaded_plugins = await load_plugins(bot)
"""

from abc import ABC, abstractmethod
import os
import importlib
import logging
from typing import List
from discord.ext import commands

logger = logging.getLogger("app.plugins")


class Plugin(ABC):
    """
    Abstract base class for bot plugins.

    All plugins must inherit from this class and implement the required
    attributes and methods.

    Required Attributes:
        name (str): Unique identifier for the plugin
        description (str): Human-readable description of the plugin

    Required Methods:
        setup(bot): Async method called to initialize the plugin

    Example:
        class ExamplePlugin(Plugin):
            name = "example"
            description = "An example plugin"

            async def setup(self, bot):
                @bot.tree.command(name="example")
                async def example_command(interaction):
                    await interaction.response.send_message("Hello from plugin!")
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for the plugin.

        Returns:
            str: Plugin name (lowercase, no spaces)
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of the plugin.

        Returns:
            str: Plugin description
        """
        pass

    @abstractmethod
    async def setup(self, bot: commands.Bot):
        """
        Initialize the plugin.

        Called during bot startup to register commands, event handlers,
        or perform any other setup required by the plugin.

        Args:
            bot: The Discord bot instance

        Raises:
            Exception: Any errors during setup will be caught and logged
        """
        pass


async def load_plugins(bot: commands.Bot) -> List[str]:
    """
    Discover and load all plugins from the app/plugins/ directory.

    This function scans the plugins directory for Python modules and attempts
    to load each one. Files are included if they:
    - Have a .py extension
    - Don't start with underscore (_)
    - Are not __init__.py

    For each valid module, the function looks for a setup() function and calls
    it with the bot instance. If setup() returns a string, that's treated as
    the plugin name and added to the returned list.

    Invalid plugins (syntax errors, import errors, setup failures) are logged
    but don't crash the bot - loading continues with remaining plugins.

    Args:
        bot: The Discord bot instance to pass to plugins

    Returns:
        List of successfully loaded plugin names

    Example:
        bot = commands.Bot(...)
        loaded = await load_plugins(bot)
        logger.info(f"Loaded {len(loaded)} plugins: {loaded}")
    """
    loaded_plugins = []

    # Get the plugins directory path
    plugins_dir = os.path.dirname(__file__)

    # Get list of files in plugins directory
    try:
        files = os.listdir(plugins_dir)
    except OSError as e:
        logger.error(f"Failed to read plugins directory: {e}")
        return loaded_plugins

    # Filter for valid plugin files
    plugin_files = [
        f[:-3]  # Remove .py extension
        for f in files
        if f.endswith('.py')
        and f != '__init__.py'
        and not f.startswith('_')
    ]

    # Load each plugin
    for plugin_name in plugin_files:
        try:
            # Import the module
            module = importlib.import_module(f'app.plugins.{plugin_name}')

            # Look for setup function
            if not hasattr(module, 'setup'):
                logger.warning(
                    f"Plugin '{plugin_name}' has no setup() function, skipping"
                )
                continue

            # Call setup function
            result = await module.setup(bot)

            # If setup returns a name, add it to loaded list
            if result:
                loaded_plugins.append(result)
                logger.info(f"Loaded plugin: {result}")
            else:
                # If no name returned, use module name
                loaded_plugins.append(plugin_name)
                logger.info(f"Loaded plugin: {plugin_name}")

        except (ImportError, SyntaxError) as e:
            logger.error(
                f"Failed to load plugin '{plugin_name}': {e}",
                exc_info=True
            )
            continue

        except Exception as e:
            logger.error(
                f"Error setting up plugin '{plugin_name}': {e}",
                exc_info=True
            )
            continue

    return loaded_plugins
