"""
Role-based permission system for Discord bot commands.

This module provides permission checking functionality to ensure only users
with authorized roles can execute bot commands. Permission checks are performed
per-server based on the allowed_roles configuration.

Example:
    >>> from app.utils.permissions import check_permission
    >>> if check_permission(interaction, config):
    ...     # Execute command
    ...     pass
    ... else:
    ...     # Deny access
    ...     await interaction.response.send_message("Permission denied")
"""

import discord
import logging
from app.config import Config

logger = logging.getLogger("app.permissions")


def check_permission(interaction: discord.Interaction, config: Config) -> bool:
    """
    Check if user has permission to use commands on this server.

    Validates that the user has at least one role that matches the server's
    allowed_roles list. Role matching is case-sensitive and done by role name.

    Args:
        interaction: Discord interaction object containing user and guild info
        config: Bot configuration with server-specific allowed roles

    Returns:
        True if user has any allowed role, False otherwise

    Permission Denial Cases:
        - Server not found in config (safe default: deny)
        - User has no roles
        - User has no roles matching allowed_roles list

    Example:
        >>> interaction = discord.Interaction(...)
        >>> config = Config()
        >>> if check_permission(interaction, config):
        ...     # User authorized
        ...     execute_command()

    Note:
        Role matching is case-sensitive: "Admin" != "admin"
    """
    # Get server config
    server_id = str(interaction.guild_id)
    server_config = config.get_server_config(server_id)

    if server_config is None:
        logger.warning(f"Permission denied: Server {server_id} not in config")
        return False

    # Get user's role names
    user_roles = [role.name for role in interaction.user.roles]

    # Check if any user role is in allowed roles
    for role in user_roles:
        if role in server_config.allowed_roles:
            logger.debug(f"Permission granted: User {interaction.user.id} has role '{role}'")
            return True

    logger.warning(
        f"Permission denied: User {interaction.user.id} on server {server_id} "
        f"has roles {user_roles}, needs one of {server_config.allowed_roles}"
    )
    return False
