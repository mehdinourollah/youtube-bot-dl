import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import subprocess
import os
import requests

TOKEN = os.getenv('TELEGRAM_TOKEN')
SUPPORTED_PLATFORMS = ['twitter.com', 'x.com', 'youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com']

def start(update, context):
    update.message.reply_text('Send me a video URL from Twitter, YouTube, Instagram, TikTok, etc.!')

def handle_message(update, context):
    chat_id = update.message.chat_id
    text = update.message.text

    if not any(platform in text for platform in SUPPORTED_PLATFORMS):
        update.message.reply_text('Please send a valid video URL from a supported platform.')
        return

    update.message.reply_text('Downloading your video, please wait...')
    try:
        result = subprocess.run(['yt-dlp', '-g', '-f', 'bestvideo+bestaudio/best', text], 
                              capture_output=True, text=True, check=True)
        video_url = result.stdout.strip().split('\n')[0]
        if not video_url:
            raise ValueError('No video URL found')

        response = requests.head(video_url)
        size = int(response.headers.get('content-length', 0))
        if size > 50 * 1024 * 1024:
            update.message.reply_text('Video exceeds 50 MB. Use a smaller video or try another URL.')
        else:
            update.message.reply_video(video_url)
            update.message.reply_text('Here’s your video!')
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f'Error downloading video: {e.stderr.strip()}')
    except Exception as e:
        update.message.reply_text(f'Sorry, I couldn’t download the video: {str(e)}. Check the URL and try again.')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    print('Bot is running...')
    updater.idle()

if __name__ == '__main__':
    main()