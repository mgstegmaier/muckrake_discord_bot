"""
Configuration loading system for Worldmind Discord Bot.

This module loads environment variables and parses the servers.json configuration
file with comprehensive validation to ensure all required settings are present
and properly formatted.

Environment Variables:
    DISCORD_TOKEN: Bot authentication token (required)
    LOG_LEVEL: Logging verbosity (default: INFO)
    BASE_IMAGE_URL: Base URL for image hosting (required, must be HTTPS)
    SERVERS_CONFIG_PATH: Path to servers.json file (default: config/servers.json)

Example:
    >>> from app.config import Config
    >>> config = Config()
    >>> print(config.discord_token)
    >>> server_config = config.get_server_config("123456789")
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any
from urllib.parse import urlparse


class ConfigError(Exception):
    """
    Exception raised for configuration errors.

    This exception is raised when required environment variables are missing,
    configuration files are invalid, or validation fails.
    """
    pass


@dataclass
class ServerConfig:
    """
    Configuration for a single Discord server.

    Attributes:
        name: Human-readable server name
        allowed_roles: List of role names permitted to use bot commands
        images: Dictionary mapping command names to image definitions
            Each image definition contains 'url' and 'title' keys
    """
    name: str
    allowed_roles: list[str]
    images: Dict[str, Dict[str, str]]


class Config:
    """
    Main configuration class for the Discord bot.

    Loads and validates environment variables and servers.json configuration.
    Provides typed access to all bot settings.

    Attributes:
        discord_token: Discord bot authentication token
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        base_image_url: Base URL for image hosting (HTTPS only)
        servers: Dictionary mapping server IDs to ServerConfig objects

    Raises:
        ConfigError: If required configuration is missing or invalid

    Example:
        >>> config = Config()
        >>> config.discord_token
        'your-bot-token'
        >>> server = config.get_server_config("123456789")
        >>> server.allowed_roles
        ['Admin', 'Moderator']
    """

    def __init__(self):
        """
        Initialize configuration by loading environment variables and servers.json.

        Raises:
            ConfigError: If any required configuration is missing or invalid
        """
        self._load_environment()
        self._load_servers_config()

    def _load_environment(self) -> None:
        """
        Load and validate environment variables.

        Raises:
            ConfigError: If required variables are missing or invalid
        """
        # DISCORD_TOKEN is required
        self.discord_token = os.getenv('DISCORD_TOKEN')
        if not self.discord_token:
            raise ConfigError(
                "DISCORD_TOKEN environment variable is required. "
                "Please set it to your Discord bot token."
            )

        # LOG_LEVEL defaults to INFO
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # BASE_IMAGE_URL is required and must be HTTPS
        self.base_image_url = os.getenv('BASE_IMAGE_URL')
        if not self.base_image_url:
            raise ConfigError(
                "BASE_IMAGE_URL environment variable is required. "
                "Please set it to your image hosting base URL (e.g., https://heckatron.xyz/images/)."
            )

        self._validate_url_format(self.base_image_url)

    def _validate_url_format(self, url: str) -> None:
        """
        Validate that a URL is properly formatted and uses HTTPS.

        Args:
            url: The URL to validate

        Raises:
            ConfigError: If URL format is invalid or doesn't use HTTPS
        """
        try:
            parsed = urlparse(url)

            # Must have scheme and netloc for valid URL
            if not parsed.scheme or not parsed.netloc:
                raise ConfigError(
                    f"BASE_IMAGE_URL has invalid URL format: {url}. "
                    "Expected format: https://example.com/path/"
                )

            # Must use HTTPS for security
            if parsed.scheme != 'https':
                raise ConfigError(
                    f"BASE_IMAGE_URL must use HTTPS protocol, not {parsed.scheme}. "
                    f"Got: {url}"
                )
        except ValueError as e:
            raise ConfigError(
                f"BASE_IMAGE_URL has invalid URL format: {url}. Error: {e}"
            )

    def _load_servers_config(self) -> None:
        """
        Load and validate servers.json configuration file.

        Raises:
            ConfigError: If file is missing, malformed, or contains invalid data
        """
        # Default to config/servers.json, but allow override
        config_path = os.getenv(
            'SERVERS_CONFIG_PATH',
            'config/servers.json'
        )

        # Check file exists
        if not os.path.exists(config_path):
            raise ConfigError(
                f"servers.json configuration file not found at: {config_path}. "
                "Please create this file with your server configurations."
            )

        # Parse JSON
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Failed to parse servers.json: Invalid JSON format. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
            )
        except Exception as e:
            raise ConfigError(
                f"Failed to read servers.json: {e}"
            )

        # Validate structure
        if 'servers' not in data:
            raise ConfigError(
                "servers.json must contain a 'servers' key at the root level. "
                "Expected format: {\"servers\": {\"server_id\": {...}}}"
            )

        # Parse and validate each server config
        self.servers: Dict[str, ServerConfig] = {}
        for server_id, server_data in data['servers'].items():
            self._validate_server_config(server_id, server_data)
            self.servers[server_id] = ServerConfig(
                name=server_data['name'],
                allowed_roles=server_data['allowed_roles'],
                images=server_data['images']
            )

    def _validate_server_config(self, server_id: str, config: Dict[str, Any]) -> None:
        """
        Validate a single server configuration.

        Args:
            server_id: The Discord server ID
            config: The server configuration dictionary

        Raises:
            ConfigError: If required fields are missing or invalid
        """
        # Check required fields
        if 'allowed_roles' not in config:
            raise ConfigError(
                f"Server {server_id} is missing required field 'allowed_roles'. "
                "This field must contain a list of role names."
            )

        if 'images' not in config:
            raise ConfigError(
                f"Server {server_id} is missing required field 'images'. "
                "This field must contain a dictionary of image definitions."
            )

        # Validate allowed_roles is a list
        if not isinstance(config['allowed_roles'], list):
            raise ConfigError(
                f"Server {server_id}: 'allowed_roles' must be a list of role names."
            )

        # Validate images is a dict
        if not isinstance(config['images'], dict):
            raise ConfigError(
                f"Server {server_id}: 'images' must be a dictionary."
            )

        # Validate each image definition
        for image_name, image_data in config['images'].items():
            if not isinstance(image_data, dict):
                raise ConfigError(
                    f"Server {server_id}, image '{image_name}': "
                    "Image definition must be a dictionary with 'url' and 'title' keys."
                )

            if 'url' not in image_data:
                raise ConfigError(
                    f"Server {server_id}, image '{image_name}': "
                    "Missing required 'url' field."
                )

            if 'title' not in image_data:
                raise ConfigError(
                    f"Server {server_id}, image '{image_name}': "
                    "Missing required 'title' field."
                )

    def get_server_config(self, server_id: str) -> Optional[ServerConfig]:
        """
        Get configuration for a specific Discord server.

        Args:
            server_id: The Discord server ID as a string

        Returns:
            ServerConfig object if server exists, None otherwise

        Example:
            >>> config = Config()
            >>> server = config.get_server_config("123456789")
            >>> if server:
            ...     print(server.allowed_roles)
        """
        return self.servers.get(server_id)
