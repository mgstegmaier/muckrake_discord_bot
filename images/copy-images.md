## How to copy images to the server 
  ```bash
scp images/* heckatron@192.168.50.100:/mnt/cargo/media/muckrake_bot/images/
```

## ssh to server
### CHOWN the config directory to match the PUID/PGID:
  ```bash
  sudo chown -R 1002:1004 /mnt/cargo/media/muckrake_bot/images/
  ```

## Add the command to config/servers.json

  ```bash
          "heartbreaking": {
            "url": "heartbreaking.jpg",
            "title": "Heartbreaking..."
          },
           "gavin": {
             "url": "gavin.jpg",
             "title": "Jump Scare!"
           }
  ```

### Rebuild the app and publish!
  ```bash
    cd /Users/heckatron/github_repos/muckrake_discord_bot && \
    docker build -f docker/Dockerfile -t mgstegmaier/discordbot.heck:latest . && \
    docker push mgstegmaier/discordbot.heck:latest
  ```