# YouTube Downloader Telegram Bot

A reliable Telegram bot that downloads YouTube videos and sends them back to the user. Built with Python, `aiogram`, and `yt-dlp`. Dockerized for easy deployment on any VPS.

## Prerequisites

1.  **Telegram Bot Token**: Get one from [@BotFather](https://t.me/BotFather) on Telegram.
2.  **Docker** (Recommended) OR **Python 3.11+** installed.

## Quick Start (Docker) - Recommended

1.  Create a file named `.env` in this directory:
    ```env
    TELEGRAM_TOKEN=your_token_here
    ```

2.  Build the image:
    ```bash
    docker build -t ytbot .
    ```

3.  Run the container:
    ```bash
    docker run -d --env-file .env --name my-yt-bot ytbot
    ```

## Local Development (Python)

1.  Install system dependencies (`ffmpeg`):
    - **Mac**: `brew install ffmpeg`
    - **Linux**: `sudo apt install ffmpeg`
    - **Windows**: Download and add to PATH.

2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set your token in `.env` (or export as variable):
    ```bash
    export TELEGRAM_TOKEN=your_token_here
    ```

4.  Run the bot:
    ```bash
    python bot.py
    ```

## Features

-   Downloads YouTube videos using `yt-dlp` (highest reliability).
-   Tries to select video quality < 50MB (Telegram's bot API limit).
-   Sends video file directly to chat.

## Deploying to a VPS

Since this is Dockerized, you can deploy it to any provider:
-   **DigitalOcean / Linode / Hetzner**: Rent a small VPS ($5/mo), install Docker, and run the commands above.
-   **Railway / Fly.io**: Connect your GitHub repo and let them build the Dockerfile automatically.
