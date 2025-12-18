import asyncio
import logging
import os
import shutil
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import yt_dlp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API Token
API_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Check if token is present
if not API_TOKEN:
    logger.error("No TELEGRAM_TOKEN found in environment variables. Please set it in .env")
    exit(1)

# Initialize Bot and Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    This handler will be called when user sends `/start` command
    """
    await message.answer("👋 Hi! I'm a reliable YouTube Downloader Bot.\n\n"
                         "Send me a YouTube link, and I will try to download and send it to you.")

@dp.message(F.text)
async def handle_message(message: types.Message):
    """
    This handler will be called when user sends a text message (presumably a link)
    """
    url = message.text.strip()
    
    status_msg = await message.answer("🔍 Processing your link...")
    
    # Create a unique folder for this download to avoid collisions
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(DOWNLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    try:
        ydl_opts = {
            'format': 'best[ext=mp4][filesize<50M]/best[ext=mp4]/best', # Prioritize small enough files, otherwise just best
            'outtmpl': os.path.join(task_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        await bot.edit_message_text("⬇️ Downloading video...", chat_id=message.chat.id, message_id=status_msg.message_id)
        
        # Run yt-dlp in a separate thread to not block the bot
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, download_video, ydl_opts, url)
        
        # Find the downloaded file
        files = os.listdir(task_dir)
        if not files:
            await bot.edit_message_text("❌ Failed to download video: No file found.", chat_id=message.chat.id, message_id=status_msg.message_id)
            return
            
        video_path = os.path.join(task_dir, files[0])
        file_size = os.path.getsize(video_path)
        
        # Telegram Bot API Limit is 50MB
        if file_size > 50 * 1024 * 1024:
             await bot.edit_message_text(f"⚠️ Video is too large ({file_size / (1024*1024):.2f} MB). I can only send up to 50MB directly.", chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            await bot.edit_message_text("⬆️ Uploading to Telegram...", chat_id=message.chat.id, message_id=status_msg.message_id)
            video_file = FSInputFile(video_path)
            await message.reply_video(video_file, caption="Here is your video! 🎥")
            await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        logger.error(f"Error processing url {url}: {e}")
        await bot.edit_message_text(f"❌ Error occurred: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)
    finally:
        # Cleanup
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir)

def download_video(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

async def cleanup_downloads():
    """
    Cleans up the valid download directory on startup.
    """
    if os.path.exists(DOWNLOAD_DIR):
        logger.info(f"Cleaning up {DOWNLOAD_DIR}...")
        try:
            for item in os.listdir(DOWNLOAD_DIR):
                item_path = os.path.join(DOWNLOAD_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    await cleanup_downloads()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
