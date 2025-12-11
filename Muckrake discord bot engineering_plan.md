# Muckraker Discord Bot - Engineering Development Plan

## Project Overview

### Objective
Develop a containerized Discord bot that responds to slash commands by posting specific images, with role-based access control and multi-server support.

### Core Requirements
- **Commands**: `/tapsign` and `/heartbreaking` (extensible architecture for additional commands)
- **Access Control**: Role-based permissions per Discord server
- **Multi-Server Support**: Single bot instance serving multiple Discord servers
- **Image Hosting**: Images served from `heckatron.xyz` domain via Cloudflare
- **Deployment**: Docker container managed through Portainer on Ubuntu home server
- **Cost**: Minimal operational cost (free-tier services only)

### Technical Stack
- **Language**: Python 3.11+
- **Framework**: discord.py
- **Containerization**: Docker with Docker Compose
- **Configuration**: Environment variables with Docker secrets
- **Repository**: GitHub with main/develop branching
- **Deployment**: Portainer on Ubuntu server
- **Domain**: Cloudflare-managed heckatron.xyz

---

## Responsibility Split

### Server Admin (You) - Pre-Development Tasks
These tasks can be completed **before** developer starts work:
- GitHub repository setup and configuration
- Discord bot application creation and token generation
- Image hosting infrastructure setup
- Cloudflare configuration and testing
- Server environment preparation
- Configuration files creation

### Developer Tasks  
These tasks require the pre-development tasks to be completed:
- Python application development
- Docker containerization
- Testing and validation
- Documentation completion

### Server Admin (You) - Post-Development Tasks
These tasks require developer work to be completed:
- Production deployment via Portainer
- Final integration testing
- Production monitoring setup

---

# SERVER ADMIN TASKS (YOU)

## Pre-Development Phase: Infrastructure Setup
**Duration**: 2-3 hours  
**When**: Complete BEFORE developer starts  
**Dependencies**: None - can start immediately

### A1. GitHub Repository Setup
**Time**: 30 minutes

#### Tasks:
1. **Repository Already Created**
   - Repository exists at: `https://github.com/mgstegmaier/muckraker-bot`
   - Verify it has Python .gitignore
   - Update description if needed: "Discord bot for posting images with role-based permissions"

2. **Branch Configuration**
   - Create `develop` branch from `main`
   - Set up branch protection for `main`:
     - Require pull request reviews
     - Require status checks to pass
     - Require up-to-date branches

3. **Repository Settings**
   - Add developer as collaborator with "Write" permissions
   - Configure default branch to `develop` for active development

#### Deliverables:
- [ ] Repository URL: `https://github.com/mgstegmaier/muckraker-bot`
- [ ] Developer has access
- [ ] Branch protection configured

---

### A2. Discord Bot Application Setup
**Time**: 20 minutes

#### Tasks:
1. **Create Discord Application**
   - Go to https://discord.com/developers/applications
   - Click "New Application", name: "Muckraker Bot"
   - Navigate to "Bot" section, click "Add Bot"
   - **SAVE THE BOT TOKEN** (you'll need this for config)

2. **Bot Configuration**
   - Enable "Message Content Intent" under Privileged Gateway Intents
   - Set bot username and avatar if desired
   - Note: Keep token secure, never commit to GitHub

3. **Bot Permissions Setup**
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot` and `applications.commands`
   - Select bot permissions: 
     - `Send Messages`
     - `Use Slash Commands` 
     - `Attach Files`
     - `Embed Links`
   - **SAVE THE INVITE URL** for later server invitations

#### Deliverables:
- [ ] Discord bot token (keep secure)
- [ ] Bot invite URL
- [ ] Bot configured with proper permissions

---

### A3. Image Hosting Infrastructure
**Time**: 45 minutes

#### Tasks:
1. **Server Directory Setup**
   ```bash
   # On your Ubuntu server
   sudo mkdir -p /var/www/heckatron.xyz/images
   sudo chown $USER:$USER /var/www/heckatron.xyz/images
   chmod 755 /var/www/heckatron.xyz/images
   ```

2. **Upload Images**
   ```bash
   # Upload your images (replace with actual paths)
   cp /path/to/tapsign-image.png /var/www/heckatron.xyz/images/
   cp /path/to/heartbreaking-image.png /var/www/heckatron.xyz/images/
   
   # Set proper permissions
   chmod 644 /var/www/heckatron.xyz/images/*.png
   ```

3. **Nginx Configuration**
   Add to your nginx config file:
   ```nginx
   server {
       listen 443 ssl http2;
       server_name heckatron.xyz;
       
       # Your existing SSL config here
       
       location /images/ {
           alias /var/www/heckatron.xyz/images/;
           expires 1y;
           add_header Cache-Control "public, immutable";
           add_header Access-Control-Allow-Origin "*";
           add_header X-Content-Type-Options nosniff;
       }
   }
   ```

4. **Test Configuration**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

#### Deliverables:
- [ ] Images accessible at: `https://heckatron.xyz/images/tapsign-image.png`
- [ ] Images accessible at: `https://heckatron.xyz/images/heartbreaking-image.png`

---

### A4. Cloudflare Configuration
**Time**: 30 minutes

#### Tasks:
1. **DNS Verification**
   - Confirm A record: `heckatron.xyz` → `[your-server-ip]` (Proxied ✓)
   - Test DNS resolution: `nslookup heckatron.xyz`

2. **SSL/TLS Settings**
   - Set encryption mode: **"Full (strict)"**
   - Enable **"Always Use HTTPS"**

3. **Caching Configuration**
   - Go to **Rules** → **Page Rules**
   - Create rule: `heckatron.xyz/images/*`
   - Settings:
     - Cache Level: Cache Everything
     - Edge Cache TTL: 1 month
     - Browser Cache TTL: 1 month

4. **Security Settings**
   - **Security** → **WAF**: Ensure Discord isn't blocked
   - If needed, create allow rule:
     - Field: User Agent, Operator: contains, Value: Discord, Action: Allow

5. **Test Image Access**
   ```bash
   # Test direct access
   curl -I https://heckatron.xyz/images/tapsign-image.png
   
   # Test with Discord user agent
   curl -H "User-Agent: Mozilla/5.0 (compatible; Discordbot/2.0)" https://heckatron.xyz/images/tapsign-image.png
   ```

#### Deliverables:
- [ ] Images load properly via HTTPS
- [ ] Cloudflare caching active
- [ ] Discord user agent not blocked

---

### A5. Discord Server Setup
**Time**: 15 minutes

#### Tasks:
1. **Test Server Creation** (if you don't have one)
   - Create a private Discord server for testing
   - Set up roles: "Admin", "Tester" (or use existing roles)
   - **SAVE SERVER ID**: Right-click server → "Copy Server ID"

2. **Production Server Preparation**
   - Identify production Discord server
   - Note the role names that should have bot access
   - **SAVE SERVER ID**: Right-click server → "Copy Server ID"

3. **Server Configuration Planning**
   - Document which roles can use commands on each server
   - Plan any server-specific image sets (if different)

#### Deliverables:
- [ ] Test server ID
- [ ] Production server ID  
- [ ] List of allowed role names per server

---

### A6. Configuration Files Creation
**Time**: 30 minutes

#### Tasks:
1. **Environment Configuration**
   Create file: `config/.env.example`
   ```env
   # Discord Configuration
   DISCORD_TOKEN=your_bot_token_here
   
   # Application Settings
   LOG_LEVEL=INFO
   HEALTH_CHECK_PORT=8080
   
   # Image Hosting
   BASE_IMAGE_URL=https://heckatron.xyz/images
   ```

2. **Server Configuration**
   Create file: `config/servers.json.example`
   ```json
   {
     "servers": {
       "YOUR_TEST_SERVER_ID": {
         "name": "Test Server",
         "allowed_roles": ["Admin", "Tester"],
         "images": {
           "tapsign": {
             "url": "https://heckatron.xyz/images/tapsign-image.png",
             "title": "Tap Sign",
             "description": "Posts the tap sign image"
           },
           "heartbreaking": {
             "url": "https://heckatron.xyz/images/heartbreaking-image.png",
             "title": "Heartbreaking", 
             "description": "Posts the heartbreaking image"
           }
         }
       },
       "YOUR_PRODUCTION_SERVER_ID": {
         "name": "Production Server",
         "allowed_roles": ["Admin", "Moderator"],
         "images": {
           "tapsign": {
             "url": "https://heckatron.xyz/images/tapsign-image.png",
             "title": "Tap Sign",
             "description": "Posts the tap sign image"
           },
           "heartbreaking": {
             "url": "https://heckatron.xyz/images/heartbreaking-image.png",
             "title": "Heartbreaking",
             "description": "Posts the heartbreaking image"
           }
         }
       }
     }
   }
   ```

3. **Create Actual Configuration Files**
   - Copy `.env.example` to `.env` with real values
   - Copy `servers.json.example` to `servers.json` with real server IDs
   - **DO NOT COMMIT** the actual `.env` and `servers.json` files

4. **Commit Configuration Templates**
   ```bash
   git add config/.env.example config/servers.json.example
   git commit -m "Add configuration templates"
   git push origin develop
   ```

#### Deliverables:
- [ ] Configuration templates in repository
- [ ] Actual configuration files created locally (not committed)
- [ ] Real Discord token and server IDs configured

---

### A7. Server Environment Preparation  
**Time**: 20 minutes

#### Tasks:
1. **Docker Verification**
   ```bash
   docker --version
   docker-compose --version
   # Should show recent versions
   ```

2. **Portainer Preparation**
   - Verify Portainer is accessible
   - Note the network name you typically use for containers
   - Ensure you can create new stacks

3. **File Permissions Setup**
   ```bash
   # Create directory for bot deployment
   mkdir -p ~/docker-apps/muckraker-bot
   cd ~/docker-apps/muckraker-bot
   
   # This is where you'll place the actual config files later
   mkdir config
   chmod 700 config  # Secure permissions for sensitive config
   ```

#### Deliverables:
- [ ] Docker and Docker Compose working
- [ ] Portainer accessible
- [ ] Deployment directory prepared

---

## Pre-Development Validation Checklist
**Complete this before handing off to developer:**

### Infrastructure Ready:
- [ ] GitHub repository created and configured
- [ ] Discord bot application created, token secured
- [ ] Images accessible via `https://heckatron.xyz/images/[filename]`
- [ ] Cloudflare caching and security configured
- [ ] Test and production Discord servers identified
- [ ] Configuration files created with real values
- [ ] Server environment prepared for deployment

### Information for Developer:
- [ ] Repository URL: `https://github.com/mgstegmaier/muckraker-bot`
- [ ] Discord bot token (provide securely)
- [ ] Server IDs and role configurations
- [ ] Image URLs confirmed working
- [ ] Portainer access details

---

# DEVELOPER TASKS

## Development Phase Overview
**Dependencies**: All Server Admin pre-development tasks must be completed first  
**Duration**: 6-8 hours over 3-5 days  
**Branch Strategy**: Work on `develop` branch, PR to `main` when complete

---

## D1. Project Foundation & Structure
**Duration**: 1-2 hours  
**Dependencies**: Server Admin A1 (GitHub repo setup)

### Tasks:
1. **Clone Repository and Setup**
   ```bash
   git clone https://github.com/mgstegmaier/muckraker-bot.git
   cd muckraker-bot
   git checkout develop
   ```

2. **Create Project Structure**
   ```
   muckraker-bot/
   ├── app/
   │   ├── __init__.py
   │   ├── bot.py                 # Main bot application
   │   ├── config.py              # Configuration management
   │   ├── commands/
   │   │   ├── __init__.py
   │   │   └── image_commands.py  # Image command implementations
   │   └── utils/
   │       ├── __init__.py
   │       ├── permissions.py     # Role checking utilities
   │       └── validators.py      # Input validation
   ├── docker/
   │   ├── Dockerfile
   │   └── docker-compose.yml
   ├── docs/
   │   ├── deployment.md
   │   └── testing-checklist.md
   ├── requirements.txt
   └── .dockerignore
   ```

3. **Initialize Python Dependencies**
   Create `requirements.txt`:
   ```
   discord.py>=2.3.0
   python-dotenv>=1.0.0
   aiohttp>=3.8.0
   ```

4. **Create .dockerignore**
   ```
   .git
   .gitignore
   README.md
   .env
   config/servers.json
   docs/
   __pycache__/
   *.pyc
   .pytest_cache/
   ```

### Acceptance Criteria:
- [ ] Project structure created and committed to `develop`
- [ ] Dependencies defined in `requirements.txt`
- [ ] Docker configuration files stubbed out

---

## D2. Core Application Development
**Duration**: 3-4 hours  
**Dependencies**: D1 complete, Server Admin A2 & A6 (Discord setup & config files)

### Tasks:
1. **Configuration Management System** (`app/config.py`)
   - Load environment variables with validation
   - Parse server configuration JSON
   - Validate server IDs and image URLs
   - Error handling for missing/invalid config

2. **Permission System** (`app/utils/permissions.py`)
   - Role-based access control per server
   - Server-specific role checking
   - Permission denial handling
   - Input validation utilities

3. **Image Command System** (`app/commands/image_commands.py`)
   - Generic image posting framework  
   - Discord embed creation
   - Error handling for failed image loads
   - Extensible command registration

4. **Main Bot Application** (`app/bot.py`)
   - Bot initialization and Discord connection
   - Slash command registration per server
   - Event handlers (on_ready, error handling)
   - Health check endpoint for Docker
   - Graceful shutdown handling

5. **Multi-Server Support Integration**
   - Server-specific configuration loading
   - Command sync per configured server
   - Isolated permission schemes
   - Server validation on startup

### Acceptance Criteria:
- [ ] Bot connects to Discord successfully
- [ ] Configuration system loads server-specific settings
- [ ] Permission system validates roles correctly  
- [ ] Image commands create proper embeds
- [ ] Error handling provides user-friendly messages
- [ ] Health check endpoint responds
- [ ] Code follows security best practices

---

## D3. Docker Containerization
**Duration**: 2 hours  
**Dependencies**: D2 complete

### Tasks:
1. **Multi-stage Dockerfile** (`docker/Dockerfile`)
   - Use Python 3.11-slim base image
   - Multi-stage build for minimal image size
   - Non-root user implementation
   - Health check integration
   - Proper signal handling

2. **Docker Compose Configuration** (`docker/docker-compose.yml`)
   - Service definition with restart policies
   - Volume mounts for configuration files
   - Environment variable handling
   - Network isolation
   - Resource limits for home server
   - Health check configuration

3. **Container Security**
   - Run as non-root user
   - Read-only file system where possible
   - Minimal attack surface
   - Proper file permissions

### Acceptance Criteria:
- [ ] Docker image builds successfully
- [ ] Container runs with non-root user
- [ ] Health checks respond correctly
- [ ] Configuration files mount properly
- [ ] Container handles signals gracefully

---

## D4. Testing & Validation
**Duration**: 1-2 hours  
**Dependencies**: D3 complete, Server Admin A3-A5 (infrastructure setup)

### Tasks:
1. **Local Development Testing**
   - Test bot with provided configuration
   - Validate Discord connection
   - Test slash command registration
   - Verify image posting functionality
   - Test role-based permissions

2. **Container Testing**
   - Build and run container locally
   - Test health check endpoint
   - Verify configuration loading
   - Test container restart scenarios
   - Monitor resource usage

3. **Integration Testing**
   - Test with actual Discord servers (using provided test server)
   - Validate multi-server configuration
   - Test image loading via Cloudflare
   - Verify error handling scenarios

4. **Create Testing Documentation** (`docs/testing-checklist.md`)
   - Manual testing procedures
   - Validation checklists
   - Troubleshooting common issues

### Acceptance Criteria:
- [ ] Bot responds to commands in test environment
- [ ] Role permissions work correctly
- [ ] Images load and display in Discord
- [ ] Container maintains stability
- [ ] Testing documentation complete

---

## D5. Documentation & Handoff
**Duration**: 1 hour  
**Dependencies**: D4 complete

### Tasks:
1. **Deployment Documentation** (`docs/deployment.md`)
   - Portainer deployment steps
   - Configuration file setup
   - Environment variable reference
   - Troubleshooting guide

2. **Code Documentation**
   - Docstrings for all functions
   - README.md updates
   - Configuration examples
   - Adding new commands guide

3. **Repository Cleanup**
   - Final commit to `develop` branch
   - Create pull request to `main`
   - Tag release version
   - Clean up any development files

### Acceptance Criteria:
- [ ] Complete deployment documentation
- [ ] Code properly documented
- [ ] README updated with full instructions
- [ ] Repository ready for production deployment

---

# SERVER ADMIN TASKS (YOU) - POST-DEVELOPMENT

## Production Deployment Phase
**Duration**: 1-2 hours  
**Dependencies**: All developer tasks complete

### A8. Production Deployment
**Time**: 45 minutes

#### Tasks:
1. **Prepare Production Environment**
   ```bash
   cd ~/docker-apps/muckraker-bot
   git pull origin main
   
   # Copy your actual config files (not the examples)
   cp /path/to/your/.env config/.env
   cp /path/to/your/servers.json config/servers.json
   
   # Secure permissions
   chmod 600 config/.env config/servers.json
   ```

2. **Deploy via Portainer**
   - Open Portainer
   - Create new stack: "muckraker-bot"
   - Upload/paste the docker-compose.yml
   - Set environment variables if needed
   - Deploy stack

3. **Verify Deployment**
   - Check container logs in Portainer
   - Verify bot shows online in Discord
   - Test health check endpoint

#### Deliverables:
- [ ] Container running in Portainer
- [ ] Bot online in Discord
- [ ] Logs show successful startup

---

### A9. Discord Server Integration
**Time**: 30 minutes

#### Tasks:
1. **Bot Server Invitations**
   - Use saved invite URL to add bot to test server
   - Add bot to production server
   - Verify bot has proper permissions

2. **Slash Command Testing**
   - Test `/tapsign` command on test server
   - Test `/heartbreaking` command on test server
   - Verify role permissions work correctly
   - Test on production server with appropriate roles

3. **Final Validation**
   - Confirm images display correctly in Discord
   - Test error handling (try command without proper role)
   - Verify multi-server functionality

#### Deliverables:
- [ ] Bot integrated in both test and production servers
- [ ] All commands working correctly
- [ ] Role permissions validated

---

### A10. Monitoring Setup
**Time**: 15 minutes

#### Tasks:
1. **Portainer Monitoring**
   - Set up container restart policy
   - Configure log retention
   - Test restart functionality

2. **Health Monitoring**
   - Verify health check is working
   - Test container recovery after failure
   - Document any manual recovery procedures

#### Deliverables:
- [ ] Monitoring configured in Portainer
- [ ] Auto-restart working
- [ ] Recovery procedures documented

---

# DEPENDENCIES MATRIX

## Task Dependencies:
```
Server Admin Pre-Development:
A1 (GitHub) → A6 (Config Files)
A2 (Discord Setup) → A6 (Config Files)  
A3 (Image Hosting) → A4 (Cloudflare)
A4 (Cloudflare) → A6 (Config Files)
A5 (Discord Servers) → A6 (Config Files)
A7 (Server Prep) → [Independent]

Developer Tasks:
D1 → depends on A1
D2 → depends on D1 + A2 + A6
D3 → depends on D2
D4 → depends on D3 + A3 + A4 + A5
D5 → depends on D4

Server Admin Post-Development:
A8 → depends on D5 (all dev work complete)
A9 → depends on A8
A10 → depends on A9
```

## Optimal Workflow:
1. **Week 1**: Server Admin completes A1-A7 (all pre-development tasks)
2. **Week 2**: Developer works on D1-D5 while Server Admin focuses on other projects
3. **Week 2 End**: Server Admin completes A8-A10 (production deployment)

This approach minimizes back-and-forth and allows maximum parallel work.