# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Muckraker Bot is a containerized Discord bot that responds to slash commands by posting images with role-based access control and multi-server support.

**Tech Stack**: Python 3.11+, discord.py, Docker, Cloudflare-hosted images on heckatron.xyz

## Project Structure (Target)

```
muckraker-bot/
├── app/
│   ├── bot.py              # Main bot application, Discord connection, slash commands
│   ├── config.py           # Environment and server configuration loading
│   ├── commands/
│   │   └── image_commands.py   # Image posting with Discord embeds
│   └── utils/
│       ├── permissions.py  # Role-based access control per server
│       └── validators.py   # Input validation
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   ├── .env.example        # Template for DISCORD_TOKEN, LOG_LEVEL, etc.
│   └── servers.json.example # Template for server-specific configs
└── requirements.txt
```

## Build & Run Commands

```bash
# Local development
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.bot

# Docker build and run
docker build -f docker/Dockerfile -t muckraker-bot .
docker-compose -f docker/docker-compose.yml up

# Health check (when running)
curl http://localhost:8080/health
```

## Architecture Notes

- **Multi-server support**: Single bot instance serves multiple Discord servers with isolated configurations
- **Server configuration**: `config/servers.json` defines per-server settings including allowed roles and image URLs
- **Image hosting**: Images served from `https://heckatron.xyz/images/` via Cloudflare CDN
- **Commands**: `/tapsign` and `/heartbreaking` (extensible pattern for additional image commands)
- **Permissions**: Role-based access checked per server before command execution

## Configuration

Environment variables (`.env`):
- `DISCORD_TOKEN` - Bot authentication token
- `LOG_LEVEL` - Logging verbosity (default: INFO)
- `HEALTH_CHECK_PORT` - HTTP port for container health checks (default: 8080)
- `BASE_IMAGE_URL` - Base URL for image hosting

Server config (`servers.json`):
- Maps server IDs to allowed roles and image definitions
- Each server can have different role requirements and image sets

## Security Considerations

- Bot token must never be committed - use environment variables
- Container runs as non-root user
- Configuration files (`.env`, `servers.json`) are gitignored
- Input validation on all user-provided data
