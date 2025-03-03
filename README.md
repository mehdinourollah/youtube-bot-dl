# 🎥 Universal Video Grabber Bot

> A sleek Telegram bot that fetches videos from your favorite social platforms with style.

## ✨ Features

- 🚀 Lightning-fast video downloads
- 🎯 Supports multiple platforms:
  - Twitter/X
  - YouTube
  - Instagram
  - TikTok
- 🔄 Automatic format selection
- 📱 Direct delivery to Telegram
- 🛡️ Size limit protection (50MB)

## 🛠️ Tech Stack

- Python 3.12
- python-telegram-bot
- yt-dlp
- Docker
- GitHub Actions

## 🚀 Deployment

The bot automatically deploys to your VPS via GitHub Actions when you push to the main branch.

### 🔑 Required Secrets

```bash
TELEGRAM_TOKEN      # Your Telegram Bot Token
DOCKER_USERNAME     # Docker Hub Username
DOCKER_TOKEN        # Docker Hub Access Token
VPS_HOST           # Your VPS IP/Domain
VPS_USERNAME       # VPS SSH Username
VPS_SSH_KEY        # VPS SSH Private Key
```

## 🏃‍♂️ Local Development

1. Clone the repository
2. Build the Docker image:
   ```bash
   docker build -t video-grabber-bot .
   ```
3. Run the container:
   ```bash
   docker run -e TELEGRAM_TOKEN=your_token video-grabber-bot
   ```

## 📝 Usage

1. Start a chat with the bot
2. Send a video URL from any supported platform
3. Wait for your video to arrive!

## ⚠️ Limitations

- Maximum video size: 50MB
- Supported platforms: Twitter/X, YouTube, Instagram, TikTok
- Some platform restrictions may apply

## 📜 License

MIT License - Feel free to use and modify!