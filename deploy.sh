#!/bin/bash
set -e

echo "Starting deploy.sh"
echo "Updating system..."
sudo apt update -y || { echo "apt update failed"; exit 1; }
echo "Installing dependencies..."
sudo apt install -y python3 python3-pip python3-dev gcc ffmpeg || { echo "apt install failed"; exit 1; }

# Verify pip3 is available
if ! command -v pip3 >/dev/null 2>&1; then
    echo "pip3 not found, attempting to install manually..."
    sudo apt install -y python3-pip || { echo "Failed to install python3-pip"; exit 1; }
fi

echo "pip3 version: $(pip3 --version)"
echo "Installing Python packages..."
pip3 install -r requirements.txt || { echo "pip install failed"; exit 1; }
echo "Creating directories..."
mkdir -p user_cookies downloads || { echo "mkdir failed"; exit 1; }
echo "Starting bot..."
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot started with PID $!"
sleep 1  # Give it a moment to start
echo "Bot status: $(ps aux | grep 'python3 bot.py' | grep -v grep || echo 'Not running')"
echo "deploy.sh completed"