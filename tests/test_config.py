"""
Tests for configuration loading system.

Following TDD workflow - these tests define the expected behavior
of the Config class before implementation.
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


# Import will fail initially - this is expected in RED phase
from app.config import Config, ConfigError, ServerConfig


class TestConfigInitialization:
    """Test basic Config class initialization."""

    def test_config_loads_with_valid_environment(self, valid_config_setup):
        """Config should initialize successfully with valid env vars and servers.json."""
        config = Config()

        assert config.discord_token is not None
        assert config.log_level == "INFO"
        assert config.base_image_url == "https://heckatron.xyz/images/"
        assert len(config.servers) > 0

    def test_config_provides_typed_access(self, valid_config_setup):
        """Config should provide type-safe access to settings."""
        config = Config()

        # Check types
        assert isinstance(config.discord_token, str)
        assert isinstance(config.log_level, str)
        assert isinstance(config.base_image_url, str)
        assert isinstance(config.servers, dict)


class TestEnvironmentValidation:
    """Test environment variable validation."""

    def test_missing_discord_token_raises_error(self, servers_json_file):
        """Missing DISCORD_TOKEN should raise ConfigError with helpful message."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
            os.environ['SERVERS_CONFIG_PATH'] = servers_json_file

            with pytest.raises(ConfigError) as exc_info:
                Config()

            assert "DISCORD_TOKEN" in str(exc_info.value)
            assert "required" in str(exc_info.value).lower()

    def test_missing_base_image_url_raises_error(self, servers_json_file):
        """Missing BASE_IMAGE_URL should raise ConfigError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ['DISCORD_TOKEN'] = 'test_token_123'
            os.environ['SERVERS_CONFIG_PATH'] = servers_json_file

            with pytest.raises(ConfigError) as exc_info:
                Config()

            assert "BASE_IMAGE_URL" in str(exc_info.value)

    def test_log_level_defaults_to_info(self, valid_config_setup):
        """LOG_LEVEL should default to INFO when not specified."""
        with patch.dict(os.environ, os.environ.copy()):
            if 'LOG_LEVEL' in os.environ:
                del os.environ['LOG_LEVEL']

            config = Config()
            assert config.log_level == "INFO"

    def test_custom_log_level_respected(self, valid_config_setup):
        """Custom LOG_LEVEL should be used when provided."""
        with patch.dict(os.environ, os.environ.copy()):
            os.environ['LOG_LEVEL'] = 'DEBUG'

            config = Config()
            assert config.log_level == "DEBUG"


class TestURLValidation:
    """Test URL format validation."""

    def test_invalid_url_format_raises_error(self, servers_json_file):
        """BASE_IMAGE_URL with invalid format should raise ConfigError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ['DISCORD_TOKEN'] = 'test_token_123'
            os.environ['BASE_IMAGE_URL'] = 'not-a-valid-url'
            os.environ['SERVERS_CONFIG_PATH'] = servers_json_file

            with pytest.raises(ConfigError) as exc_info:
                Config()

            assert "URL" in str(exc_info.value)
            assert "format" in str(exc_info.value).lower()

    def test_url_must_use_https(self, servers_json_file):
        """BASE_IMAGE_URL must use https protocol."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ['DISCORD_TOKEN'] = 'test_token_123'
            os.environ['BASE_IMAGE_URL'] = 'http://heckatron.xyz/images/'
            os.environ['SERVERS_CONFIG_PATH'] = servers_json_file

            with pytest.raises(ConfigError) as exc_info:
                Config()

            assert "https" in str(exc_info.value).lower()


class TestServersJsonParsing:
    """Test servers.json file parsing and validation."""

    def test_missing_servers_json_raises_error(self):
        """Missing servers.json file should raise ConfigError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ['DISCORD_TOKEN'] = 'test_token_123'
            os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
            os.environ['SERVERS_CONFIG_PATH'] = '/nonexistent/servers.json'

            with pytest.raises(ConfigError) as exc_info:
                Config()

            assert "servers.json" in str(exc_info.value).lower()

    def test_invalid_json_raises_error(self):
        """Malformed JSON should raise ConfigError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_path = f.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                os.environ['DISCORD_TOKEN'] = 'test_token_123'
                os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
                os.environ['SERVERS_CONFIG_PATH'] = temp_path

                with pytest.raises(ConfigError) as exc_info:
                    Config()

                assert "JSON" in str(exc_info.value) or "parse" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_missing_servers_key_raises_error(self):
        """servers.json without 'servers' key should raise ConfigError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"wrong_key": {}}, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                os.environ['DISCORD_TOKEN'] = 'test_token_123'
                os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
                os.environ['SERVERS_CONFIG_PATH'] = temp_path

                with pytest.raises(ConfigError) as exc_info:
                    Config()

                assert "servers" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_server_missing_allowed_roles_raises_error(self):
        """Server config without allowed_roles should raise ConfigError."""
        config_data = {
            "servers": {
                "123456789": {
                    "name": "Test Server",
                    "images": {
                        "tapsign": {
                            "url": "tapsign.jpg",
                            "title": "Tap Sign"
                        }
                    }
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                os.environ['DISCORD_TOKEN'] = 'test_token_123'
                os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
                os.environ['SERVERS_CONFIG_PATH'] = temp_path

                with pytest.raises(ConfigError) as exc_info:
                    Config()

                assert "allowed_roles" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_server_missing_images_raises_error(self):
        """Server config without images should raise ConfigError."""
        config_data = {
            "servers": {
                "123456789": {
                    "name": "Test Server",
                    "allowed_roles": ["Admin"]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                os.environ['DISCORD_TOKEN'] = 'test_token_123'
                os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
                os.environ['SERVERS_CONFIG_PATH'] = temp_path

                with pytest.raises(ConfigError) as exc_info:
                    Config()

                assert "images" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)


class TestServerConfigAccess:
    """Test ServerConfig access methods."""

    def test_get_server_config_returns_config(self, valid_config_setup):
        """get_server_config should return ServerConfig for valid server ID."""
        config = Config()
        server_config = config.get_server_config("123456789")

        assert server_config is not None
        assert isinstance(server_config, ServerConfig)
        assert server_config.name == "Test Server"
        assert "Admin" in server_config.allowed_roles

    def test_get_server_config_returns_none_for_unknown_server(self, valid_config_setup):
        """get_server_config should return None for unknown server ID."""
        config = Config()
        server_config = config.get_server_config("999999999")

        assert server_config is None

    def test_server_config_provides_image_access(self, valid_config_setup):
        """ServerConfig should provide access to image definitions."""
        config = Config()
        server_config = config.get_server_config("123456789")

        assert "tapsign" in server_config.images
        assert server_config.images["tapsign"]["url"] == "tapsign.jpg"
        assert server_config.images["tapsign"]["title"] == "Tap Sign"


# Pytest fixtures

@pytest.fixture
def servers_json_file():
    """Create a valid servers.json file for testing."""
    config_data = {
        "servers": {
            "123456789": {
                "name": "Test Server",
                "allowed_roles": ["Admin", "Moderator"],
                "images": {
                    "tapsign": {
                        "url": "tapsign.jpg",
                        "title": "Tap Sign"
                    },
                    "heartbreaking": {
                        "url": "heartbreaking.jpg",
                        "title": "Heartbreaking"
                    }
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def valid_config_setup(servers_json_file):
    """Set up valid environment for Config initialization."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ['DISCORD_TOKEN'] = 'test_token_abc123'
        os.environ['BASE_IMAGE_URL'] = 'https://heckatron.xyz/images/'
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['SERVERS_CONFIG_PATH'] = servers_json_file
        yield
