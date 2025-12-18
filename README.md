# YouTube Downloader Telegram Bot

A reliable Telegram bot that downloads YouTube videos and sends them back to the user. Built with Python, `aiogram`, and `yt-dlp`.

**Features:**
-   **Massive File Support**: Supports up to 2GB per file (via Local API) and up to 4GB+ via auto-splitting.
-   **Auto-Cleanup**: Automatically cleans disk space on startup.
-   **Auto-Deploy**: Built-in GitHub Actions CI/CD.

## Prerequisites

1.  **Telegram Bot Token**: Get one from [@BotFather](https://t.me/BotFather).
2.  **Telegram API ID & Hash**: Get these from [my.telegram.org](https://my.telegram.org/apps) (Required for 2GB+ support).
3.  **Docker** (Recommended) OR **Python 3.11+** installed.

## Quick Start (Docker Compose) - Recommended

1.  Create a file named `.env` in this directory:
    ```env
    BOT_TOKEN=your_token_here
    TELEGRAM_API_ID=123456
    TELEGRAM_API_HASH=abcdef123456
    ```

2.  Run the stack:
    ```bash
    docker-compose up -d
    ```

## Automated Deployment (GitHub Actions)

This repository includes a "Click-to-Deploy" workflow in `.github/workflows/deploy.yml`.

1.  **Configure Secrets**: Go to your GitHub Repository -> Settings -> Secrets and variables -> Actions -> New repository secret. Add these:
    -   `VPS_IP`: The IP address of your server.
    -   `VPS_USER`: The username (e.g., `root`).
    -   `SSH_KEY`: Your private SSH key (content of `id_rsa`).
    -   `BOT_TOKEN`: Your Telegram Bot Token.
    -   `API_ID`: Your App ID from my.telegram.org.
    -   `API_HASH`: Your App Hash from my.telegram.org.
    -   `DOCKER_USERNAME`: GitHub Username (for Container Registry).
    -   `DOCKER_TOKEN`: GitHub Personal Access Token (PAT) with `read:packages` and `write:packages` scope.

2.  **Deploy**: Just push to the `main` branch. GitHub will build the Docker image and auto-deploy it to your VPS.
