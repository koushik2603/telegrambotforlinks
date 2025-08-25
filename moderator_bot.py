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


# FINAL DEBUGGING VERSION
def check_sightengine_adult_content(url):
    """Checks a URL for adult or obscene content and handles API errors."""
    api_url = f"https://api.sightengine.com/1.0/check-url.json"
    params = {
        'url': url,
        'models': 'adult,obscene',
        'api_user': SIGHTENGINE_API_USER,
        'api_secret': SIGHTENGINE_API_SECRET
    }

    try:
        response = requests.get(api_url, params=params)
        data = response.json()

        # First, check if the API call itself failed (e.g., bad keys)
        if data.get('status') == 'failure':
            print(f"ERROR: Sightengine API call failed. Reason: {data.get('error', {}).get('message')}")
            return False

        # If the call succeeded, check the scores
        is_adult = data.get('adult', {}).get('prob', 0) > 0.5
        is_obscene = data.get('obscene', {}).get('prob', 0) > 0.5

        if is_adult or is_obscene:
            print(f"Adult/Obscene content link found by Sightengine: {url}")
            return True

    except Exception as e:
        print(f"ERROR: An exception occurred while checking Sightengine: {e}")

    return False

# --- Bot Logic ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks messages for adult links from non-admins and deletes them."""
    message = update.message
    if not message or not message.text:
        return

    user = message.from_user
    chat_id = message.chat_id
    print(f"DEBUG: Received message from user '{user.username}'.") # New print statement

    # 1. Check if the user is an admin or creator
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        if chat_member.status in ['administrator', 'creator']:
            print("DEBUG: User is an admin. Ignoring.") # New print statement
            return
    except Exception:
        print("DEBUG: Could not check admin status. Ignoring.") # New print statement
        return

    print("DEBUG: User is not an admin. Checking for URLs.") # New print statement
    urls = extract_urls(message.text)

    if not urls:
        print("DEBUG: No URLs found in message.") # New print statement
        return

    print(f"DEBUG: Found URL(s): {urls}") # New print statement

    # We only check for adult content now
    for url in urls:
        print(f"DEBUG: Checking URL with Sightengine: {url}") # New print statement
        is_adult = check_sightengine_adult_content(url)

        if is_adult:
            print("DEBUG: Sightengine reported link as ADULT. Attempting to delete.") # New print statement
            try:
                await message.delete()
                print(f"SUCCESS: Deleted message from '{user.username}'.")
                return
            except Exception as e:
                print(f"ERROR: Failed to delete message: {e}")
                return
        else:
            print("DEBUG: Sightengine reported link as SAFE.") # New print statement

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

