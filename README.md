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

### Plugin System Overview

The bot includes a plugin system that automatically discovers and loads Python modules from `app/plugins/`. This allows you to extend the bot with custom commands, event handlers, and behavior without modifying the core bot code.

**Key Features**:
- Automatic plugin discovery and loading at bot startup
- Graceful error handling (broken plugins won't crash the bot)
- Support for both simple function-based and class-based plugins
- Access to full discord.py API and bot instance

### Creating a Plugin

Plugins are Python modules placed in `app/plugins/` with a required `setup()` function.

#### Simple Function-Based Plugin

**File**: `app/plugins/hello_plugin.py`

```python
"""Simple hello world plugin."""

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger("app.plugins.hello")


async def setup(bot: commands.Bot) -> str:
    """
    Plugin setup function called by bot loader.

    Args:
        bot: The Discord bot instance

    Returns:
        Plugin name for logging (optional)
    """
    @bot.tree.command(name="hello", description="Say hello")
    async def hello_command(interaction: discord.Interaction):
        """Simple hello command."""
        await interaction.response.send_message(
            f"Hello, {interaction.user.mention}!",
            ephemeral=True
        )

    logger.info("Hello plugin loaded")
    return "hello_plugin"
```

#### Class-Based Plugin (Advanced)

For more structured plugins, use the `Plugin` base class:

**File**: `app/plugins/advanced_plugin.py`

```python
"""Advanced plugin using Plugin base class."""

from app.plugins import Plugin
import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger("app.plugins.advanced")


class AdvancedPlugin(Plugin):
    """Example of a structured plugin using the Plugin base class."""

    name = "advanced_plugin"
    description = "Demonstrates advanced plugin features"

    async def setup(self, bot: commands.Bot):
        """Initialize the plugin."""

        @bot.tree.command(name="stats", description="Show bot statistics")
        async def stats_command(interaction: discord.Interaction):
            """Show bot stats."""
            guild_count = len(bot.guilds)
            await interaction.response.send_message(
                f"I'm in {guild_count} servers!",
                ephemeral=True
            )

        logger.info(f"{self.name} initialized")


async def setup(bot: commands.Bot) -> str:
    """Setup function using Plugin class."""
    plugin = AdvancedPlugin()
    await plugin.setup(bot)
    return plugin.name
```

### Plugin Loading

**Automatic Loading**:
- Place your plugin file in `app/plugins/`
- Ensure it has a `.py` extension and a `setup()` function
- Plugin loads automatically on bot startup

**Disabled Plugins**:
- Files starting with underscore (`_example_plugin.py`) are ignored
- See `app/plugins/_example_plugin.py` for a comprehensive example
- Rename to enable (e.g., `example_plugin.py`)

**Plugin Discovery Rules**:
- Must be a `.py` file in `app/plugins/`
- Must NOT be `__init__.py`
- Must NOT start with underscore (`_`)
- Must have an async `setup(bot)` function

### Plugin Lifecycle

1. **Discovery**: Bot scans `app/plugins/` for valid plugin files
2. **Import**: Each plugin module is imported
3. **Setup**: Plugin's `setup()` function is called with bot instance
4. **Registration**: Plugin commands/handlers are registered with Discord
5. **Logging**: Success/failure logged for each plugin

### Example: Plugin with Parameters

```python
"""Plugin demonstrating command parameters."""

import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger("app.plugins.greet")


async def setup(bot: commands.Bot) -> str:
    """Setup greeting command with parameters."""

    @bot.tree.command(name="greet", description="Greet someone")
    @app_commands.describe(
        name="The person to greet",
        style="Greeting style"
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="Friendly", value="friendly"),
        app_commands.Choice(name="Formal", value="formal"),
        app_commands.Choice(name="Casual", value="casual")
    ])
    async def greet_command(
        interaction: discord.Interaction,
        name: str,
        style: str = "friendly"
    ):
        """Greet someone with different styles."""
        greetings = {
            "friendly": f"Hey there, {name}! How's it going?",
            "formal": f"Good day, {name}. I hope you are well.",
            "casual": f"Yo {name}, what's up?"
        }

        message = greetings.get(style, f"Hello, {name}!")
        await interaction.response.send_message(message)

    logger.info("Greet plugin loaded")
    return "greet_plugin"
```

### Plugin Best Practices

1. **Return plugin name**: Have `setup()` return a string for better logging
2. **Use structured logging**: Use `logging.getLogger("app.plugins.yourplugin")`
3. **Handle errors gracefully**: Wrap risky operations in try/except
4. **Document your plugin**: Add module docstrings and command descriptions
5. **Test before deploying**: Errors in `setup()` are logged but plugin won't load
6. **Avoid blocking operations**: Use async/await for I/O operations
7. **Defer long tasks**: Use `await interaction.response.defer()` for >3 second operations

### Example: Plugin with Error Handling

```python
"""Plugin with robust error handling."""

import discord
from discord.ext import commands
import logging
import aiohttp

logger = logging.getLogger("app.plugins.weather")


async def setup(bot: commands.Bot) -> str:
    """Setup weather command with error handling."""

    @bot.tree.command(name="weather", description="Get weather info")
    async def weather_command(interaction: discord.Interaction, city: str):
        """Fetch weather data with proper error handling."""
        try:
            # Defer response for longer operation
            await interaction.response.defer(ephemeral=True)

            # Simulated API call (replace with real API)
            async with aiohttp.ClientSession() as session:
                # Your API call here
                pass

            await interaction.followup.send(f"Weather for {city}: Sunny!")

        except aiohttp.ClientError as e:
            logger.error(f"Weather API error: {e}")
            await interaction.followup.send(
                "Failed to fetch weather data. Try again later.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error in weather command: {e}", exc_info=True)
            await interaction.followup.send(
                "An error occurred. Please try again.",
                ephemeral=True
            )

    logger.info("Weather plugin loaded")
    return "weather_plugin"
```

### Debugging Plugins

**Enable debug logging**:
```bash
# In .env file
LOG_LEVEL=DEBUG
```

**Check logs**:
```bash
# Docker
docker logs -f worldmind-bot | grep plugin

# Local
# Logs will show:
# INFO - Loading plugins...
# INFO - Loaded plugin: your_plugin_name
# ERROR - Failed to load plugin 'broken_plugin': <error details>
```

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not loading | Missing `setup()` function | Add async `setup(bot)` function |
| Import errors | Missing dependencies | Install required packages in `requirements.txt` |
| Syntax errors | Python syntax errors | Check logs for traceback, fix syntax |
| Commands not appearing | Plugin loaded but not synced | Restart bot, commands sync on startup |
| Permission denied | Missing bot permissions | Ensure bot has required permissions in server |

### Example Plugin Reference

See `app/plugins/_example_plugin.py` for a comprehensive example showing:
- Simple slash commands
- Commands with parameters
- Event handlers
- Both function-based and class-based approaches
- Proper documentation structure

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
│   │   ├── __init__.py          # Plugin base class and loading infrastructure
│   │   └── _example_plugin.py   # Example plugin (disabled by default)
│   └── utils/
│       ├── __init__.py
│       └── permissions.py  # Role-based access control per server
├── docker/
│   ├── Dockerfile          # Multi-stage build, non-root user, security hardened
│   └── docker-compose.yml  # Container orchestration with resource limits
├── config/
│   ├── .env.example        # Template for DISCORD_TOKEN, LOG_LEVEL, etc.
│   └── servers.json.example # Template for server-specific configs
├── tests/                  # pytest test suite with 90+ tests
│   ├── __init__.py
│   ├── test_bot.py
│   ├── test_config.py
│   ├── test_permissions.py
│   ├── test_image_commands.py
│   ├── test_error_handling.py
│   ├── test_shutdown.py
│   ├── test_logging_setup.py
│   └── test_plugins.py     # Plugin system tests
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
