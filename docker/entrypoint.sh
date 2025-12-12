#!/bin/bash
# Entrypoint script for Discord Bot
# Handles PUID/PGID user mapping similar to LinuxServer.io images

PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting with UID: $PUID, GID: $PGID"

# Create group if it doesn't exist
if ! getent group botgroup > /dev/null 2>&1; then
    groupadd -g "$PGID" botgroup
fi

# Create user if it doesn't exist, or modify existing user
if ! id -u botuser > /dev/null 2>&1; then
    useradd -u "$PUID" -g "$PGID" -d /app -s /bin/bash botuser
else
    usermod -u "$PUID" -g "$PGID" botuser
fi

# Fix ownership of app directory
chown -R botuser:botgroup /app

# Run the bot as the specified user
exec gosu botuser python -m app.bot
