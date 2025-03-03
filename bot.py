import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import subprocess
import os
import requests

TOKEN = os.getenv('TELEGRAM_TOKEN')
SUPPORTED_PLATFORMS = ['twitter.com', 'x.com', 'youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com']

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Send me a video URL from Twitter, YouTube, Instagram, TikTok, etc.!')

async def handle_message(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text

    if not any(platform in text for platform in SUPPORTED_PLATFORMS):
        await context.bot.send_message(chat_id=chat_id, text='Please send a valid video URL from a supported platform.')
        return

    await context.bot.send_message(chat_id=chat_id, text='Downloading your video, please wait...')
    try:
        result = subprocess.run(['yt-dlp', '-g', '-f', 'bestvideo+bestaudio/best', text], 
                              capture_output=True, text=True, check=True)
        video_url = result.stdout.strip().split('\n')[0]
        if not video_url:
            raise ValueError('No video URL found')

        response = requests.head(video_url)
        size = int(response.headers.get('content-length', 0))
        if size > 50 * 1024 * 1024:
            await context.bot.send_message(chat_id=chat_id, text='Video exceeds 50 MB. Use a smaller video or try another URL.')
        else:
            await context.bot.send_video(chat_id=chat_id, video=video_url)
            await context.bot.send_message(chat_id=chat_id, text='Here’s your video!')
    except subprocess.CalledProcessError as e:
        await context.bot.send_message(chat_id=chat_id, text=f'Error downloading video: {e.stderr.strip()}')
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f'Sorry, I couldn’t download the video: {str(e)}. Check the URL and try again.')

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN not set")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print('Bot is running...')
    application.run_polling()

if __name__ == '__main__':
    main()