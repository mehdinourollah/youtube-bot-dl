import os
import asyncio
import json
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Load credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_COOKIES_DIR = os.getenv("USER_COOKIES_DIR", "user_cookies")

# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handler for /start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("🍪 Cookie Instructions", callback_data="cookie")]
    ])
    
    await message.reply(
        "👋 Welcome to the Universal Video Grabber Bot!\n\n"
        "Simply send me a video URL from YouTube, Twitter, Instagram, or TikTok, "
        "and I'll download and send it to you.",
        reply_markup=keyboard
    )

# Handler for /help command
@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply(
        "📖 **How to use this bot:**\n\n"
        "1️⃣ Send any video URL from supported platforms\n"
        "2️⃣ Wait for the bot to process and send your video\n\n"
        "🍪 **Using cookies for private content:**\n"
        "- Send /cookie for instructions on uploading cookies\n"
        "- Maximum video size: 2GB (Telegram limit)\n\n"
        "Supported platforms: YouTube, Twitter/X, Instagram, TikTok"
    )

# Handler for /cookie command
@app.on_message(filters.command("cookie"))
async def cookie_command(client, message):
    await message.reply(
        "🍪 **Cookie File Instructions:**\n\n"
        "To access private or age-restricted content, you can upload a cookie file:\n\n"
        "1. Export cookies from your browser as a .txt file\n"
        "2. Simply send the .txt file to this chat\n"
        "3. Your cookies will be stored securely for your account only\n\n"
        "Once uploaded, all your downloads will use your cookies automatically."
    )

# Add callback handler for button clicks
@app.on_callback_query()
async def handle_callback(client, callback_query):
    if callback_query.data == "help":
        await callback_query.message.edit_text(
            "📖 **How to use this bot:**\n\n"
            "1️⃣ Send any video URL from supported platforms\n"
            "2️⃣ Wait for the bot to process and send your video\n\n"
            "🍪 **Using cookies for private content:**\n"
            "- Send /cookie for instructions on uploading cookies\n"
            "- Maximum video size: 2GB (Telegram limit)\n\n"
            "Supported platforms: YouTube, Twitter/X, Instagram, TikTok",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="back")
            ]])
        )
    elif callback_query.data == "cookie":
        await callback_query.message.edit_text(
            "🍪 **Cookie File Instructions:**\n\n"
            "To access private or age-restricted content, you can upload a cookie file:\n\n"
            "1. Export cookies from your browser as a .txt file\n"
            "2. Simply send the .txt file to this chat\n"
            "3. Your cookies will be stored securely for your account only\n\n"
            "Once uploaded, all your downloads will use your cookies automatically.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="back")
            ]])
        )
    elif callback_query.data == "back":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Help", callback_data="help"),
             InlineKeyboardButton("🍪 Cookie Instructions", callback_data="cookie")]
        ])
        await callback_query.message.edit_text(
            "👋 Welcome to the Universal Video Grabber Bot!\n\n"
            "Simply send me a video URL from YouTube, Twitter, Instagram, or TikTok, "
            "and I'll download and send it to you.",
            reply_markup=keyboard
        )
    
    # Answer the callback query to remove the loading indicator
    await callback_query.answer()

# Handler for text messages (YouTube, Twitter, Instagram URLs)
@app.on_message(filters.text & ~filters.command(["start", "help", "cookie"]))
async def handle_message(client, message):
    url = message.text.strip()
    user_id = str(message.from_user.id)
    
    # URL validation regex pattern
    url_pattern = re.compile(
        r'https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)'
    )
    
    # Check if the message is a valid URL
    if not url_pattern.match(url):
        await message.reply(
            "❌ That doesn't look like a valid URL.\n\n"
            "Please send a video URL from YouTube, Twitter, Instagram, or TikTok.\n"
            "Type /help for more information."
        )
        return
    
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
            
            if not info:
                await status_msg.edit("❌ Failed to download video. This may require authentication or the video is unavailable.")
                return
                
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
        await status_msg.edit(f"Error: {str(e)}\n\nIf this is a YouTube video, you may need to upload cookies. Send /cookie for instructions.")


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