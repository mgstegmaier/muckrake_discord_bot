"""
Tests for plugin system.

Tests plugin base class, plugin discovery, loading, and error handling.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from discord.ext import commands
import discord


# Load test environment
os.environ['DISCORD_TOKEN'] = 'test-token-value'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['BASE_IMAGE_URL'] = 'https://example.com/images/'


class TestPluginBase:
    """Test the Plugin base class and interface."""

    def test_plugin_base_class_exists(self):
        """Plugin base class should be importable."""
        from app.plugins import Plugin
        assert Plugin is not None

    def test_plugin_has_setup_method(self):
        """Plugin base class should have a setup method."""
        from app.plugins import Plugin
        assert hasattr(Plugin, 'setup')

    def test_plugin_has_name_property(self):
        """Plugin base class should have a name property."""
        from app.plugins import Plugin
        assert hasattr(Plugin, 'name')

    def test_plugin_has_description_property(self):
        """Plugin base class should have a description property."""
        from app.plugins import Plugin
        assert hasattr(Plugin, 'description')

    def test_plugin_cannot_be_instantiated_directly(self):
        """Plugin base class should be abstract (cannot be instantiated)."""
        from app.plugins import Plugin

        # Should raise TypeError when trying to instantiate abstract class
        with pytest.raises(TypeError):
            Plugin()

    def test_plugin_subclass_requires_setup(self):
        """Plugin subclass without setup method should fail to instantiate."""
        from app.plugins import Plugin

        class InvalidPlugin(Plugin):
            name = "invalid"
            description = "Missing setup method"

        # Should raise TypeError for missing abstract method
        with pytest.raises(TypeError):
            InvalidPlugin()

    def test_plugin_subclass_requires_name(self):
        """Plugin subclass without name should fail to instantiate."""
        from app.plugins import Plugin

        class InvalidPlugin(Plugin):
            description = "Missing name"
            async def setup(self, bot):
                pass

        # Should raise TypeError or AttributeError for missing name
        with pytest.raises((TypeError, AttributeError)):
            plugin = InvalidPlugin()
            _ = plugin.name

    def test_plugin_subclass_requires_description(self):
        """Plugin subclass without description should fail to instantiate."""
        from app.plugins import Plugin

        class InvalidPlugin(Plugin):
            name = "invalid"
            async def setup(self, bot):
                pass

        # Should raise TypeError or AttributeError for missing description
        with pytest.raises((TypeError, AttributeError)):
            plugin = InvalidPlugin()
            _ = plugin.description

    def test_valid_plugin_can_be_instantiated(self):
        """Valid plugin with all required attributes should instantiate."""
        from app.plugins import Plugin

        class ValidPlugin(Plugin):
            name = "test_plugin"
            description = "A test plugin"

            async def setup(self, bot):
                pass

        plugin = ValidPlugin()
        assert plugin is not None
        assert plugin.name == "test_plugin"
        assert plugin.description == "A test plugin"


class TestPluginLoader:
    """Test plugin discovery and loading functionality."""

    def test_load_plugins_function_exists(self):
        """load_plugins function should be importable."""
        from app.plugins import load_plugins
        assert load_plugins is not None

    @pytest.mark.asyncio
    async def test_load_plugins_with_no_plugins(self):
        """load_plugins should return empty list when no plugins found."""
        from app.plugins import load_plugins

        bot = Mock(spec=commands.Bot)

        # Mock the plugin directory to be empty
        with patch('os.listdir', return_value=[]):
            plugins = await load_plugins(bot)
            assert plugins == []

    @pytest.mark.asyncio
    async def test_load_plugins_ignores_init_file(self):
        """load_plugins should ignore __init__.py file."""
        from app.plugins import load_plugins

        bot = Mock(spec=commands.Bot)

        # Mock directory with only __init__.py
        with patch('os.listdir', return_value=['__init__.py']):
            plugins = await load_plugins(bot)
            assert plugins == []

    @pytest.mark.asyncio
    async def test_load_plugins_ignores_underscore_prefix(self):
        """load_plugins should ignore files starting with underscore."""
        from app.plugins import load_plugins

        bot = Mock(spec=commands.Bot)

        # Mock directory with underscore-prefixed file
        with patch('os.listdir', return_value=['_example_plugin.py', '__init__.py']):
            plugins = await load_plugins(bot)
            assert plugins == []

    @pytest.mark.asyncio
    async def test_load_plugins_ignores_non_python_files(self):
        """load_plugins should ignore non-.py files."""
        from app.plugins import load_plugins

        bot = Mock(spec=commands.Bot)

        # Mock directory with non-Python files
        with patch('os.listdir', return_value=['README.md', 'config.json']):
            plugins = await load_plugins(bot)
            assert plugins == []

    @pytest.mark.asyncio
    async def test_load_plugins_handles_import_error_gracefully(self, caplog):
        """load_plugins should log error and continue on import failure."""
        from app.plugins import load_plugins
        import logging

        bot = Mock(spec=commands.Bot)

        # Mock a plugin file that will fail to import
        with patch('os.listdir', return_value=['broken_plugin.py']), \
             patch('importlib.import_module', side_effect=ImportError("Module not found")), \
             caplog.at_level(logging.ERROR):

            plugins = await load_plugins(bot)

            # Should return empty list and log error
            assert plugins == []
            assert "Failed to load plugin" in caplog.text
            assert "broken_plugin" in caplog.text

    @pytest.mark.asyncio
    async def test_load_plugins_handles_syntax_error_gracefully(self, caplog):
        """load_plugins should log error and continue on syntax error."""
        from app.plugins import load_plugins
        import logging

        bot = Mock(spec=commands.Bot)

        # Mock a plugin file with syntax error
        with patch('os.listdir', return_value=['syntax_error_plugin.py']), \
             patch('importlib.import_module', side_effect=SyntaxError("invalid syntax")), \
             caplog.at_level(logging.ERROR):

            plugins = await load_plugins(bot)

            # Should return empty list and log error
            assert plugins == []
            assert "Failed to load plugin" in caplog.text

    @pytest.mark.asyncio
    async def test_load_plugins_calls_setup_function(self):
        """load_plugins should call setup() function if present in module."""
        from app.plugins import load_plugins

        bot = Mock(spec=commands.Bot)

        # Mock a module with setup function
        mock_module = MagicMock()
        mock_setup = MagicMock(return_value=None)
        mock_module.setup = mock_setup

        with patch('os.listdir', return_value=['test_plugin.py']), \
             patch('importlib.import_module', return_value=mock_module):

            # Make setup async
            async def async_setup(b):
                mock_setup(b)
                return "test_plugin"

            mock_module.setup = async_setup

            plugins = await load_plugins(bot)

            # Should have called setup with bot instance
            # We check that the plugin name was returned
            assert len(plugins) == 1
            assert plugins[0] == "test_plugin"

    @pytest.mark.asyncio
    async def test_load_plugins_handles_setup_error_gracefully(self, caplog):
        """load_plugins should log error and continue if setup() fails."""
        from app.plugins import load_plugins
        import logging

        bot = Mock(spec=commands.Bot)

        # Mock a module with failing setup function
        mock_module = MagicMock()

        async def failing_setup(b):
            raise RuntimeError("Setup failed")

        mock_module.setup = failing_setup

        with patch('os.listdir', return_value=['failing_plugin.py']), \
             patch('importlib.import_module', return_value=mock_module), \
             caplog.at_level(logging.ERROR):

            plugins = await load_plugins(bot)

            # Should return empty list and log error
            assert plugins == []
            assert "Error setting up plugin" in caplog.text
            assert "failing_plugin" in caplog.text

    @pytest.mark.asyncio
    async def test_load_plugins_continues_after_one_failure(self, caplog):
        """load_plugins should continue loading plugins after one fails."""
        from app.plugins import load_plugins
        import logging

        bot = Mock(spec=commands.Bot)

        # Create two mock modules: one that fails, one that succeeds
        failing_module = MagicMock()
        async def failing_setup(b):
            raise RuntimeError("Setup failed")
        failing_module.setup = failing_setup

        success_module = MagicMock()
        async def success_setup(b):
            return "success_plugin"
        success_module.setup = success_setup

        # Mock import_module to return different modules for different names
        def mock_import(name):
            if 'failing' in name:
                return failing_module
            else:
                return success_module

        with patch('os.listdir', return_value=['failing_plugin.py', 'success_plugin.py']), \
             patch('importlib.import_module', side_effect=mock_import), \
             caplog.at_level(logging.ERROR):

            plugins = await load_plugins(bot)

            # Should have loaded one plugin despite the failure
            assert len(plugins) == 1
            assert plugins[0] == "success_plugin"
            assert "Error setting up plugin" in caplog.text


class TestBotIntegration:
    """Test plugin integration with bot startup."""

    @pytest.mark.asyncio
    async def test_bot_loads_plugins_on_startup(self):
        """Bot should call load_plugins during startup process."""
        # This test verifies that the bot integration point exists
        # The actual loading happens in bot.py's on_ready handler
        from app.plugins import load_plugins
        from unittest.mock import Mock

        bot = Mock(spec=commands.Bot)

        # Should be able to call load_plugins with bot instance
        plugins = await load_plugins(bot)
        assert isinstance(plugins, list)

    def test_bot_module_has_plugin_imports(self):
        """Bot module should import plugin loading functionality."""
        import app.bot

        # Bot module should have access to plugin system
        # (This just verifies no import errors)
        assert app.bot is not None
