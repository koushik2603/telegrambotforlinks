import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
# These are loaded securely from your hosting environment (e.g., Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")

# --- Sightengine API Function ---
def check_message_for_bad_links(message_text):
    """Sends the entire message text to Sightengine for link moderation."""
    # This uses the correct Text Moderation API endpoint
    api_url = "https://api.sightengine.com/1.0/text/check.json"
    
    params = {
        'text': message_text,
        'lang': 'en',
        'mode': 'rules', # This mode is for checking links and profanity
        'api_user': SIGHTENGINE_API_USER,
        'api_secret': SIGHTENGINE_API_SECRET
    }
    
    try:
        response = requests.post(api_url, data=params)
        data = response.json()

        # Check for an API call failure (e.g., bad keys)
        if data.get('status') == 'failure':
            print(f"ERROR: Sightengine API call failed. Reason: {data.get('error', {}).get('message')}")
            return False

        # Check if the 'link' section has any matches
        if data.get('link', {}).get('matches'):
            print(f"SUCCESS: Sightengine found a flagged link in the message.")
            return True
            
    except Exception as e:
        print(f"ERROR: An exception occurred while checking Sightengine: {e}")
        
    return False

# --- Bot Logic ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks messages for bad links from non-admins and deletes them."""
    message = update.message
    if not message or not message.text:
        return

    user = message.from_user
    chat_id = message.chat_id
    
    # 1. Check if the user is an admin
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        if chat_member.status in ['administrator', 'creator']:
            return # Ignore admins
    except Exception:
        return

    # 2. Check the entire message for bad links using our new function
    if check_message_for_bad_links(message.text):
        try:
            await message.delete()
            print(f"Deleted a message from '{user.username}' containing a flagged link.")
        except Exception as e:
            print(f"Failed to delete message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hello! I am a moderation bot. I will automatically remove malicious or adult links from non-admin users. "
        "Make sure I have 'Delete Messages' permission to work correctly."
    )

# --- Main Bot Runner ---
def main():
    """Starts the bot."""
    if not all([BOT_TOKEN, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET]):
        print("ERROR: One or more environment variables are missing. Please check your hosting configuration.")
        return
        
    print("Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
