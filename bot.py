import os
from pyrogram import Client, filters
import yt_dlp

# Replace these with your actual credentials
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TELEGRAM_TOKEN)

# Handler for text messages
@app.on_message(filters.text)
async def handle_message(client, message):
    url = message.text.strip()
    
    # Check if the URL is from YouTube or Twitter
    if any(domain in url for domain in ["youtube.com", "youtu.be", "twitter.com", "x.com"]):
        # Send initial feedback
        status_msg = await message.reply("Processing your request...")

        try:
            # Step 1: Download the video with yt-dlp
            ydl_opts = {
                'outtmpl': 'downloads/%(id)s.%(ext)s',  # Save to downloads folder
                'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best',  # Prioritize H.264 and AAC
                'merge_output_format': 'mp4',           # Ensure output is mp4 for Telegram compatibility
                'quiet': False,                          # Suppress yt-dlp output
                # 'cookiefile': 'cookie.txt',            # Use cookies.txt for YouTube login
            }
            
            # Create downloads directory if it doesn't exist
            os.makedirs("downloads", exist_ok=True)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await status_msg.edit("Downloading video...")
                info = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info)
                # Ensure the file has the correct extension after merging
                file_name = file_name.rsplit('.', 1)[0] + '.mp4'

            # Step 2: Check file size
            file_size = os.path.getsize(file_name) / (1024 * 1024)  # Size in MB
            await status_msg.edit(f"Uploading video ({file_size:.2f} MB)...")

            # Step 3: Send the video
            if file_size <= 2000:  # Telegram's limit is 2GB (2000MB)
                await client.send_video(
                    chat_id=message.chat.id,
                    video=file_name,
                    supports_streaming=True,  # Enable streaming in Telegram
                )
            else:
                await status_msg.edit("Error: Video exceeds Telegram's 2GB limit.")

            # Step 4: Clean up
            os.remove(file_name)
            await status_msg.delete()

        except Exception as e:
            await status_msg.edit(f"Error: {str(e)}")
    else:
        await message.reply("Please send a valid YouTube or Twitter link.")

# Run the bot
print("Bot is running...")
app.run()