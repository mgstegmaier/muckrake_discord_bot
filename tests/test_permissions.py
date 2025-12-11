"""
Tests for role-based permission system.

This module tests the check_permission function to ensure:
- Users with matching roles are granted permission
- Users without matching roles are denied
- Servers not in config are denied by default
- Role matching is case-sensitive
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.config import Config, ServerConfig
from app.utils.permissions import check_permission


class TestCheckPermission:
    """Test suite for check_permission function."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Config object with test server configuration."""
        config = Mock(spec=Config)

        # Server with allowed roles
        server_config = ServerConfig(
            name="Test Server",
            allowed_roles=["Admin", "Moderator"],
            images={}
        )

        # Configure get_server_config to return our test config for "123456789"
        def get_server_config(server_id):
            if server_id == "123456789":
                return server_config
            return None

        config.get_server_config = Mock(side_effect=get_server_config)
        return config

    @pytest.fixture
    def mock_interaction(self):
        """Create a mock Discord interaction object."""
        interaction = Mock()
        interaction.guild_id = 123456789  # Integer, will be converted to string
        interaction.user = Mock()
        interaction.user.id = 987654321
        return interaction

    def test_user_with_matching_role_returns_true(self, mock_interaction, mock_config):
        """Test that user with an allowed role is granted permission."""
        # Create mock roles - user has "Admin" role
        admin_role = Mock()
        admin_role.name = "Admin"
        member_role = Mock()
        member_role.name = "Member"

        mock_interaction.user.roles = [member_role, admin_role]

        # User should be granted permission
        assert check_permission(mock_interaction, mock_config) is True

    def test_user_with_moderator_role_returns_true(self, mock_interaction, mock_config):
        """Test that user with Moderator role is granted permission."""
        # Create mock roles - user has "Moderator" role
        moderator_role = Mock()
        moderator_role.name = "Moderator"

        mock_interaction.user.roles = [moderator_role]

        # User should be granted permission
        assert check_permission(mock_interaction, mock_config) is True

    def test_user_without_matching_role_returns_false(self, mock_interaction, mock_config):
        """Test that user without any allowed role is denied permission."""
        # Create mock roles - user only has "Member" role (not in allowed_roles)
        member_role = Mock()
        member_role.name = "Member"

        mock_interaction.user.roles = [member_role]

        # User should be denied permission
        assert check_permission(mock_interaction, mock_config) is False

    def test_user_with_no_roles_returns_false(self, mock_interaction, mock_config):
        """Test that user with no roles is denied permission."""
        # User has no roles (empty list)
        mock_interaction.user.roles = []

        # User should be denied permission
        assert check_permission(mock_interaction, mock_config) is False

    def test_server_not_in_config_returns_false(self, mock_interaction, mock_config):
        """Test that requests from unconfigured servers are denied."""
        # Set guild_id to a server not in config
        mock_interaction.guild_id = 999999999

        # Create mock roles - even with Admin role, should be denied
        admin_role = Mock()
        admin_role.name = "Admin"
        mock_interaction.user.roles = [admin_role]

        # Should be denied because server is not in config
        assert check_permission(mock_interaction, mock_config) is False

    def test_role_matching_is_case_sensitive(self, mock_interaction, mock_config):
        """Test that role matching is case-sensitive."""
        # Create mock roles with different casing
        admin_lowercase = Mock()
        admin_lowercase.name = "admin"  # lowercase, should NOT match "Admin"

        mock_interaction.user.roles = [admin_lowercase]

        # Should be denied because "admin" != "Admin" (case-sensitive)
        assert check_permission(mock_interaction, mock_config) is False

    def test_multiple_roles_any_match_grants_permission(self, mock_interaction, mock_config):
        """Test that having ANY allowed role grants permission."""
        # Create multiple mock roles, one matches
        user_role = Mock()
        user_role.name = "User"
        moderator_role = Mock()
        moderator_role.name = "Moderator"
        member_role = Mock()
        member_role.name = "Member"

        mock_interaction.user.roles = [user_role, member_role, moderator_role]

        # Should be granted because Moderator is in allowed_roles
        assert check_permission(mock_interaction, mock_config) is True
