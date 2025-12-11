# Worldmind Discord Bot

A containerized Discord bot that posts images via slash commands with role-based access control and multi-server support.

## Features

- **Slash Commands**: Modern Discord slash commands (`/tapsign`, `/heartbreaking`)
- **Multi-Server Support**: Single bot instance serves multiple Discord servers with isolated configurations
- **Role-Based Access Control**: Configurable allowed roles per server
- **Config-Driven Commands**: Add new image commands via `servers.json` without code changes
- **Plugin System**: Extend with code-based commands for advanced functionality
- **Docker Ready**: Production-ready containerization with multi-stage builds and non-root user
- **Graceful Shutdown**: Clean container stops with proper signal handling
- **Structured Logging**: JSON-formatted logs with configurable levels
- **Health Checks**: HTTP endpoint for container orchestration

## Prerequisites

- **Python 3.11+** (for local development)
- **Docker & Docker Compose** (for containerized deployment)
- **Discord Bot Token** - Get one from [Discord Developer Portal](https://discord.com/developers/applications)
- **Image Hosting** - HTTPS-accessible image URLs (e.g., Cloudflare CDN)

## Quick Start (Docker)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/worldmind-bot.git
   cd worldmind-bot
   ```

2. **Configure environment**:
   ```bash
   cp config/.env.example config/.env
   cp config/servers.json.example config/servers.json
   ```

3. **Edit `config/.env`**:
   ```bash
   DISCORD_TOKEN=your_actual_bot_token_here
   BASE_IMAGE_URL=https://heckatron.xyz/images/
   LOG_LEVEL=INFO
   ```

4. **Edit `config/servers.json`** with your Discord server IDs:
   ```json
   {
     "servers": {
       "YOUR_SERVER_ID_HERE": {
         "name": "My Server",
         "allowed_roles": ["Admin", "Moderator"],
         "images": {
           "tapsign": {
             "url": "tapsign.jpg",
             "title": "Tap Sign"
           }
         }
       }
     }
   }
   ```

5. **Build and run**:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

6. **Verify the bot is running**:
   ```bash
   docker logs -f worldmind-bot
   ```

You should see log output indicating successful connection to Discord.

## Local Development Setup

### 1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure environment:
```bash
cp config/.env.example config/.env
cp config/servers.json.example config/servers.json
# Edit both files with your actual values
```

### 4. Run the bot:
```bash
python -m app.bot
```

### 5. Run tests:
```bash
pytest tests/ -v
```

### 6. Run tests with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## Configuration Reference

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Discord bot authentication token from Developer Portal |
| `BASE_IMAGE_URL` | Yes | - | Base URL for image hosting (must use HTTPS) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `SERVERS_CONFIG_PATH` | No | `config/servers.json` | Path to server configuration file |

### Server Configuration (`servers.json`)

The `servers.json` file defines per-server settings including allowed roles and available image commands.

**Structure**:
```json
{
  "servers": {
    "SERVER_ID": {
      "name": "Server Name",
      "allowed_roles": ["Role1", "Role2"],
      "images": {
        "commandname": {
          "url": "image_filename.jpg",
          "title": "Display Title"
        }
      }
    }
  }
}
```

**Field Descriptions**:

- `SERVER_ID`: Discord server (guild) ID as a string (18-19 digits)
  - Get this by enabling Developer Mode in Discord, right-clicking your server, and selecting "Copy Server ID"
- `name`: Human-readable server name (for logging/debugging)
- `allowed_roles`: Array of role names that can use bot commands
  - Role names are case-sensitive and must match exactly
  - Users with any of these roles can execute commands
- `images`: Object mapping command names to image configurations
  - `commandname`: The slash command name (e.g., `tapsign` becomes `/tapsign`)
    - Must be lowercase, no spaces (Discord requirement)
  - `url`: Image filename or path relative to `BASE_IMAGE_URL`
  - `title`: Title shown in the Discord embed

**Example with multiple servers**:
```json
{
  "servers": {
    "123456789012345678": {
      "name": "Gaming Server",
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
    },
    "987654321098765432": {
      "name": "Community Server",
      "allowed_roles": ["Bot Manager"],
      "images": {
        "tapsign": {
          "url": "tapsign.jpg",
          "title": "Tap Sign"
        }
      }
    }
  }
}
```

## Adding New Image Commands

You can add new image commands **without writing any code** by editing `config/servers.json`.

### Step-by-Step Guide

1. **Upload your image** to your hosting service (e.g., `https://heckatron.xyz/images/newimage.jpg`)

2. **Edit `config/servers.json`** and add a new entry under the `images` object:
   ```json
   {
     "servers": {
       "YOUR_SERVER_ID": {
         "name": "Your Server",
         "allowed_roles": ["Admin"],
         "images": {
           "tapsign": {
             "url": "tapsign.jpg",
             "title": "Tap Sign"
           },
           "newcommand": {
             "url": "newimage.jpg",
             "title": "My New Image"
           }
         }
       }
     }
   }
   ```

3. **Restart the bot**:
   - **Docker**: `docker-compose -f docker/docker-compose.yml restart`
   - **Local**: Stop (Ctrl+C) and restart `python -m app.bot`

4. **Test the command** in Discord by typing `/newcommand`

**Notes**:
- Command names must be lowercase and alphanumeric (no spaces or special characters)
- Images must be accessible via HTTPS
- Commands are server-specific; add to each server config where you want them available
- Changes require a bot restart to take effect

## Plugin Development

For advanced functionality beyond simple image posting, you can create custom plugins.

### Plugin Interface

Plugins are Python modules placed in `app/plugins/` that extend the bot with custom commands and behavior.

**Basic Plugin Structure**:
```python
# app/plugins/my_plugin.py

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger("app.plugins.my_plugin")


class MyPlugin(commands.Cog):
    """Custom plugin for advanced functionality."""

    def __init__(self, bot: commands.Bot, config):
        self.bot = bot
        self.config = config
        logger.info("MyPlugin loaded")

    @app_commands.command(name="mycommand", description="My custom command")
    async def my_command(self, interaction: discord.Interaction):
        """Handle /mycommand slash command."""
        await interaction.response.send_message("Hello from my plugin!")


async def setup(bot: commands.Bot, config):
    """
    Plugin setup function called by the bot loader.

    Args:
        bot: The Discord bot instance
        config: Configuration object
    """
    await bot.add_cog(MyPlugin(bot, config))
    logger.info("MyPlugin setup complete")
```

### Plugin Loading

**Automatic Loading** (Not yet implemented):
- Plugins in `app/plugins/` with a `setup()` function will be auto-loaded at bot startup

**Manual Loading** (Current approach):
- Import and register plugins in `app/bot.py`:
  ```python
  from app.plugins.my_plugin import setup as my_plugin_setup

  # In create_bot_instance():
  await my_plugin_setup(bot, config)
  ```

### Plugin Best Practices

1. **Use the Cog pattern**: Organize related commands in a `commands.Cog` subclass
2. **Leverage config**: Access `self.config` for server-specific settings
3. **Check permissions**: Use `app.utils.permissions.check_permission()` for role-based access
4. **Log activity**: Use structured logging with `logging.getLogger()`
5. **Handle errors**: Wrap command logic in try/except and send user-friendly error messages
6. **Defer long operations**: Use `await interaction.response.defer()` for commands taking >3 seconds

### Example: Role-Protected Plugin Command

```python
from app.utils.permissions import check_permission

@app_commands.command(name="admin_only", description="Admin-only command")
async def admin_command(self, interaction: discord.Interaction):
    """Command that requires specific roles."""
    # Check if user has permission
    has_permission = await check_permission(
        interaction,
        self.config,
        interaction.guild_id
    )

    if not has_permission:
        await interaction.response.send_message(
            "You don't have permission to use this command.",
            ephemeral=True
        )
        return

    # Execute privileged operation
    await interaction.response.send_message("Admin operation complete!")
```

## Project Structure

```
worldmind-bot/
├── app/
│   ├── __init__.py
│   ├── bot.py              # Main bot application, Discord connection, slash commands
│   ├── config.py           # Environment and server configuration loading
│   ├── logging_setup.py    # Structured JSON logging configuration
│   ├── commands/
│   │   ├── __init__.py
│   │   └── image_commands.py   # Dynamic slash command registration, image posting
│   ├── plugins/
│   │   └── __init__.py     # Plugin loading infrastructure (extensible)
│   └── utils/
│       ├── __init__.py
│       └── permissions.py  # Role-based access control per server
├── docker/
│   ├── Dockerfile          # Multi-stage build, non-root user, security hardened
│   └── docker-compose.yml  # Container orchestration with resource limits
├── config/
│   ├── .env.example        # Template for DISCORD_TOKEN, LOG_LEVEL, etc.
│   └── servers.json.example # Template for server-specific configs
├── tests/                  # pytest test suite with 70+ tests
│   ├── __init__.py
│   ├── test_bot.py
│   ├── test_config.py
│   ├── test_permissions.py
│   ├── test_image_commands.py
│   ├── test_error_handling.py
│   ├── test_shutdown.py
│   └── test_logging_setup.py
├── images/                 # Source images for hosting
│   ├── tapsign.jpg
│   └── heartbreaking.jpg
├── requirements.txt        # Python dependencies
├── pytest.ini              # Test configuration
├── .gitignore
└── README.md
```

## Docker Deployment Details

### Building the Image

```bash
docker build -f docker/Dockerfile -t worldmind-bot .
```

### Running with Docker Compose

```bash
# Start in background
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker logs -f worldmind-bot

# Stop the bot
docker-compose -f docker/docker-compose.yml down
```

### Environment Variables in Docker

The `docker-compose.yml` file automatically loads `config/.env`. You can also pass environment variables directly:

```yaml
services:
  worldmind-bot:
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - LOG_LEVEL=DEBUG
```

### Security Features

- **Non-root user**: Container runs as UID 1000 (`botuser`)
- **Multi-stage build**: Minimal runtime image without build tools
- **Read-only config**: Configuration mounted as read-only volume
- **Resource limits**: Memory limits prevent resource exhaustion
- **No exposed ports**: Bot only connects outbound to Discord API

## Troubleshooting

### Bot doesn't connect to Discord

**Check logs**:
```bash
docker logs worldmind-bot
# or for local:
python -m app.bot
```

**Common issues**:
- Invalid `DISCORD_TOKEN` - verify token in Discord Developer Portal
- Bot not invited to server - use OAuth2 URL generator with `bot` and `applications.commands` scopes
- Missing intents - ensure "Server Members Intent" is enabled if using member-based features

### Commands don't appear in Discord

**Check**:
1. Bot has `applications.commands` scope when invited
2. `servers.json` contains your server ID (not server name)
3. Bot has restarted after config changes
4. Check logs for "Synced X commands" message

**Force command sync**:
Commands sync automatically on bot startup. If needed, restart the bot.

### Permission denied errors

**Check**:
1. User has one of the `allowed_roles` in `servers.json`
2. Role names match exactly (case-sensitive)
3. User has the role on that specific server (roles are server-specific)

**Debug**:
Set `LOG_LEVEL=DEBUG` to see permission check details in logs.

### Image doesn't load in Discord embed

**Check**:
1. Image URL is publicly accessible via HTTPS
2. `BASE_IMAGE_URL` + `image.url` forms a valid URL
3. Image file exists at that URL
4. Image is a supported format (JPG, PNG, GIF, WebP)

**Test URL**:
```bash
curl -I https://heckatron.xyz/images/tapsign.jpg
# Should return 200 OK
```

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_permissions.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Stop on first failure
pytest tests/ -x
```

### Code Style

This project follows:
- PEP 8 for Python code style
- Type hints on public functions
- Docstrings for modules, classes, and public methods
- Structured logging with context

### Contributing

1. Create a feature branch: `git checkout -b feature/new-feature`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/`
4. Update documentation as needed
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Containerized for deployment on Docker/Portainer
- Images hosted via Cloudflare CDN
