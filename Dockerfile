FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir python-telegram-bot==20.8 yt-dlp requests

COPY bot.py .

CMD ["python", "bot.py"]