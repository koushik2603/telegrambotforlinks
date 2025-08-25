import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")


ADULT_WORDS = [
    # Base words
    "porn", "porno", "pornography", "xxx", "adult", "erotic", "sex", "sexual", "nude",
    "p#rn",
    "p@rn",
    "p0rn",
    "s3x",
    "s.e.x",
    "erotica", "naked", "sexy", "hardcore", "softcore", "fetish", "bdsm", "kinky", "orgasm", 
    "intercourse", "explicit", "x-rated", "18+", "nsfw", "hentai", "strip", "stripping", 
    "webcam", "camgirl", "camboy", "onlyfans", "escort", "prostitute", "prostitution", 
    "brothel", "voyeur", "exhibitionist", "masturbation", "genitalia", "arousal", 
    "foreplay", "bondage", "dominatrix", "submissive", "adultfilm", "pornstar", "sextape", 
    "adultcontent", "nudevideo", "sexvideo", "sexcam", "smut", "raunchy", "steamy", 
    "naughty", "dirty", "freaky", "spicy", "racy", "lewd", "obscene", "vulgar"
]

# --- Sightengine API Function ---
def check_message_for_bad_links(message_text):
    """Sends the entire message text to Sightengine for link moderation."""
    api_url = "https://api.sightengine.com/1.0/text/check.json"
    params = {
        'text': message_text,
        'lang': 'en',
        'mode': 'rules',
        'api_user': SIGHTENGINE_API_USER,
        'api_secret': SIGHTENGINE_API_SECRET
    }
    try:
        response = requests.post(api_url, data=params)
        data = response.json()
        if data.get('status') == 'failure':
            print(f"ERROR: Sightengine API call failed. Reason: {data.get('error', {}).get('message')}")
            return False
        if data.get('link', {}).get('matches'):
            print(f"SUCCESS: Sightengine found a flagged link in the message.")
            return True
    except Exception as e:
        print(f"ERROR: An exception occurred while checking Sightengine: {e}")
    return False

# --- Bot Logic ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks messages for banned words or bad links from non-admins and deletes them."""
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

    # Convert the user's message to lowercase once
    message_text_lower = message.text.lower()

    # Check if any of the banned words are in the lowercase message
    for word in ADULT_WORDS:
        if word in message_text_lower:
            try:
                await message.delete()
                print(f"Deleted a message from '{user.username}' containing a banned word: '{word}'")
                return # Stop processing after deleting
            except Exception as e:
                print(f"Failed to delete message for banned word: {e}")
            return

    # If no banned words are found, then check for bad links
    if check_message_for_bad_links(message.text):
        try:
            await message.delete()
            print(f"Deleted a message from '{user.username}' containing a flagged link.")
        except Exception as e:
            print(f"Failed to delete message for flagged link: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message."""
    await update.message.reply_text(
        "Hello! I am a moderation bot. I delete messages with banned words or malicious links from non-admins."
    )

# --- Main Bot Runner ---
def main():
    """Starts the bot."""
    if not all([BOT_TOKEN, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET]):
        print("ERROR: One or more environment variables are missing.")
        return
        
    print("Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
