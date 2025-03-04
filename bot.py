import os
import asyncio
from pyrogram import Client, filters
import yt_dlp

# Load credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIE_FILE = os.getenv("COOKIE_FILE", "youtube_cookies.txt")  # Default cookie file path

# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handler for text messages (YouTube/Twitter URLs)
@app.on_message(filters.text)
async def handle_message(client, message):
    url = message.text.strip()
    
    if any(domain in url for domain in ["youtube.com", "youtu.be", "twitter.com", "x.com"]):
        status_msg = await message.reply("Processing your request...")
        try:
            ydl_opts = {
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best',
                'merge_output_format': 'mp4',
                'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
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
    else:
        await message.reply("Please send a valid YouTube or Twitter link, or upload a cookie file (youtube_cookies.txt).")

# Handler for document uploads (cookie file)
@app.on_message(filters.document)
async def handle_document(client, message):
    if message.document.file_name == "youtube_cookies.txt":
        status_msg = await message.reply("Processing your cookie file...")
        try:
            # Download the cookie file to the specified COOKIE_FILE path
            await message.download(file_name=COOKIE_FILE)
            await status_msg.edit(f"Cookie file saved as {COOKIE_FILE}. You can now send YouTube links!")
        except Exception as e:
            await status_msg.edit(f"Error saving cookie file: {str(e)}")
    else:
        await message.reply("Please upload a file named 'youtube_cookies.txt'.")

print("Bot is running...")
app.run()