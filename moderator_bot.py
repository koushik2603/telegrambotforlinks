import asyncio
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")

def extract_urls(text):
    """Finds all URLs in a given string, including those starting with www."""

    return re.findall(r'(?:(?:https?://)|(?:www\.))\S+', text)


def check_sightengine_adult_content(url):
    """Checks a URL for adult content using the Sightengine API."""
    api_url = f"https://api.sightengine.com/1.0/check-url.json"
    params = {
        'url': url,
        'models': 'obscene',
        'api_user': SIGHTENGINE_API_USER,
        'api_secret': SIGHTENGINE_API_SECRET
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        
        if data.get('obscene', {}).get('prob', 0) > 0.5:
            print(f"Adult content link found by Sightengine: {url}")
            return True
    except Exception as e:
        print(f"Error checking Sightengine: {e}")
    return False

# --- Bot Logic ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks messages for malicious or adult links from non-admins."""
    message = update.message
    if not message or not message.text:
        return

    user = message.from_user
    chat_id = message.chat_id


    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        if chat_member.status in ['administrator', 'creator']:
            return 
    except Exception:
        return 


    urls = extract_urls(message.text)
    if not urls:
        return 

    for url in urls:
        
        if check_sightengine_adult_content(url):
            try:
                await message.delete()
                print(f"Deleted message from '{user.username}' for containing an adult content link.")
                
                return
            except Exception as e:
                print(f"Failed to delete message: {e}")
                return

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message."""
    await update.message.reply_text(
        "Hello! I am a moderation bot. I will automatically remove malicious or adult content links from non-admin users. "
        "Make sure I have 'Delete Messages' permission."
    )

def main():
    """Starts the bot."""
    print("Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()