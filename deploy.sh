#!/bin/bash
set -e

# Install Python dependencies
pip3 install -r requirements.txt

# Create necessary directories
mkdir -p user_cookies
mkdir -p downloads

# Run the bot in the background
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot deployed and running. Check bot.log for output."