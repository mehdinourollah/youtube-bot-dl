import os
import asyncio
from pyrogram import Client, filters
import yt_dlp

# Load credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_COOKIE_FILE = os.getenv("YOUTUBE_COOKIE_FILE", "youtube_cookies.txt")
INSTAGRAM_COOKIE_FILE = os.getenv("INSTAGRAM_COOKIE_FILE", "instagram_cookies.txt")

# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handler for text messages (YouTube, Twitter, Instagram URLs)
@app.on_message(filters.text)
async def handle_message(client, message):
    url = message.text.strip()
    
    # Check if the URL is from YouTube, Twitter, or Instagram
    if any(domain in url for domain in ["youtube.com", "youtu.be", "twitter.com", "x.com", "instagram.com"]):
        status_msg = await message.reply("Processing your request...")
        try:
            # Determine the appropriate cookie file based on the URL
            cookie_file = None
            if "youtube.com" in url or "youtu.be" in url:
                cookie_file = YOUTUBE_COOKIE_FILE if os.path.exists(YOUTUBE_COOKIE_FILE) else None
            elif "instagram.com" in url:
                cookie_file = INSTAGRAM_COOKIE_FILE if os.path.exists(INSTAGRAM_COOKIE_FILE) else None
                # Instagram-specific warning
                if not cookie_file:
                    await status_msg.edit("Note: Instagram may require cookies for some content. Upload 'instagram_cookies.txt' if needed.")

            ydl_opts = {
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best',
                'merge_output_format': 'mp4',
                'cookiefile': cookie_file,
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
        await message.reply("Please send a valid YouTube, Twitter, or Instagram link, or upload a cookie file (youtube_cookies.txt or instagram_cookies.txt).")

# Handler for document uploads (cookie files)
@app.on_message(filters.document)
async def handle_document(client, message):
    if message.document.file_name in ["youtube_cookies.txt", "instagram_cookies.txt"]:
        status_msg = await message.reply("Processing your cookie file...")
        try:
            # Save to the appropriate cookie file path
            target_file = YOUTUBE_COOKIE_FILE if message.document.file_name == "youtube_cookies.txt" else INSTAGRAM_COOKIE_FILE
            await message.download(file_name=target_file)
            await status_msg.edit(f"Cookie file saved as {target_file}. You can now send links!")
        except Exception as e:
            await status_msg.edit(f"Error saving cookie file: {str(e)}")
    else:
        await message.reply("Please upload a file named 'youtube_cookies.txt' or 'instagram_cookies.txt'.")

print("Bot is running...")
app.run()