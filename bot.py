import os
import asyncio
import json
from pathlib import Path
from pyrogram import Client, filters
import yt_dlp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_COOKIES_DIR = os.getenv("USER_COOKIES_DIR", "user_cookies")

# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handler for text messages (YouTube, Twitter, Instagram URLs)
@app.on_message(filters.text)
async def handle_message(client, message):
    url = message.text.strip()
    user_id = str(message.from_user.id)
    
    status_msg = await message.reply("Processing your request...")
    try:
        # Check for user-specific cookies
        cookie_file = None
        user_cookie_dir = Path(USER_COOKIES_DIR) / user_id
        
        if os.path.exists(user_cookie_dir):
            # Find any cookie file in the user's directory
            cookie_files = list(user_cookie_dir.glob("*.txt"))
            if cookie_files:
                cookie_file = str(cookie_files[0])  # Use the first cookie file found

        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best',
            'merge_output_format': 'mp4',
            'cookiefile': cookie_file if cookie_file else None,
            'quiet': False,
        }
        os.makedirs("downloads", exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_msg.edit("Downloading video...")
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            file_name = file_name.rsplit('.', 1)[0] + '.mp4'

        file_size = os.path.getsize(file_name) / (1024 * 1024)
        await status_msg.edit(f"Uploading video ({file_size:.2f} MB)...")

        if file_size <= 2000:
            await client.send_video(chat_id=message.chat.id, video=file_name, supports_streaming=True)
        else:
            await status_msg.edit("Error: Video exceeds Telegram's 2GB limit.")

        os.remove(file_name)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"Error: {str(e)}")


# Handler for document uploads (cookie files)
@app.on_message(filters.document)
async def handle_document(client, message):
    if message.document.file_name.endswith('.txt'):
        status_msg = await message.reply("Processing your cookie file...")
        try:
            # Create user-specific directory
            user_id = str(message.from_user.id)
            user_cookie_dir = Path(USER_COOKIES_DIR) / user_id
            os.makedirs(user_cookie_dir, exist_ok=True)
            
            # Save cookie file with original name
            target_file = user_cookie_dir / message.document.file_name
            await message.download(file_name=target_file)
            
            await status_msg.edit(f"Cookie file saved successfully. You can now send links!")
        except Exception as e:
            await status_msg.edit(f"Error saving cookie file: {str(e)}")
    else:
        await message.reply("Please upload a cookie file with .txt extension.")

print("Bot is running...")
app.run()