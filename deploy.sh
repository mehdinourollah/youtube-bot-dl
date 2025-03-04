#!/bin/bash
set -e

# Update system and install dependencies
sudo apt update -y
sudo apt install -y python3 python3-pip python3-dev gcc

# Install Python dependencies
pip3 install -r requirements.txt

# Run the bot in the background
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot deployed and running. Check bot.log for output."