import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")

# The comprehensive list of banned words
BANNED_WORDS = [
    "abbo", "abo", "abortion", "abuse", "addict", "adult", "amateur", "anal", "analsex", "angry", 
    "anus", "areola", "arse", "arsehole", "ass", "assassin", "assault", "assbagger", "assblaster", 
    "assclown", "asscowboy", "asses", "assfuck", "assfucker", "asshat", "asshole", "assholes", 
    "asshore", "assjockey", "asskiss", "asskisser", "assklown", "asslick", "asslicker", "asslover", 
    "assman", "assmonkey", "assmunch", "assmuncher", "asspacker", "asspirate", "asspuppies", 
    "assranger", "asswhore", "asswipe", "attack", "babe", "babies", "backdoor", "backdoorman", 
    "backseat", "badfuck", "balllicker", "balls", "ballsack", "banging", "barelylegal", "barf", 
    "barface", "barfface", "bast", "bastard", "bazongas", "bazooms", "beaner", "beast", "beastality", 
    "beastial", "beastiality", "beatoff", "beat-off", "beatyourmeat", "beaver", "bestial", "bestiality", 
    "bi", "biatch", "bicurious", "bigass", "bigbastard", "bigbutt", "bigger", "bisexual", "bitch", 
    "bitcher", "bitches", "bitchez", "bitchin", "bitching", "bitchslap", "bitchy", "biteme", "black", 
    "blackman", "blackout", "blacks", "blow", "blowjob", "boang", "bogan", "bohunk", "bollick", "bollock", 
    "bomb", "bombers", "bombing", "bombs", "bomd", "bondage", "boner", "bong", "boob", "boobies", "boobs", 
    "booby", "boody", "boom", "boong", "boonga", "boonie", "booty", "bootycall", "bountybar", "bra", 
    "brea5t", "breast", "breastjob", "breastlover", "breastman", "brothel", "bugger", "buggered", 
    "buggery", "bullcrap", "bulldike", "bulldyke", "bullshit", "bumblefuck", "bumfuck", "bunga", 
    "bunghole", "buried", "burn", "butchbabes", "butchdike", "butchdyke", "butt", "buttbang", "buttface", 
    "buttfuck", "buttfucker", "buttfuckers", "butthead", "buttman", "buttmunch", "buttmuncher", 
    "buttpirate", "buttplug", "buttstain", "byatch", "cacker", "cameljockey", "cameltoe", "canadian", 
    "cancer", "carpetmuncher", "carruth", "catholic", "catholics", "cemetery", "chav", "cherrypopper", 
    "chickslick", "children", "chin", "chinaman", "chinamen", "chinese", "chink", "chinky", "choad", 
    "chode", "christ", "christian", "church", "cigarette", "cigs", "clamdigger", "clamdiver", "clit", 
    "clitoris", "clogwog", "cocain", "cocaine", "cock", "cocksucker", "coonass", "cornhole", "cox", 
    "cracker", "crap", "cunt", "deepthro", "dick", "dumbass", "dyke", "ectasy", "erotic", "erotica", 
    "exhibitionist", "fag", "faggot", "feck", "fentanyl", "fistfuck", "fuck", "fucker", "fuckery", 
    "fuckface", "fuckher", "fuckjoe", "fuckup", "gay", "gaysex", "genitalia", "gore", "heroine", 
    "homoerotic", "hookup", "hot", "idiot", "intercourse", "jerk", "kike", "kinky", "ketamine", 
    "lickmy", "lingerie", "lsd", "marijuana", "masturbation", "meth", "methamphetamine", "molly", 
    "morphine", "motherfucker", "naked", "naughty", "nigga", "nigger", "nude", "obscene", "orgasm", 
    "paki", "penis", "piss", "poof", "poofter", "porn", "porno", "pornography", "prick", "prostitute", 
    "prostitution", "pussy", "racy", "ratfucking", "raunchy", "retard", "sexcam", "sexvideo", "sexy", 
    "shit", "shithouse", "shitposting", "shitter", "slut", "smut", "spicy", "steroids", "strip", 
    "stripping", "suckmy", "swinger", "topless", "twat", "vagina", "voyeur", "vulgar", "wank", 
    "webcam", "xanax", "xrated", "xxx", "zoophile", "zoophilia",
    # New words added
    "dengey", "dengue", "modda", "mda", "lavada", "lawada", "puku", "sulli", "puka", "eripuka", "erripuka", "erpk"
]

# The smart pattern for common variations
PATTERN = re.compile(r'\b(p[o0]rn|f[uU][cC][kK]|s[eE3][xX])\b', re.IGNORECASE)

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
    """Checks messages for banned words/patterns or bad links from non-admins and deletes them."""
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

    # Layer 1: Check with the smart PATTERN first
    if PATTERN.search(message.text):
        try:
            await message.delete()
            print(f"Deleted a message from '{user.username}' containing a regex pattern match.")
            return
        except Exception as e:
            print(f"Failed to delete message for regex pattern: {e}")
        return

    # Layer 2: Check the comprehensive BANNED_WORDS list
    message_text_lower = message.text.lower()
    for word in BANNED_WORDS:
        if word in message_text_lower:
            try:
                await message.delete()
                print(f"Deleted a message from '{user.username}' containing a banned word: '{word}'")
                return
            except Exception as e:
                print(f"Failed to delete message for banned word: {e}")
            return

    # Layer 3: If no banned words are found, check for bad links
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

