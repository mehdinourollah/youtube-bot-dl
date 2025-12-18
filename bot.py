```python
import asyncio
import logging
import os
import shutil
import uuid
import math
import subprocess
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from dotenv import load_dotenv
import yt_dlp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Configuration
API_TOKEN = os.getenv("BOT_TOKEN")
BOT_API_URL = os.getenv("BOT_API_URL", "https://api.telegram.org") # Default to public if not set, but Docker will set this

# Check if token is present
if not API_TOKEN:
    logger.error("No BOT_TOKEN found in environment variables. Please set it in .env")
    exit(1)

# Configure Bot with Local API Server if provided
session = None
if "api.telegram.org" not in BOT_API_URL:
    logger.info(f"Using Local Bot API Server at: {BOT_API_URL}")
    session = AiohttpSession(
        api=TelegramAPIServer.from_base(BOT_API_URL)
    )

bot = Bot(token=API_TOKEN, session=session)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
# Shared volume path inside the container. 
# PLEASE NOTE: For Local API to work efficiently (move files instead of upload), 
# the paths must align. We are just sending the file path.
# However, inside the bot container, we see /app/downloads.
# The Local API server sees the same absolute path if we mount it correctly. 
# But standard upload also works fine with Local API up to 2GB.

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    This handler will be called when user sends `/start` command
    """
    await message.answer("👋 Hi! I'm a robust YouTube Downloader Bot.\n"
                         "I can handle large videos (up to 4GB+) thanks to my Local API Server.\n\n"
                         "Send me a YouTube link to start!")

@dp.message(F.text)
async def handle_message(message: types.Message):
    """
    This handler will be called when user sends a text message (presumably a link)
    """
    url = message.text.strip()
    
    # Basic validation for youtube links
    if "youtube.com" not in url and "youtu.be" not in url:
        await message.answer("⚠️ That doesn't look like a valid YouTube link.")
        return

    status_msg = await message.answer("🔍 Processing your link...")
    
    # Create a unique folder for this download
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(DOWNLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    try:
        # Download best quality. We no longer limit to 50MB.
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'outtmpl': os.path.join(task_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        await bot.edit_message_text("⬇️ Downloading video (High Quality)...", chat_id=message.chat.id, message_id=status_msg.message_id)
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, download_video, ydl_opts, url)
        
        files = os.listdir(task_dir)
        if not files:
            await bot.edit_message_text("❌ Failed to download video: No file found.", chat_id=message.chat.id, message_id=status_msg.message_id)
            return
            
        video_path = os.path.join(task_dir, files[0])
        file_size = os.path.getsize(video_path)
        file_size_gb = file_size / (1024 * 1024 * 1024)
        
        if file_size_gb > 2.0:
            await bot.edit_message_text(f"⚠️ Video is {file_size_gb:.2f}GB. It exceeds the 2GB single-file limit.\n✂️ Splitting into parts...", chat_id=message.chat.id, message_id=status_msg.message_id)
            parts = await loop.run_in_executor(None, split_video, video_path, task_dir)
            
            for i, part in enumerate(parts):
                await bot.send_message(message.chat.id, f"⬆️ Uploading Part {i+1}/{len(parts)}...")
                video_file = FSInputFile(part)
                await message.reply_video(video_file, caption=f"Part {i+1}/{len(parts)}")
            
            await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
            
        else:
            await bot.edit_message_text(f"⬆️ Uploading ({file_size_gb:.2f} GB)...", chat_id=message.chat.id, message_id=status_msg.message_id)
            video_file = FSInputFile(video_path)
            await message.reply_video(video_file)
            await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        logger.error(f"Error processing url {url}: {e}")
        await bot.edit_message_text(f"❌ Error occurred: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)
    finally:
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir)

def download_video(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

def split_video(input_path, output_dir):
    """
    Splits a video file into chunks of 1.9GB to be safe under 2GB limit.
    """
    chunk_size = 1900 * 1024 * 1024 # 1.9GB in bytes
    parts = []
    
    file_name = os.path.basename(input_path)
    base_name, ext = os.path.splitext(file_name)
    
    # Use ffmpeg to split without re-encoding (very fast)
    # -c copy is crucial
    # -f segment -segment_time is unreliable for size, so we rely on fs (filesize) with 'split' cmd or complex mapping
    # Actually, simplistic 'split' command for binaries is riskier for playback.
    # Telegram requires valid container headers. Generic binary splitting breaks mp4 headers.
    
    # CORRECT APPROACH: We must use ffmpeg to ensure each part is a playable video file.
    # We will split by time. We need to calculate duration first.
    
    duration = get_video_duration(input_path)
    total_size = os.path.getsize(input_path)
    
    # Calculate how many parts we need
    num_parts = math.ceil(total_size / chunk_size)
    part_duration = duration / num_parts
    
    for i in range(num_parts):
        part_name = f"{base_name}_part{i+1}{ext}"
        out_path = os.path.join(output_dir, part_name)
        start_time = i * part_duration
        
        # ffmpeg -ss <start> -t <duration> -i in -c copy out
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(part_duration),
            '-i', input_path,
            '-c', 'copy',
            out_path
        ]
        subprocess.run(cmd, check=True)
        parts.append(out_path)
        
    return parts

def get_video_duration(path):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

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
