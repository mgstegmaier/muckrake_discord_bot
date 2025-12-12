# Adding New Image Commands

This guide walks through the complete process of adding a new slash command to the Muckraker Bot.

## Overview

Adding a new command requires:
1. Upload the image to the server
2. Add the command to `servers.json` (local)
3. Copy `servers.json` to the server
4. Restart the container

**Note:** The Docker image does NOT contain the config - it's mounted as a volume. You don't need to rebuild the image to add new commands.

---

## Step 1: Add Image to Server

Copy your image file to the server's image directory:

```bash
scp images/yourimage.jpg heckatron@192.168.50.100:/mnt/cargo/media/muckrake_bot/images/
```

Verify it uploaded:
```bash
ssh heckatron@192.168.50.100 "ls /mnt/cargo/media/muckrake_bot/images/"
```

---

## Step 2: Update servers.json (Local)

Edit `config/servers.json` and add the new command to each server's `images` section:

```json
{
  "servers": {
    "760964123206615082": {
      "name": "The Muckraker Podcast Discord Server",
      "allowed_roles": ["Administrators", "Moderators", "All Access Muckraker"],
      "images": {
        "tapsign": {
          "url": "tapsign.jpg",
          "title": "Don't Make Me Tap The Sign..."
        },
        "heartbreaking": {
          "url": "heartbreaking.jpg",
          "title": "Heartbreaking..."
        },
        "yournewcommand": {
          "url": "yourimage.jpg",
          "title": "Your Title Here"
        }
      }
    }
  }
}
```

**Important:**
- The key (`yournewcommand`) becomes the slash command name (`/yournewcommand`)
- `url` is just the filename (not the full path)
- `title` appears in the Discord embed above the image
- Add the command to ALL servers that should have access

---

## Step 3: Copy servers.json to Server

```bash
scp config/servers.json heckatron@192.168.50.100:/mnt/nvme2TB/docker/discordbot.heck/config/
```

If you get permission denied, fix ownership first (one-time setup):
```bash
ssh heckatron@192.168.50.100 "sudo chown -R heckatron:1004 /mnt/nvme2TB/docker/discordbot.heck/config/ && sudo chmod 775 /mnt/nvme2TB/docker/discordbot.heck/config/"
```

---

## Step 4: Restart Container and Verify

```bash
ssh heckatron@192.168.50.100 "docker restart discordbot.heck && sleep 2 && docker logs discordbot.heck 2>&1 | grep Registered | tail -2"
```

You should see:
```
Registered 3 commands for server The Muckraker Podcast Discord Server (760964123206615082)
Registered 3 commands for server Heck (485595571336249367)
```

The number should match how many images you have configured.

---

## Quick Reference (All-in-One)

Once permissions are set up, adding a new command is just:

```bash
# 1. Copy image
scp images/newimage.jpg heckatron@192.168.50.100:/mnt/cargo/media/muckrake_bot/images/

# 2. Edit config/servers.json locally (add the new command entry)

# 3. Copy config and restart
scp config/servers.json heckatron@192.168.50.100:/mnt/nvme2TB/docker/discordbot.heck/config/ && \
ssh heckatron@192.168.50.100 "docker restart discordbot.heck"
```

---

## When to Rebuild the Docker Image

You only need to rebuild if you change **code** (Python files). Config changes don't require a rebuild.

```bash
cd /Users/heckatron/github_repos/muckrake_discord_bot && \
docker buildx build --platform linux/amd64 --provenance=false --sbom=false -f docker/Dockerfile -t mgstegmaier/discordbot.heck:latest --push .
```

Then pull and restart on server:
```bash
ssh heckatron@192.168.50.100 "docker pull mgstegmaier/discordbot.heck:latest && docker restart discordbot.heck"
```

---

## Troubleshooting

**Command not appearing in Discord:**
- Check logs: `ssh heckatron@192.168.50.100 "docker logs discordbot.heck 2>&1 | tail -20"`
- Verify servers.json syntax is valid JSON
- Ensure the server ID in config matches your Discord server

**Image not loading in embed:**
- Verify image exists: `ssh heckatron@192.168.50.100 "ls /mnt/cargo/media/muckrake_bot/images/"`
- Check the filename in servers.json matches exactly (case-sensitive)
- Test the URL directly: `https://images.heckatron.xyz/yourimage.jpg`
