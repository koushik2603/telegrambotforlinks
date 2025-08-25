import asyncio
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")

# --- Helper Functions for API Checks ---

# def extract_urls(text):
#     """Finds all URLs in a given string."""
#     # This regex finds http/https links
#     return re.findall(r'https?://[^\s]+', text)

# NEW, IMPROVED CODE
def extract_urls(text):
    """Finds all URLs in a given string, including those starting with www."""
    # This regex is improved to find http, https, and www links
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
        # Check if the 'obscene' score is high (e.g., > 0.5 is likely)
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

    # 1. Check if the user is an admin or creator
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        if chat_member.status in ['administrator', 'creator']:
            return # Ignore admins
    except Exception:
        return # Could not check status, better to ignore

    # 2. Extract all URLs from the message
    urls = extract_urls(message.text)
    if not urls:
        return # No URLs in message, nothing to do

    # 3. Check each URL against the APIs
    # NEW SIMPLIFIED SECTION
    for url in urls:
        # We only check for adult content now
        if check_sightengine_adult_content(url):
            try:
                await message.delete()
                print(f"Deleted message from '{user.username}' for containing an adult content link.")
                # Once one bad link is found, delete the message and stop
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